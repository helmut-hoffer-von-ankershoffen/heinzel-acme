# Development-tool security review

ACME's SonarCloud security findings include local development commands. Review their actual input boundaries
before changing the commands or resolving a finding. Plugin runtime code is not exposed through these scripts.

## Changes

The confidentiality check treats `--messages` as a Git revision operand, rejects options, and uses
`--end-of-options` before the revision. Git is resolved from PATH before execution. Integration tests exercise
option rejection and a real commit-range scan without revealing the configured term.

Direct tool invocations in PR and release helpers use the already-installed development environment (`make setup` first). Those commands
use `uv run --frozen --no-sync --no-build`; standard-library scripts no longer create separate script environments.
The publication checks use the same flags. Delegated preflight, fixes and Git hooks retain their own dependency
installation and build steps; release preparation also updates the lockfile. CI installation explicitly uses `--frozen --no-build`.

The SDK stays at version 0.7.2 but is installed from its official release wheel, whose SHA-256 is recorded in
`uv.lock`. Its GitHub attestation resolves to commit `42c6242ba7a111b10b24b536fdf7db483a861ebe`, the existing
SDK tag. All 221 matching source files in the wheel were compared with that tag and matched. Installed-acceptance
tests independently verify that same digest before passing a local wheel to `uv tool install`; a URL hash fragment
alone is not enforced by that command. A tampered-artifact regression test prevents installation before execution.
The source-only
`actionlint-py` wrapper is replaced by the same actionlint 1.7.12 binary, pinned with the vendor release checksums
for all supported platforms through the existing tool manifest.

The project defaults to `no-build = true`: ordinary third-party dependency installations need wheels. Reviewed
local workspace projects can still be built.

### Python 3.15 compatibility build

PyYAML 6.0.3 has no upstream Python 3.15 wheel. That matrix job skips only PyYAML during the frozen wheel-only
sync, then runs `scripts/bootstrap-pyyaml.sh`. This explicit exception builds the pure-Python wheel from the
same source archive and SHA-256 recorded in `uv.lock`. It verifies the archive before executing a backend,
uses a disposable environment with hash-pinned backend wheels, disables the optional native extension, and
installs the resulting local wheel without resolving dependencies. The job has no release credentials.
Tests reject altered archive contents before any backend command, and enforce agreement with the main lockfile.
This preserves the existing Python matrix without enabling general source-distribution builds.

Installed acceptance selects the same interpreter as its test process, avoiding accidental selection of an
unrelated system Python with different available dependency wheels.

## Findings requiring input-boundary review

| Location | Boundary and evidence |
| --- | --- |
| `scripts/tools.py:pin` | The CLI cannot supply a manifest path: it always writes `scripts/tools.toml`. The reported trace follows the manifest's **contents** into the data argument of `Path.write_text`, not into its destination path. Changing file contents cannot redirect this write. |
| `scripts/tools.py:run` | A local developer selects a named tool from the checked-in manifest and supplies that tool's arguments. The executable is installed with checksum verification or explicitly resolved from PATH. `os.execv` passes an argument vector without a shell. Argument forwarding is the command's documented purpose; this is not a web or plugin operation. |
| `scripts/changelog_intros.py:main` | A local developer or the release helper explicitly selects input/output changelog files. The release helper supplies its own temporary previous file and the fixed `CHANGELOG.md` output. There is no HTTP input, privilege boundary or plugin operation. |
| `scripts/release_notes.py:main` | The optional input filename is an intentional local file-reader interface. Publication supplies only a release tag and reads the fixed `CHANGELOG.md`; it does not supply an external filename. |
| `scripts/check_confidentiality.py:sources` | The commit-message filename is supplied by the local Git hook. Worktrees may place it outside the checkout, in the shared Git directory. The tool only scans it and reports term numbers, not contents. Arbitrary network callers cannot invoke it. |
| CI and Release `uv sync` | Ordinary installation uses `--frozen --no-build`, with a wheel-only SDK dependency and the project-level no-build policy. The narrowly isolated Python 3.15 PyYAML build is documented above. The previous SDK Git build is removed. |

Review any changes to these boundaries again. Do not add broad analyzer exclusions, disable security rules or use
`NOSONAR` to suppress unreviewed findings. A false-positive resolution needs a finding-specific explanation.
