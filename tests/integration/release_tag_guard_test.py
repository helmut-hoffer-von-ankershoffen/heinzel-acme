"""Execute the publication guard against real local Git histories, without publishing or using a network."""

import os
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration
WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/publish.yml"


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=repository, capture_output=True, text=True, check=True, timeout=10
    ).stdout.strip()


def _guard(job: str) -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    steps = workflow["jobs"][job]["steps"]
    checkout = next(step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@"))
    assert checkout["with"]["ref"].startswith("refs/tags/")
    assert checkout["with"]["fetch-depth"] == 0
    guarded = next(step for step in steps if step.get("name") == "Verify the checked-out release tag")
    assert steps.index(guarded) < next(index for index, step in enumerate(steps) if "setup-uv@" in step.get("uses", ""))
    script = guarded["run"]
    assert isinstance(script, str)
    return script


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "--quiet", "--initial-branch=main")
    _git(tmp_path, "config", "user.name", "Example Author")
    _git(tmp_path, "config", "user.email", "author@example.test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    _git(tmp_path, "config", "tag.gpgsign", "false")
    _git(tmp_path, "commit", "--quiet", "--allow-empty", "-m", "Reviewed fixture")
    _git(tmp_path, "tag", "--annotate", "v1.0.0", "-m", "Reviewed release")
    _git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(tmp_path, "switch", "--quiet", "-c", "v1.0.0")
    _git(tmp_path, "commit", "--quiet", "--allow-empty", "-m", "Unreviewed branch fixture")
    return tmp_path


@pytest.mark.parametrize("job", ["publish"])
def test_guard_accepts_the_reviewed_annotated_tag_even_when_a_branch_has_the_same_name(
    repository: Path, job: str
) -> None:
    _git(repository, "checkout", "--quiet", "--detach", "refs/tags/v1.0.0")
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", _guard(job)],
        cwd=repository,
        env={**os.environ, "TAG": "v1.0.0"},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("job", ["publish"])
def test_guard_refuses_a_same_named_branch_instead_of_building_the_wrong_commit(repository: Path, job: str) -> None:
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", _guard(job)],
        cwd=repository,
        env={**os.environ, "TAG": "v1.0.0"},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode != 0


@pytest.mark.parametrize("job", ["publish"])
def test_guard_refuses_an_exact_tag_outside_reviewed_main(repository: Path, job: str) -> None:
    _git(repository, "tag", "v2.0.0")
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", _guard(job)],
        cwd=repository,
        env={**os.environ, "TAG": "v2.0.0"},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode != 0


@pytest.mark.parametrize("job", ["publish"])
def test_guard_refuses_missing_or_shell_like_tag_input_without_executing_it(repository: Path, job: str) -> None:
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", _guard(job)],
        cwd=repository,
        env={**os.environ, "TAG": "v9.9.9$(touch sentinel)"},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode != 0
    assert not (repository / "sentinel").exists()
