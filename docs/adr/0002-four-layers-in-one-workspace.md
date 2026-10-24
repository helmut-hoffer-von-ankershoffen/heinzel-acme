---
status: accepted
date: 2026-10-24
---

# 0002: Acme is four plugins in one workspace, declared through one bridge to the core's layer API

## Context and Problem Statement

The core decided (its ADR 0040) that a company's structure is plugins stacked as layers, that a company keeps its
plugins in one private repository laid out like the core's `plugins/`, and that a public reference company shows all
of it. The core's layer API (`Module.layer`) is being built while this repository is; its playbook API (ADR 0037) is
on the core's `main` but not yet released. How is the reference laid out, and how does it declare layers before the
core can take them?

## Considered Options

- **One uv workspace: the company layer at the root, org, site and team in `plugins/`, released together; layers
  declared through one bridge module** (chosen)
- **Four repositories**: closer to how independent teams might work, but not what ADR 0040 asks a company to copy,
  and four releases for one change to the stack.
- **One plugin with four modules**: no team could install its own stack, and nothing would test installing a team's
  plugin pulling in its parents.
- **Declare layers only once the core has the API**: the tree, the stack and its rules would wait, and so would the
  rehearsal.

## Decision Outcome

Chosen option: **one workspace, one bridge**.

- Each layer is a distribution `heinzel-<path>` with one module named after its path; a layer depends on its parent's
  and site's distributions, so `hz system plugin add` of the team installs the stack. All four share one version.
- Every layer declares itself with `heinzel_acme.layers.declare(module, parent=..., site=..., roles=...)`, the core's
  signature. It forwards to `Module.layer` when the installed core has it and records the declaration otherwise;
  `hz acme layers` shows the tree either way. Nothing else in the repository calls a layer API.
- The company layer's defaults are its playbook's recommended settings (the bindings), never applied without a yes.
- Discovery hints name Acme's own (made-up) document ids: the core's capabilities can confirm a known document but not
  search for one (its ADR 0037, "Bad"); assets without a confirming read (the tracker project, the repository) have no
  hint, and `hz acme seed` prints the `--asset` values for a rehearsal world.
- Heinzelmännchen is pinned to a commit on its `main` for tests until a release has the playbook API; the runtime
  dependency stays `heinzel>=0.2.0,<1` so the installed Heinzelmännchen is used.

### Consequences

- Good: the layout is the one a company copies; one pull request changes the whole stack; CI tests installing a team.
- Good: switching to the core's layer API is one file and a grep (`layers.declare`).
- Bad: until the core has `Module.layer`, the kernel doesn't stack Acme's layers: playbooks are listed per module, and
  org-and-site precedence (ADR 0040, open) can't be exercised here.
- Bad: a pin to a commit, not a release, until the core releases; README "Pins" tracks it.

### Confirmation

`tests/unit/repository_test.py` (names follow paths, dependencies on parent and site, one version, no layer API
outside the bridge); `tests/unit/layers_test.py` (stack order, labels, refused declarations, forwarding to the core's
API); `tests/e2e/install_test.py` (adding the team plugin installs its stack).
