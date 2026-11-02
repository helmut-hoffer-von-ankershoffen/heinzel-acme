"""A dispatched merge gate judges only main, or an open pull request at the branch's head with main's gate.

Runs scripts/merge_gate_dispatch.sh against a local origin and a stand-in `gh`. Offline.
"""

import os
import stat
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "merge_gate_dispatch.sh"
GATE = [".github/workflows/merge-gate.yml", "scripts/merge_gate.py", "scripts/merge_gate.py.lock"]


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, timeout=10
    ).stdout.strip()


@pytest.fixture
def clone(tmp_path: Path) -> Path:
    """A checkout of a branch off main, whose origin is a local bare repository."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "--quiet", "--bare", "--initial-branch=main", str(origin))
    work = tmp_path / "work"
    git(tmp_path, "clone", "--quiet", str(origin), str(work))
    for key, value in [
        ("user.name", "Example Author"),
        ("user.email", "author@example.test"),
        ("commit.gpgsign", "false"),
    ]:
        git(work, "config", key, value)
    for name in GATE:
        (work / name).parent.mkdir(parents=True, exist_ok=True)
        (work / name).write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
    (work / "scripts" / "merge_gate_dispatch.sh").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "--quiet", "-m", "main")
    git(work, "push", "--quiet", "origin", "main")
    git(work, "switch", "--quiet", "-c", "release/v9.9.9")
    (work / "CHANGELOG.md").write_text("v9.9.9\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "--quiet", "-m", "chore(release): v9.9.9")
    return work


def dispatch(work: Path, *, pr: str, ref: str, answer: str = "") -> subprocess.CompletedProcess[str]:
    """Run the check as the workflow does, with a `gh` that answers `state base head` for the pull request."""
    bin_dir = work.parent / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(f"#!/bin/sh\necho '{answer}'\n", encoding="utf-8")
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "PR": pr,
        "REF": ref,
        "SHA": git(work, "rev-parse", "HEAD"),
        "GITHUB_REPOSITORY": "owner/thing",
        "GH_TOKEN": "unused",
    }
    return subprocess.run(
        ["bash", str(SCRIPT)], cwd=work, env=env, capture_output=True, text=True, check=False, timeout=10
    )


def test_main_without_a_pull_request_judges_the_project(clone: Path):
    assert dispatch(clone, pr="", ref="refs/heads/main").returncode == 0


def test_a_branch_without_a_pull_request_fails_instead_of_skipping(clone: Path):
    result = dispatch(clone, pr="", ref="refs/heads/release/v9.9.9")
    assert result.returncode == 1
    assert "without a pull request" in result.stderr


def test_the_open_pull_request_at_this_head_with_mains_gate_passes(clone: Path):
    head = git(clone, "rev-parse", "HEAD")
    assert dispatch(clone, pr="30", ref="refs/heads/release/v9.9.9", answer=f"open main {head}").returncode == 0


@pytest.mark.parametrize(
    ("answer", "words"),
    [("closed main {head}", "is closed"), ("open other {head}", "not main"), ("open main " + "b" * 40, "head is")],
)
def test_a_pull_request_that_is_not_this_open_head_into_main_fails(clone: Path, answer: str, words: str):
    head = git(clone, "rev-parse", "HEAD")
    result = dispatch(clone, pr="30", ref="refs/heads/release/v9.9.9", answer=answer.format(head=head))
    assert result.returncode == 1
    assert words in result.stderr


def test_a_branch_that_changes_the_gate_fails(clone: Path):
    (clone / "scripts" / "merge_gate.py").write_text("print('pass')\n", encoding="utf-8")
    git(clone, "commit", "--quiet", "-am", "judge myself")
    head = git(clone, "rev-parse", "HEAD")
    result = dispatch(clone, pr="30", ref="refs/heads/release/v9.9.9", answer=f"open main {head}")
    assert result.returncode == 1
    assert "changes the merge gate" in result.stderr


def test_a_number_is_required_and_main_is_not_a_pull_requests_branch(clone: Path):
    assert dispatch(clone, pr="30; rm -rf /", ref="refs/heads/release/v9.9.9").returncode == 1
    assert dispatch(clone, pr="30", ref="refs/heads/main").returncode == 1
