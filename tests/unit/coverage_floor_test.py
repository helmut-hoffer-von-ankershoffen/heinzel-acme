"""The coverage floor is a job of the pull request's own CI run, and its verdict says why it failed."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("coverage_floor", ROOT / "scripts" / "coverage_floor.py")
assert spec
assert spec.loader
floor = importlib.util.module_from_spec(spec)
sys.modules["coverage_floor"] = floor
spec.loader.exec_module(floor)

pytestmark = pytest.mark.unit

WORKFLOW = "  coverage:\n    steps:\n      - with:\n          MINIMUM_ORANGE: 80\n"
PYPROJECT = "[tool.coverage.report]\nfail_under = 90\n"
LISTING = (
    "src/heinzel_acme/a.py      120     30     40      5    71%   3-9, 14\n"
    "src/heinzel_acme/b.py       10      2      0      0    80%   7-8\n"
)


def _run(tmp_path: Path, total: str | None, result: str = "success") -> tuple[int, str, str]:
    (tmp_path / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (tmp_path / floor.WORKFLOW).write_text(WORKFLOW, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    env = {
        "COVERAGE_RESULT": result,
        "GITHUB_SHA": "a" * 40,
        "GITHUB_OUTPUT": str(tmp_path / "output"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        "UNCOVERED": LISTING,
        "COVERAGE_TOTAL": str(tmp_path / "coverage-total.txt"),
    }
    if total is not None:
        (tmp_path / "coverage-total.txt").write_text(total, encoding="utf-8")
    code = floor.main(env, tmp_path)
    return code, (tmp_path / "output").read_text(encoding="utf-8"), (tmp_path / "summary").read_text(encoding="utf-8")


def test_a_total_above_both_thresholds_passes_and_names_measured_required_and_scope(tmp_path):
    code, output, summary = _run(tmp_path, "93.20\n")
    assert code == 0
    assert output == (
        "verdict=Coverage floor passed: whole-project coverage 93.2% "
        "(required 80% floor and 90% report threshold (fail_under))\n"
    )
    assert "Whole-project coverage: measured 93.2%, required 80% floor and 90% report threshold" in summary
    assert "the whole project" in summary
    assert "aaaaaaaaaaaa" in summary
    assert "src/heinzel_acme/a.py" in summary
    assert "3-9, 14" in summary


@pytest.mark.parametrize(
    "case",
    [
        ("79.99", "failure", "whole-project coverage 79.99% is below the 80% floor"),
        ("88.5", "failure", "whole-project coverage 88.5% is below the 90% report threshold (fail_under)"),
        ("95", "failure", "the Coverage job ended with failure after measuring 95%"),
        (None, "failure", "the Coverage job ended with failure before it measured a total"),
        ("", "failure", "the Coverage job ended with failure before it measured a total"),
    ],
)
def test_a_shortfall_fails_as_not_met_with_its_reason(tmp_path, capsys, case):
    total, result, reason = case
    code, output, summary = _run(tmp_path, total, result)
    assert code == 1
    assert output.startswith(f"verdict=Coverage floor FAILED (not met): {reason}")
    assert f"::error title=Coverage floor::Coverage floor FAILED (not met): {reason}" in capsys.readouterr().out
    assert summary.startswith("### Coverage floor FAILED")


@pytest.mark.parametrize(
    "case",
    [
        (None, "the Coverage job passed but left no coverage-total artifact"),
        ("", "the Coverage job passed but left no coverage-total artifact"),
        ("eighty", "not a percentage"),
        ("101", "not a percentage"),
    ],
)
def test_a_judge_that_cannot_read_its_inputs_says_tool_error(tmp_path, case):
    total, reason = case
    code, output, _ = _run(tmp_path, total)
    assert code == 2
    assert output.startswith("verdict=Coverage floor TOOL ERROR (the judge broke, coverage was not judged): ")
    assert reason in output


def test_the_floor_is_read_from_the_real_workflow():
    workflow = (ROOT / floor.WORKFLOW).read_text(encoding="utf-8")
    assert floor.red_below(workflow) == 80
    assert floor.fail_under((ROOT / "pyproject.toml").read_text(encoding="utf-8")) == 90
    assert floor.fail_under("") is None


def test_the_script_runs_isolated_with_the_standard_library_only(tmp_path):
    (tmp_path / "total").write_text("85", encoding="utf-8")
    env = {"COVERAGE_RESULT": "success", "COVERAGE_TOTAL": str(tmp_path / "total"), "PATH": "/usr/bin:/bin"}
    done = subprocess.run(
        [sys.executable, "-I", "scripts/coverage_floor.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert done.returncode == 1
    assert "FAILED (not met): whole-project coverage 85% is below the 90% report threshold" in done.stdout


def test_the_floor_is_a_ci_job_that_ci_ok_requires_and_no_merge_gate_workflow_is_left():
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))["jobs"]
    job = jobs["coverage-floor"]
    assert job["name"] == "Coverage floor"
    assert job["needs"] == ["coverage"]
    assert job["permissions"] == {"contents": "read"}
    assert [step["run"] for step in job["steps"] if "run" in step] == ["python3 -I scripts/coverage_floor.py"]
    assert "coverage-floor" in jobs["ci-ok"]["needs"]
    assert '[ "$FLOOR" != success ]' in jobs["ci-ok"]["steps"][0]["run"]
    assert ".value.outputs.verdict" in jobs["ci-ok"]["steps"][0]["run"]
    assert not (ROOT / ".github/workflows/merge-gate.yml").exists()
    assert not (ROOT / "scripts/merge_gate.py").exists()
    assert jobs["coverage"]["outputs"]["uncovered"] == "${{ steps.uncovered.outputs.files }}"
