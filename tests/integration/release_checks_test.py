"""release.yml starts every required check on the release pull request, after the held pull_request run. Offline."""

import os
import stat
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "release_checks.sh"

FAKE_GH = """#!/bin/sh
echo "$*" >> "$LOG"
case "$1 $2" in
  "pr view") echo "30 {head}" ;;
  "api repos/owner/thing/actions/workflows/ci.yml/runs?head_sha={head}&event=pull_request") echo "$HELD" ;;
esac
"""


def run(tmp_path: Path, held: str) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    head = "c" * 40
    gh = tmp_path / "gh"
    gh.write_text(FAKE_GH.replace("{head}", head), encoding="utf-8")
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls"
    env = {
        **os.environ,
        "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
        "GITHUB_REPOSITORY": "owner/thing",
        "LOG": str(log),
        "HELD": held,
        "WAIT": "0",
    }
    result = subprocess.run(
        ["bash", str(SCRIPT), "release/v9.9.9"], env=env, capture_output=True, text=True, check=False, timeout=10
    )
    return result, log.read_text(encoding="utf-8").splitlines()


def test_ci_and_both_gates_are_dispatched_after_the_held_run(tmp_path: Path):
    result, calls = run(tmp_path, held="1")
    assert result.returncode == 0, result.stderr
    held = next(i for i, c in enumerate(calls) if "event=pull_request" in c)
    ci = calls.index("workflow run ci.yml --repo owner/thing --ref release/v9.9.9")
    gate = calls.index("workflow run merge-gate.yml --repo owner/thing --ref release/v9.9.9 -f pr=30")
    assert held < ci < gate


def test_without_a_held_run_it_still_dispatches_and_says_so(tmp_path: Path):
    result, calls = run(tmp_path, held="0")
    assert result.returncode == 0, result.stderr
    assert "dispatching anyway" in result.stdout
    assert any(c.startswith("workflow run merge-gate.yml") for c in calls)


def test_the_release_workflow_runs_it_and_may_dispatch():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"]["pull-request"]
    assert job["permissions"]["actions"] == "write"
    assert any("scripts/release_checks.sh" in str(step.get("run", "")) for step in job["steps"])
