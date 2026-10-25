# Port Acme to your company

A runbook for one session, a coding agent's or yours, with nothing but this repository and access to your company's
GitHub: it creates a **private** repository `heinzel-<company>` with the same shape as this one (a company layer, an
org, a site and a team, each a plugin) and the weekly report playbook, bound to your company's tools. Follow it top
to bottom; every step ends with a check.

Two rules hold throughout:

- **The new repository is private, and nothing flows back.** Your company's names, people, document ids and
  providers go into `heinzel-<company>` only, never into this repository, the core or any public issue or pull
  request. Ask before pushing anywhere public.
- **Only what an ordinary employee may do** (core ADR 0035). Vendor CLIs logged in as the person; no app an
  administrator must register. Where the company reaches a tool differently, that is a provider in your company
  layer, not a change to the core.

## 0. Ask for the inputs

Ask the person for these, and write the answers into the new repository's `INTENT.md` as you go:

| Input | Example (Acme) | Becomes |
| --- | --- | --- |
| Company slug | `acme` | the company layer `heinzel-<company>`, package `heinzel_<company>` |
| Org slug | `payments` | `heinzel-<company>-<org>` |
| Team slug | `checkout` | `heinzel-<company>-<org>-<team>` |
| Site slug | `lisbon` | `heinzel-<company>-<site>` |
| GitHub owner of the private repository | `acme-example` | `gh repo create <owner>/heinzel-<company> --private` |
| Per capability, the tool and how an employee reaches it | code host GitHub via `gh`, tracker Jira via `acli`, documents Google via `gws`, mail Gmail, meetings Zoom summaries | `_bindings.py` |
| The weekly report: where it lives, its sections, its deadline | a Google Doc, newest week first; Highlights, Progress on goals, Risks, Next week; Friday 17:00 | the team's template contract |
| The site's time zone, working hours and rhythm | Europe/Lisbon, 09:00 to 18:00, stand-up 09:30 | the site calendar |

A company with more levels (a division between company and org) adds a layer per level; the names keep following the
path (`<company>-<division>-<org>`).

## 1. Create the repository from this one

```bash
gh repo clone helmut-hoffer-von-ankershoffen/heinzel-acme       # this repository, read only
gh repo create <owner>/heinzel-<company> --private --clone
cd heinzel-<company>
git -C ../heinzel-acme archive HEAD | tar -x      # this repository's files, without its history
```

Rename, longest names first so no shorter one is replaced inside a longer one:

| Replace | With |
| --- | --- |
| `acme-payments-checkout`, `acme_payments_checkout` | `<company>-<org>-<team>`, `<company>_<org>_<team>` |
| `acme-payments`, `acme_payments` | `<company>-<org>`, `<company>_<org>` |
| `acme-lisbon`, `acme_lisbon` | `<company>-<site>`, `<company>_<site>` |
| `heinzel-acme`, `heinzel_acme`, `acme` (module and command) | `heinzel-<company>`, `heinzel_<company>`, `<company>` |
| `Acme`, `Payments`, `Checkout`, `Lisbon`, `acme.example` | your names and domain |
| the plugin directories under `plugins/` and the packages under `src/` | the same renames (`git mv`) |
| `.copier-answers.yml`: `plugin_name`, `project_name`, `package_name`, `github_owner` | your answers |

Then `make setup && make check`. **Check:** green, and `uv run hz <company> layers` shows four layers with the team's
stack `<company>`, `<company>-<org>`, `<company>-<site>`, `<company>-<org>-<team>`.

Remove what is rehearsal-only: `src/heinzel_<company>/seed/`, `_world.py`, their tests and `docs/REHEARSAL.md`
(keep the seed only if the company gives you a sandbox to rehearse in). Rewrite `README.md` and `INTENT.md` for your
company. **Check:** `make check` green, `git grep -i acme` finds nothing.

