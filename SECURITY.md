# Security policy

<!-- badges:start -->
[![CI](https://img.shields.io/github/actions/workflow/status/helmut-hoffer-von-ankershoffen/heinzel-acme/ci.yml?branch=main&label=CI)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/helmut-hoffer-von-ankershoffen/heinzel-acme/python-coverage-comment-action-data/endpoint.json)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/tree/python-coverage-comment-action-data)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/helmut-hoffer-von-ankershoffen/heinzel-acme/codeql.yml?branch=main&label=CodeQL)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/badge)](https://scorecard.dev/viewer/?uri=github.com/helmut-hoffer-von-ankershoffen/heinzel-acme)
[![Release](https://img.shields.io/github/v/release/helmut-hoffer-von-ankershoffen/heinzel-acme?sort=semver)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/releases)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14%20%7C%203.15-blue)](pyproject.toml)
[![Types: mypy + pyright strict](https://img.shields.io/badge/types-mypy%20%2B%20pyright%20strict-blue)](docs/CODING_STANDARDS.md#python)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
<!-- badges:end -->

## Reporting a vulnerability

Report vulnerabilities privately, not through public issues.
[Open a private security advisory](../../security/advisories/new) for this repository: Security tab, then
**Report a vulnerability**. GitHub explains the steps in
[Privately reporting a security vulnerability](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately).

Include what is affected (version, command, plugin), how to reproduce it and what an attacker gains.

## Scope

This repository holds four plugins: `heinzel-acme`, `heinzel-acme-payments`, `heinzel-acme-lisbon` and
`heinzel-acme-payments-checkout`. They are a made-up reference company, and they run with your rights like any plugin.
A flaw in Heinzelmännchen itself belongs in the core's advisories.

## Policy

Response times, severity ratings, disclosure and supported versions are the core's:
[Heinzelmännchen's security policy](https://github.com/helmut-hoffer-von-ankershoffen/heinzel/blob/main/SECURITY.md).
