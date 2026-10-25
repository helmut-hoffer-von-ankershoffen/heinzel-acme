"""Carries out a seed plan's steps: vendor CLIs as argument lists, never through a shell, each with a timeout.

The CLIs are logged in as the person (Heinzelmännchen ADR 0035); the runner reads no token and passes the CLIs only
the environment they need. Tests replace `Commands` with a fake: the seed never reaches a network in tests.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Protocol

from heinzel import HeinzelError, clean_text

TIMEOUT = 120
"""Seconds one command may take."""
STDERR_TAIL = 2000
"""Characters of a failing command's error output kept for its message."""
_PASS = ("PATH", "HOME", "LANG", "TMPDIR", "USER", "LOGNAME", "SSH_AUTH_SOCK", "TERM")
_PASS_PREFIXES = ("LC_", "XDG_", "GH_", "GITHUB_", "GIT_", "GOOGLE_WORKSPACE_CLI_")
_GIT_CONTEXT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    }
)
"""Inherited repository state and environment-injected config must never override the plan's Git directory."""
_GIT_CONFIG_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")


class Commands(Protocol):
    """Runs one command and returns what it printed."""

    def run(self, tool: str, args: list[str]) -> str:
        """Run `tool` with `args`; return its standard output.

        Raises:
            HeinzelError: If the tool is missing, fails or times out.
        """
        ...


def environment() -> dict[str, str]:
    """The variables a vendor CLI needs: where it lives, its configuration and the locale; nothing else."""
    return {
        key: value
        for key, value in os.environ.items()
        if (key in _PASS or key.startswith(_PASS_PREFIXES))
        and key not in _GIT_CONTEXT
        and not key.startswith(_GIT_CONFIG_PREFIXES)
    }


class Subprocesses:
    """Runs the vendor CLIs found on PATH."""

    def run(self, tool: str, args: list[str]) -> str:
        """Run `tool` with `args`; return its standard output.

        Raises:
            HeinzelError: If the tool is missing, fails or times out.
        """
        executable = shutil.which(tool)
        if executable is None:
            msg = f"{tool} is not installed or not on PATH; docs/REHEARSAL.md says how to install it."
            raise HeinzelError(msg)
        try:
            done = subprocess.run(  # noqa: S603 - an argument list, no shell
                [executable, *args],
                capture_output=True,
                text=True,
                check=False,
                timeout=TIMEOUT,
                env=environment(),
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            msg = f"{tool} {args[0] if args else ''} took longer than {TIMEOUT} s and was stopped."
            raise HeinzelError(msg) from exc
        if done.returncode != 0:
            tail = clean_text(done.stderr or done.stdout)[-STDERR_TAIL:].strip()
            msg = f"{tool} {' '.join(args[:3])} failed with exit code {done.returncode}: {tail}"
            raise HeinzelError(msg)
        return done.stdout


def write(path: Path, content: str) -> None:
    """Write `content` to `path`, creating its directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
