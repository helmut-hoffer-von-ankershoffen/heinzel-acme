---
status: accepted
date: 2026-11-01
amends: 0002
---

# 0003: The layer API is released; acme follows the core's compatible range

## Context and Problem Statement

[ADR 0002](0002-four-layers-in-one-workspace.md) was written while the core's layer and playbook APIs were unreleased.
It says the layer API is "being built", pins the core to a commit for tests and keeps the runtime dependency at
`heinzel>=0.2.0,<1`. Both APIs have since been released. What is true now?

## Decision Outcome

Chosen option: **follow the core's released range**. The decision in ADR 0002 stands; only its context statements change.

- The layer and playbook APIs are released. Every supported core has `Module.layer`.
- The runtime dependency of every plugin is the core's compatible range, currently `heinzel>=0.7.2,<1` in each
  `pyproject.toml`. The range moves when acme needs a newer core API, never otherwise.
- Tests use a released core from the lockfile, not a commit. There is no pin to track.
- `heinzel_acme.layers.declare` stays the one bridge. It forwards to `Module.layer`, and `hz acme layers` shows the same tree as
  `hz system layer list`.

### Consequences

- Good: a user installs a plugin with the standard app and gets its layers, with no core checkout.
- Good: ADR 0002's "Bad" consequences about an older core and a commit pin no longer apply.
- Bad: raising the range drops users on older cores, so a bump is a minor release.