The confidentiality check (`scripts/check_confidentiality.py`) still runs here: in a private repository it guards
against terms that must not appear even internally (another customer's name, say). Your own company's names belong
here, so don't put them in the term list this repository's CI uses.

## 2. Bind the company's tools

Edit `src/heinzel_<company>/_bindings.py`: one row per capability (`code-host`, `tracker`, `documents`, `calendar`,
`mail`, `meetings`, `chat`, `directory`), naming the adapter, the plugin that brings it, the transport and the login
command. The company playbook recommends exactly these rows; `hz setup <company>` offers them one by one.

Where a first-party adapter fits (GitHub through `gh`, Jira or Confluence through `acli`, Google Workspace through
`gws`, Zoom summaries through mail), bind it as Acme does. Where the company reaches a tool another way (an internal
CLI, an MCP gateway the company runs, an API with a token an employee may create), add the provider to the company
layer, or to a layer of its own if only some teams use it:

```python
# src/heinzel_<company>/_wiki.py: a provider of the documents capability for the company's own wiki
from heinzel import Document


class Wiki:
    """Reads pages of the company wiki through its CLI, logged in as the person."""

    def read(self, ref: str) -> Document: ...


# in src/heinzel_<company>/__init__.py
module.provides("documents", modes={"read"}, hosts=["wiki.<company domain>"])(Wiki)
```

and bind it in `_bindings.py` (`adapter="<company>"`). Follow the first-party adapters for the shape: an argument
list without a shell, a timeout, JSON output parsed into the capability's models, errors that name the fix, a doctor
check of the CLI's version, and tests against recorded output and a fake CLI. **Check:** `hz system doctor` shows
every `<company> binding` check up on your machine.

## 3. The org, the site and the team

- **Org** (`plugins/heinzel-<company>-<org>`): the `okr` asset type, or whatever the org plans with. Put the real
  document's id in its hint.
- **Site** (`plugins/heinzel-<company>-<site>`): the real time zone, working hours and rhythm in `_calendar.py`.
- **Team** (`plugins/heinzel-<company>-<org>-<team>`): in `__init__.py`, the real ids of the weekly report document
  and the engineering tracker in the hints, and the asset types the report really reads; in
  `templates/weekly-report.prose.md`, the report's real headings in step 1, the deadline in the commented schedule,
  and the inputs it really needs (one per repository, a mail or meetings input if the report uses them). Keep the
  invariants.

**Check:** `make check` green; `hz heinzel playbooks` lists all four; `hz heinzel new weekly-report --template
<company>-<org>-<team>:weekly-report --asset ...` followed by `hz heinzel check` has no diagnostics; `hz heinzel run
weekly-report --dry-run` fetches every input with your own logins.

## 4. Release and install

Push through pull requests (`make pr TITLE="feat: ..."`), apply the same repository settings as this repository's
(see its README and the core's CONTRIBUTING.md, "Repository settings"), then release (Actions → Release). People
install the team's plugin from the private repository over HTTPS, using their own `gh auth login` session:

```bash
hz system plugin add "git+https://github.com/<owner>/heinzel-<company>@v0.1.0#subdirectory=plugins/heinzel-<company>-<org>-<team>"
```

The team repository's `hz.yaml` names it (`plugin: {name: ..., source: ...}`), so `hz team join` shows it to
everyone who joins. **Check:** on a second machine, `hz team join` then the plugin line above then
`hz <company> layers` shows the stack.

## 5. Unknowns to verify first

In limited time, verify these in this order; each one can stop the port, and each has a fallback.

| # | Question | How to find out in minutes | If not |
| --- | --- | --- | --- |
| 1 | May employees install and run the vendor CLIs (`gh`, `acli`, `gws`) and a coding agent on their machines? | ask, or try `brew install` and the login on a managed machine | the company's software catalogue; a provider through what is allowed |
| 2 | Does each CLI's login work with the company's SSO, as an ordinary employee? | `gh auth login`, `acli jira auth login --web`, `gws auth login` | a provider with a token the person may create, kept by `hz system credential` |
| 3 | May an employee create their own Google OAuth client for `gws`, or does the Workspace block unverified apps? | `gws auth setup` then `gws auth login` with a work account | ask IT for an internal client; or read documents through another provider |
| 4 | May work content be sent to the agent runner the company uses? | the company's policy on AI tools and data classes | a runner the company approves; or drafts from metadata only |
| 5 | Where does the weekly report live, and what are its sections, deadline and audience? | the last three reports | the template's steps and headings |
| 6 | Which repositories, tracker project and documents does the report read, and their ids? | the people who write it | the hints and `--asset` values |
| 7 | Is the code host GitHub.com or an Enterprise Server, and does `gh` reach it? | `gh auth status` | `gh`'s host setting; the adapter follows it |
| 8 | Are meeting summaries mailed to people, and may they be read? | a recent summary e-mail | leave meetings out of the report |
| 9 | Who approves the draft, and where (ADR 0038's tag in the document, or by hand)? | the report owner | local drafts, edited and sent by hand |
| 10 | Which names, ids and terms are confidential even inside the company? | the person and the company's policy | keep them out of the repository; the term list guards it |

Record each answer (yes, no, unknown) and its date in `INTENT.md`; an unknown is a finding for the next session, not a
reason to guess.
