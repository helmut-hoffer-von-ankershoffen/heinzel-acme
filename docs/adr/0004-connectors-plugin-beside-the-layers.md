---
status: proposed
date: 2026-11-14
amends: 0002, 0003
---

# 0004: ACME's own connectors are one plugin beside the layers, and acme tests on the core that has them

## Context and Problem Statement

A company that reaches its tools through its own gateway (a company MCP gateway, one local launcher per tool)
can't use the first-party connector plugins: it writes its own adapters, for every capability, in its private plugin
repository. ACME shows the layers of such a repository (ADR 0002) but not its connectors, so a company has no worked
example of implementing every Core connector capability, and the core's connector interfaces have no reference that
breaks when they change. Where do ACME's connectors go, and which core do the tests use?

## Considered Options

- **One connector plugin, `heinzel-acme-connectors`, in `plugins/` beside the layers** (chosen)
- **Adapters inside the company layer `heinzel-acme`**: every layer would install them, and the company layer would
  carry connector code and its tests; a company replaces connectors far more often than its layers.
- **A plugin in the public plugin collection**: it would read as a plugin to install, not as the part of a company's
  private repository it is.

## Decision Outcome

Chosen option: **one connector plugin beside the layers**.

- `plugins/heinzel-acme-connectors` (module `acme-connectors`) provides an adapter for every connector capability:
  calendar, mail, documents (a drive and a wiki), tracker, chat, meetings, code host and directory, and `ai-models`
  once the core has it. Its data is dummy and made up; its one seam to replace is `_backend.py`.
- It is no layer: it declares none, depends on no layer and is marked `[tool.acme] kind = "connector"`.
  `tests/unit/repository_test.py` applies the layer rules to layers only, and checks the connector plugin is named
  after its module, declares no layer and depends only on the core.
- It is released with the layers, at their version, like every plugin in the workspace (ADR 0002).
- Its runtime range is `heinzel>=0.9.41,<1`: the core that has tracker writes, attachments and the chat interface.
  The layers keep `heinzel>=0.7.2,<1` (ADR 0003: a range moves only when a plugin needs a newer API).
- Tests use core 0.9.42 from the lockfile for the whole workspace, so the layers are tested on a current core too.
- The company layer's bindings (`src/heinzel_acme/_bindings.py`) stay on the first-party plugins; a company that
  uses its own connectors binds them instead (the plugin's README says how).

### Consequences

- Good: a company sees all of its private repository in one place: layers and connectors, and the one file to change.
- Good: the core's connector interfaces have a reference implementation that its contract tests can run.
- Bad: the workspace tests no longer run on the layers' minimum core (0.7.2); a layer that needs an API between
  0.7.2 and 0.9.42 would not be caught. The layers use none today.

### Confirmation

`tests/unit/repository_test.py`; `plugins/heinzel-acme-connectors/tests/` (each adapter against its core protocol,
its behaviour on the dummy data, every capability bound through a kernel).
