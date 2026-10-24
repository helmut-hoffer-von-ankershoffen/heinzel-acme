# AGENTS.md

Instructions for coding agents and humans working on heinzel-acme, Heinzelmännchen's reference company: four plugins
for [Heinzelmännchen](https://github.com/helmut-hoffer-von-ankershoffen/heinzel), one per layer of a made-up company.
Read [INTENT.md](INTENT.md) first.

## Ground rules

1. **Intent before code.** Changes serve [INTENT.md](INTENT.md) and respect the ADRs in [docs/adr/](docs/adr/).
2. **Follow [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md)** (shared with Heinzelmännchen, updated by
   `make update-template`). Plugins import only Heinzelmännchen's public API: `hz` and `heinzel.kernel`.
3. **Every change is tested** as `unit`, `integration` or `e2e`; the suite refuses anything else.
4. **Conventional commits**, always. Versions and the changelog are derived from them.
5. **Review before you finish** with the `review` skill and resolve every Critical and Required finding.
6. **Public and fictional.** Only made-up names: Acme (acme.example), org Payments, team Checkout, site Lisbon, the
   people in `src/heinzel_acme/_world.py`. Never a real company, team, product or person, in files, commit messages
   or pull request titles; `scripts/check_confidentiality.py` checks a private term list.
7. **Layers follow the core's ADR 0040.** A plugin per layer, named after its path, depending on its parent and site;
   declared only through `heinzel_acme.layers.declare` until the pinned core has `Module.layer`
   (`tests/unit/repository_test.py` keeps these rules).

## Commands

| Task | Command |
| --- | --- |
| Set up everything the build needs (deps, pinned tools in .tools/bin, git hooks) | `make setup` |
| What is missing, and the command that fixes it | `make doctor` |
| Edit loop, seconds | `make check-fast` |
| Everything CI checks offline | `make check` |
| Fix what tools can fix | `make fix` |
| Tests by level | `make test-unit`, `make test-integration`, `make test-e2e` |
| Try it with Heinzelmännchen | `uv run hz acme layers`, `uv run hz workflow playbooks` |
| Update to the latest Heinzelmännchen template | `make update-template` |

## Map

```
src/heinzel_acme/                 the company layer `acme`
  __init__.py                     module, its layer, the playbook recommending the bindings, info, layers, doctor
  layers.py                       THE bridge to the core's layer API (`declare`); every layer declares through it
  _bindings.py                    capability -> adapter, plugin, transport, login: what `hz setup acme` offers
  _world.py                       the made-up Acme world (people, items, pull requests, documents)
  seed/                           `hz acme seed`, rehearsal only: plan (pure), runner (vendor CLIs), service
plugins/heinzel-acme-payments/    the org layer: the okr asset type
plugins/heinzel-acme-lisbon/      the site layer: the site calendar as data
plugins/heinzel-acme-payments-checkout/  the team layer: the weekly report playbook and templates/weekly-report.prose.md
tests/                            unit/, integration/ (the CLI head, all four plugins), e2e/ (uv tool install)
plugins/*/tests/                  each layer's own tests
docs/                             REHEARSAL.md, PORT_TO_YOUR_COMPANY.md, CODING_STANDARDS.md (from the core), adr/
.claude/                          reviewer agents, skills and hooks (from Heinzelmännchen)
```

## How Heinzelmännchen sees this plugin

The entry point `[project.entry-points."heinzel.modules"]` names the root package. Heinzelmännchen walks it: every package that
declares `module = Module(name, summary)` is a module, nested ones are submodules, and their `@module.operation`
functions become commands (and later MCP tools and REST endpoints). Services are injected by type. See Heinzelmännchen's
[ARCHITECTURE.md](https://github.com/helmut-hoffer-von-ankershoffen/heinzel/blob/main/docs/ARCHITECTURE.md).

## Don'ts

- Don't import `heinzel.kernel._*`, `heinzel.modules.*` or `heinzel.heads.*` in `src/`; use the public API.
- Don't print; return models and let Heinzelmännchen's heads present them.
- Don't edit files that come from the template by hand if the change belongs in Heinzelmännchen — improve the template there.
