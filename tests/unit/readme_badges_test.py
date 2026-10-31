"""Status badges stay together at the top of the repository README."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def test_readme_status_badges_share_one_row():
    text = (ROOT / "README.md").read_text()
    match = re.search(r"<!-- badges:start -->\n([^\n]+)\n<!-- badges:end -->", text)
    assert match
    badges = match.group(1)
    for label in (
        "CI",
        "Coverage",
        "CodeQL",
        "Python",
        "Quality Gate Status",
        "Security Rating",
        "License: MIT",
    ):
        assert f"[![{label}](" in badges
        assert f"[![{label}](" not in text[: match.start()] + text[match.end() :]


def test_unpublished_package_has_no_pypi_badge():
    assert "[![PyPI]" not in (ROOT / "README.md").read_text()
