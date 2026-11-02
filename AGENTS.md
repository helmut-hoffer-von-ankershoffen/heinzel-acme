# AGENTS.md

heinzel-acme is [Heinzelmännchen](https://github.com/helmut-hoffer-von-ankershoffen/heinzel)'s reference company: four
plugins, one per layer of a made-up company. Read [INTENT.md](INTENT.md) first.

## Commands

| Task | Command |
| --- | --- |
| Set up deps, pinned tools in `.tools/bin`, git hooks (`make doctor` names what is missing) | `make setup` |
| Edit loop, seconds | `make check-fast` |
| Everything CI checks offline | `make check` |
| Fix what tools can fix | `make fix` |
| Tests by level | `make test-unit`, `make test-integration`, `make test-e2e` |
| Try it | `uv run hz acme layers`, `uv run hz heinzel playbooks` |
| Update to the latest Heinzelmännchen template | `make update-template` |

## Rules

- Serve [INTENT.md](INTENT.md) and respect the ADRs in [docs/adr/](docs/adr/).
- Follow [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) (from the core; `make update-template` updates it).
- Import only the public API: `hz` and `heinzel.kernel`. Never import `heinzel.kernel._*`, `heinzel.modules.*` or
  `heinzel.heads.*` in `src/`.
- Return models; don't print. Heinzelmännchen's heads present them.
- Put a change to template-provided files in the Heinzelmännchen template, not here.
- Use conventional commits.
- Review with the `review` skill before finishing; resolve every Critical and Required finding.
- Public and fictional: only made-up names (ACME at acme.example, org Payments, team Checkout, site Lisbon, the people
  in `src/heinzel_acme/_world.py`). Never a real company, team, product or person in files, commits or PR titles;
  `scripts/check_confidentiality.py` checks a private term list.
- Layers follow core ADR 0040: one plugin per layer, named after its path, depending on its parent and site, declared
  only through `heinzel_acme.layers.declare` (`tests/unit/repository_test.py` keeps these rules).

## Map

```
src/heinzel_acme/                 the company layer `acme`: module, layer, playbook recommending the bindings, doctor
  layers.py                       the bridge to the core's layer API (`declare`)
  _bindings.py                    capability -> adapter, plugin, transport, login: what `hz setup acme` offers
  themes/, soundscapes/           ACME's theme, logo and opt-in soundscape
  _world.py                       the made-up world (people, items, pull requests, documents)
  seed/                           `hz acme seed`, rehearsal only
plugins/heinzel-acme-payments/    org layer: the okr asset type
plugins/heinzel-acme-lisbon/      site layer: the site calendar as data
plugins/heinzel-acme-payments-checkout/  team layer: weekly report playbook and templates/weekly-report.prose.md
tests/, plugins/*/tests/          unit/, integration/ (CLI head, all four plugins), e2e/ (uv tool install)
docs/                             REHEARSAL.md, PORT_TO_YOUR_COMPANY.md, adr/
```

Module discovery and `@module.operation`: [ARCHITECTURE.md](https://github.com/helmut-hoffer-von-ankershoffen/heinzel/blob/main/docs/ARCHITECTURE.md).
