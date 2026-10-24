"""The seed's runner with a real process: git, which every machine that builds this has. Offline."""

import pytest
from heinzel import HeinzelError

from heinzel_acme.seed._runner import Subprocesses

pytestmark = pytest.mark.integration


def test_runs_a_cli_and_returns_its_output():
    assert "git version" in Subprocesses().run("git", ["--version"])


def test_a_failing_cli_is_an_error_with_its_exit_code():
    with pytest.raises(HeinzelError, match="exit code"):
        Subprocesses().run("git", ["no-such-subcommand"])
