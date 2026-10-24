# heinzel-acme

<!-- badges:start -->
[![CI](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/ci.yml/badge.svg)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/ci.yml)
[![Coverage](https://raw.githubusercontent.com/helmut-hoffer-von-ankershoffen/heinzel-acme/python-coverage-comment-action-data/badge.svg)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/tree/python-coverage-comment-action-data)
[![CodeQL](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/codeql.yml/badge.svg)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/badge)](https://scorecard.dev/viewer/?uri=github.com/helmut-hoffer-von-ankershoffen/heinzel-acme)
[![Release](https://img.shields.io/github/v/release/helmut-hoffer-von-ankershoffen/heinzel-acme?sort=semver)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/releases)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14%20%7C%203.15-blue)](pyproject.toml)
[![Types: mypy + pyright strict](https://img.shields.io/badge/types-mypy%20%2B%20pyright%20strict-blue)](docs/CODING_STANDARDS.md#python)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
<!-- badges:end -->

Acme, a made-up company: the root layer of the reference company.

A plugin for [Heinzelmännchen](https://github.com/helmut-hoffer-von-ankershoffen/heinzel), the open-source, AI-driven operating system for
product development teams.


## Install

With Heinzelmännchen installed (`uv tool install git+https://github.com/helmut-hoffer-von-ankershoffen/heinzel`):

```bash
hz system plugin add git+https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme
```

Pin a version with `@vX.Y.Z`. Running `hz system plugin add` again upgrades; `hz system plugin remove heinzel-acme` removes it.

## Use

```bash
hz acme info                 # this plugin, its version and the Heinzelmännchen it runs on
hz acme hello --name Ada     # a submodule collapsed into a command
hz acme info --json          # every command speaks JSON, for scripts and agents
hz system info                  # includes a section contributed by this plugin
hz system theme use acme        # Acme's look for the web app
```

The `acme` theme ([`src/heinzel_acme/themes/acme.toml`](src/heinzel_acme/themes/acme.toml)) is deep teal on warm
off-white, slate at night, with Acme's logo in [`themes/logo/`](src/heinzel_acme/themes/logo/): a peak shaped like an
"A" standing on an anvil's base, hand-written SVG, teal `#0f766e` in light mode and `#2dd4bf` in dark mode.

## Develop

```bash
make setup     # everything the build needs, and the git hooks; you need only git, make and uv
make doctor    # what is missing, and the command that fixes it
make check     # lint, types, unit + integration tests
make test-e2e  # installs Heinzelmännchen with uv and adds this checkout as a plugin
```

The modules live in `src/heinzel_acme/`. Read [AGENTS.md](AGENTS.md) and
[docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) before changing them; the reviewer agents and hooks in
`.claude/` enforce them.

## Release

Actions → **Release** → Run workflow opens a release pull request; merging it tags and publishes. The version comes
from conventional commits, the changelog from git-cliff; the GitHub release carries the wheel, the sdist and
provenance attestations. `main` changes only through pull requests.

Add the topic `heinzel-plugin` to the GitHub repository so `hz system plugin search` lists the plugin.

## Stay current

This repository was generated from Heinzelmännchen's copier template (0.2.0). `make update-template` pulls in the
latest standards, tooling and CI from Heinzelmännchen.
