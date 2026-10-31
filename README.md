# heinzel-acme

<!-- badges:start -->
[![CI](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/ci.yml/badge.svg)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/ci.yml) [![Coverage](https://raw.githubusercontent.com/helmut-hoffer-von-ankershoffen/heinzel-acme/python-coverage-comment-action-data/badge.svg)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/tree/python-coverage-comment-action-data) [![CodeQL](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/codeql.yml/badge.svg)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/actions/workflows/codeql.yml) [![Release](https://img.shields.io/github/v/release/helmut-hoffer-von-ankershoffen/heinzel-acme?sort=semver)](https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/releases) [![PyPI](https://img.shields.io/badge/PyPI-not%20published-lightgrey)](#install-and-look) [![Python](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=helmut-hoffer-von-ankershoffen_heinzel-acme&metric=alert_status)](https://sonarcloud.io/summary/overall?id=helmut-hoffer-von-ankershoffen_heinzel-acme) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=helmut-hoffer-von-ankershoffen_heinzel-acme&metric=security_rating)](https://sonarcloud.io/summary/overall?id=helmut-hoffer-von-ankershoffen_heinzel-acme) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
<!-- badges:end -->

**A fictional company you can explore, install and adapt for your own team.**

[**Explore Acme on the plugin page →**](https://helmut.hoffer-von-ankershoffen.me/heinzel/catalog/heinzel-acme-aa9ce1cf07/)
· [Install the team stack](#install-and-look) · [Port it to your company](#port-it-to-your-company)

<a href="https://helmut.hoffer-von-ankershoffen.me/heinzel/catalog/heinzel-acme-aa9ce1cf07/">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/ui-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/assets/ui.png">
  <img src="docs/assets/ui.png" alt="The installed ACME theme in Heinzelmännchen, using an isolated demonstration profile" width="1120">
</picture>
</a>

*The running ACME theme, captured with Heinzelmännchen 0.9.8 and fictional profile data. Accounts are unconnected;
the Doctor card shows the remaining setup. [View the full gallery and soundscape →](https://helmut.hoffer-von-ankershoffen.me/heinzel/catalog/heinzel-acme-aa9ce1cf07/)*

Acme is the reference company for [Heinzelmännchen](https://github.com/helmut-hoffer-von-ankershoffen/heinzel):
four plugins modelling a company, an organization, a site and a team. Installing the Checkout team brings its
company, Payments organization and Lisbon site with it.

- **Explore a complete team stack:** layers, recommended integrations, roles and calendars.
- **Try a weekly-report playbook:** templates and contracts that a team can adapt.
- **Make it yours:** use the [porting runbook](docs/PORT_TO_YOUR_COMPANY.md) as a worked example for a private company repository.

Everything here is fiction: Acme (acme.example), its people, its teams and its documents. It follows the core's
[layer model](https://github.com/helmut-hoffer-von-ankershoffen/heinzel/blob/main/docs/adr/0040-layers-and-playbooks-are-plugins.md)
and [plugin playbooks](https://github.com/helmut-hoffer-von-ankershoffen/heinzel/blob/main/docs/adr/0037-plugins-bring-playbooks.md).

## The layers

<details>
<summary>See the CLI screenshot</summary>

[![The Acme company, site, organization and team layers shown by the hz acme layers command](docs/assets/cli.png)](https://helmut.hoffer-von-ankershoffen.me/heinzel/catalog/heinzel-acme-aa9ce1cf07/)

*Real `hz acme layers` output from the same isolated demonstration profile.*


</details>

<details>
<summary>Layer dependency diagram</summary>

```mermaid
flowchart TB
    acme["<b>acme</b> · company<br/>capability bindings (gh, acli, gws, Gmail, Zoom summaries)<br/>roles tech-lead, report-owner<br/>hz acme seed (rehearsal only)"]
    payments["<b>acme-payments</b> · org<br/>playbook: the okr asset type"]
    lisbon["<b>acme-lisbon</b> · site<br/>the site calendar: time zone, working hours, meeting rhythm"]
    checkout["<b>acme-payments-checkout</b> · team<br/>playbook: the weekly report<br/>(asset types, hints, template contract)"]
    acme --> payments
    acme --> lisbon
    payments --> checkout
    lisbon -. site .-> checkout
```

</details>

Each box is a plugin, named after its path from the root (`heinzel-<name>`). A layer declares its parent and, for a
team, its site; Heinzelmännchen stacks a person's layers **general to specific**: for Checkout that is `acme`, then
`acme-payments` and `acme-lisbon`, then `acme-payments-checkout`. A more specific layer refines a more general one,
and nothing any layer brings becomes your configuration until you accept it (`hz setup`).

| Plugin | Layer | What it brings |
| --- | --- | --- |
| [`heinzel-acme`](src/heinzel_acme/) | company | Bindings for code host (GitHub, `gh`), tracker (Jira, `acli`), documents, calendar and mail (Google Workspace, `gws`) and meetings (Zoom's summary e-mails), offered by `hz setup acme`; roles; a doctor check per binding; `hz acme layers`; `hz acme seed` |
| [`heinzel-acme-payments`](plugins/heinzel-acme-payments/) | org | A playbook with the `okr` asset type: the org's quarterly OKR document |
| [`heinzel-acme-lisbon`](plugins/heinzel-acme-lisbon/) | site | The site calendar as data (`hz acme-lisbon calendar`): Europe/Lisbon, 09:00 to 18:00, stand-up, planning, demo, the Friday 17:00 report deadline |
| [`heinzel-acme-payments-checkout`](plugins/heinzel-acme-payments-checkout/) | team | The weekly report playbook: asset types (weekly report document, engineering tracker, tracker project, code repository) with discovery hints, and the template contract `acme-payments-checkout:weekly-report`, a draft ready by Friday 17:00 |

## Install and look

For macOS and Linux, start with the [standard app installation guide](https://helmut.hoffer-von-ankershoffen.me/heinzel/guides/install/).
Use `uvx heinzel@latest` if uv is available, or its guided curl/wget installer to install prerequisites automatically.
Windows may work, but is not supported.

Once Heinzelmännchen is installed:

```bash
hz system plugin add "git+https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme#subdirectory=plugins/heinzel-acme-payments-checkout" --confirm
```

One plugin, the team's: its org, site and company come with it, as its dependencies. Then:

```bash
hz system layer list        # the tree, from the core (a core with the layer API)
hz system layer show        # your stack: acme → acme-payments + acme-lisbon → acme-payments-checkout
hz acme layers              # the same tree as Acme declares it, on any core
hz acme info                # the bindings Acme recommends and how they stand on this machine
hz system doctor            # which adapter plugins and logins are missing
hz heinzel playbooks       # what each layer's playbook offers
hz setup acme               # accept the bindings you want, one by one
hz acme-lisbon calendar     # the site's week, at the site and on this machine
```

The first-party adapter plugins the bindings name are separate: use `hz system plugin add github --confirm` (or
`atlassian`, `zoom`, `google` in place of `github`), each with its vendor CLI logged in as you; `hz system doctor` lists what is missing with the command
that fixes it.

## The weekly report

```bash
hz heinzel new weekly-report --template acme-payments-checkout:weekly-report \
  --asset weekly-report=<doc id> --asset engineering-tracker=<sheet id> \
  --asset tracker-project=CHK --asset code-repo=<owner>/acme-checkout
hz heinzel run weekly-report --dry-run     # the inputs, fetched through gh, acli and gws; no agent, no cost
hz heinzel run weekly-report               # the draft, saved locally for you to edit and send
```

To try it against a real (trial) world, [docs/REHEARSAL.md](docs/REHEARSAL.md) walks a manager and an engineer through
it on two machines, with `hz acme seed` creating the Acme world in your own trial accounts.

## Port it to your company

[docs/PORT_TO_YOUR_COMPANY.md](docs/PORT_TO_YOUR_COMPANY.md) is the runbook a coding agent (or you) follows to create a
private `heinzel-<company>` repository with the same shape: what to rename, how to bind your company's own providers
through a private layer, and what to verify first. This repository plus that runbook is the hand-off.

## Compatibility

Each plugin declares its supported SDK range in its project metadata. The development lock records the SDK used by
tests; users install the standard app without selecting an SDK version. No unreleased Core checkout is required.

## Theme

```sh
hz system theme use acme
```

The `acme` theme ([`src/heinzel_acme/themes/acme.toml`](src/heinzel_acme/themes/acme.toml)) is deep teal on warm
off-white, slate at night, with Acme's logo in [`themes/logo/`](src/heinzel_acme/themes/logo/): a peak shaped like an
"A" standing on an anvil's base, hand-written SVG, teal `#0f766e` in light mode and `#2dd4bf` in dark mode.

## Sound

The plugin offers the [requested YouTube video](https://www.youtube.com/watch?v=t9PF00M2yDY) as the `acme`
soundscape. It pairs only with the Acme theme. It uses the core's privacy-enhanced player, with no downloaded or
bundled media; installation leaves sound off, and the person still presses **Play** in the web player.

```sh
hz system sound list
hz system theme use acme
hz system config set system.sound.follow_theme true
hz system sound list       # effective: acme
```

For a direct choice, or to turn sound off:

```sh
hz system config set system.sound.follow_theme false
hz system sound use acme
hz system sound use off
```

Plugin releases are independent of Core. An explicitly selected plugin tag or commit stays pinned when hz updates.

## Develop

```bash
make setup     # dependencies, pinned tools, git hooks
make check     # lint, types, unit and integration tests of all four plugins (offline)
make test-e2e  # installs Heinzelmännchen with uv and adds the team plugin from this checkout
```

See the [development-tool security review](docs/SECURITY_REVIEW.md) for dependency-build and CLI input boundaries.
Run `make setup` before the PR or release helpers. Their direct tool invocations reuse the installed environment;
delegated checks, fixes and Git hooks retain their own dependency installation and build steps.

Read [AGENTS.md](AGENTS.md) first. The plugins are one uv workspace: the company layer at the root, the others in
`plugins/`, released together at one version. Tests use fakes and never reach a network; `hz acme seed` refuses to
run the real CLIs inside a test session.

## Release

Actions → **Release** → Run workflow opens a release pull request; merging it tags and publishes all four plugins. The
version comes from conventional commits, the changelog from git-cliff. `main` changes only through pull requests.

This repository was generated from Heinzelmännchen's copier template; `make update-template` pulls in its latest
standards, tooling and CI.
