# The ACME dress rehearsal

A rehearsal of Heinzelmännchen's first slice, the team's weekly report, on two machines and in **your own trial
accounts**, with the made-up ACME world seeded into them. The Mac mini plays the Checkout team's engineering manager
(Nadia in the ACME world, the report owner); the MacBook Air plays an engineer who joins the team. At the end you
have a draft of Checkout's weekly report, made from real pull requests, Jira items and Google documents, and numbers
that say how well each step went.

Never run any of this against a company account: `hz acme seed` creates repositories, projects and documents.

## What you need first

| Account or tool | For | Notes |
| --- | --- | --- |
| A GitHub account per machine (a second, free one for the engineer) | the demo repository, the team repository, `gh` | the manager's account owns both repositories and invites the engineer |
| An Atlassian Cloud site on a free plan | the Jira project `CHK`, `acli` | create one at atlassian.com; note its URL and your login e-mail |
| A Google account | the three documents, `gws` | a personal account works; `gws` needs a Desktop OAuth client you create yourself in a Google Cloud project (`gws auth setup`), no administrator involved |
| Claude Code, logged in, on both machines | the agent runner that drafts | `hz system doctor` checks it |
| Zoom with AI Companion summaries | optional: meetings | needs a paid Zoom plan; the weekly report doesn't read meetings, so skip it |
| `uv`, `git`, `gh`, `acli`, `gws` (Node.js for it) | everything | The [standard app installer](https://helmut.hoffer-von-ankershoffen.me/heinzel/guides/install/) can install uv; the optional integrations need their vendor CLIs. |

## Mac mini: the manager

### 1. Install Heinzelmännchen and the plugins

Start the standard app, including its default plugins:

```sh
uvx heinzel@latest
```

Leave the workspace running and use another terminal for the optional integrations:

```bash
hz system plugin add github --confirm
hz system plugin add atlassian --confirm
hz system plugin add google --confirm
hz system plugin add "git+https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme#subdirectory=plugins/heinzel-acme-payments-checkout" --confirm
hz acme layers                   # four layers; the team's stack is acme, acme-payments, acme-lisbon, acme-payments-checkout
hz system layer show             # the same stack, from the core (a core with the layer API)
```

### 2. Log in, as yourself

```bash
gh auth login
acli jira auth login --web
gws auth setup                   # once: your own OAuth client
gws auth login --scopes https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/documents.readonly,https://www.googleapis.com/auth/spreadsheets.readonly,https://www.googleapis.com/auth/drive.metadata.readonly
```

`drive.file` lets the seed create its three documents (and only files it creates); the read-only scopes are what the
Google adapter reads with. After the rehearsal, log in again without `drive.file`.

### 3. Accept ACME's bindings

```bash
hz setup acme           # code-host github, tracker atlassian, documents/calendar/mail google, meetings zoom: yes to each you use
hz setup acme-lisbon    # the site's time zone, Europe/Lisbon
hz system doctor        # every "acme binding" check up, except the ones you skipped
```

### 4. Seed the ACME world

```bash
hz acme seed --github-owner <your login> --email <your Atlassian e-mail>          # a dry run: every command, nothing runs
hz acme seed --github-owner <your login> --email <your Atlassian e-mail> --yes    # creates it
```

It creates the private repository `<your login>/acme-checkout` with four pull requests (three merged), the Jira
project `CHK` with seven items in To Do, In Progress and Done, and three Google files: the rolling **Checkout weekly
report** (weeks 41 and 42), **ACME Payments OKRs Q4** and the **Checkout engineering tracker** sheet. It stops at
the first failure; seed the parts that didn't finish again with `--only github`, `--only jira` or `--only google`.
The last lines are the `hz heinzel new` command with every `--asset` filled in.

The project template key the seed uses is not verified on every Jira plan. If "Create the Jira project" fails,
create a Kanban project with key `CHK` in the browser, then run the item and transition commands that
`hz acme seed --only jira` (the dry run) lists, and record the failure under "What to measure".

### 5. Create the team

```bash
hz team new checkout --github <your login>/hz-team-checkout --yes
```

Then, in the new repository's `hz.yaml`, name the team's plugin and what the team recommends, and commit it:

```yaml
plugin:
  name: heinzel-acme-payments-checkout
  source: "git+https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme#subdirectory=plugins/heinzel-acme-payments-checkout"
recommend:
  plugins: [heinzel-github, heinzel-atlassian, heinzel-google]
  bindings: {code-host: github, tracker: atlassian, documents: google}
```

Invite the engineer's GitHub account to both repositories (read is enough for the demo repository), and add them to
the roster:

```bash
hz team add <engineer handle> --login <engineer login> --role engineer --yes
```

### 6. Run the weekly report

```bash
hz heinzel new weekly-report --template acme-payments-checkout:weekly-report --asset ...   # the seed's last lines
hz heinzel show weekly-report              # every requirement bound, nothing unmet
hz heinzel wake weekly-report --dry-run     # the packet: merged pull requests, CHK items, the report, the tracker
hz heinzel wake weekly-report               # the draft
hz heinzel drafts --name weekly-report --latest
```

Edit the draft as Nadia would, "send" it (paste it into the weekly report document under a new week), then record it:

```bash
hz heinzel sent weekly-report --file <the text you sent> --edit-minutes <your estimate>
hz heinzel show weekly-report              # the success test: drafting time, cost, share changed
```

`hz heinzel discover` runs the playbooks' hints: in a trial account they find nothing, because the hints name ACME's
own (made-up) document ids. That is expected; note it under "What to measure".

## MacBook Air: the engineer

Use the standard app's versionless invite line:

```bash
uvx heinzel@latest join https://github.com/<manager login>/hz-team-checkout
```

The launcher installs the standard app and default plugins when needed. Follow the current
[join-your-team guide](https://helmut.hoffer-von-ankershoffen.me/heinzel/guides/joining/) for authentication,
setup, plugin confirmation and the information kept locally.

Joining configures team membership; it does not install ACME or its integrations. On the engineer's machine,
repeat the plugin additions in step 1, sign in as the engineer in step 2, and accept the bindings in step 3.

Then run the weekly report the way the manager did (step 6), against the same seeded world.

## What to measure

Write each number down as you go; the point is to find what breaks before a real team sees it.

| Measure | How |
| --- | --- |
| Time to the first draft, manager | wall clock from the standard app launcher to the first draft, per step |
| Time to join, engineer | wall clock from the invite URL to `hz acme layers` showing the stack |
| Steps and questions | every command typed and every prompt answered; each one the target flow should remove |
| Where it stopped | each failure: the step, the message, whether its fix was in the message |
| Logins and scopes | which vendor login or scope was missing when first needed |
| Discovery | what `hz heinzel discover` found (expected: nothing in a trial) and what you had to name by hand |
| Draft quality | `hz heinzel show weekly-report`: share of words changed, drafting time, cost; your edit minutes |
| Faithfulness | every statement in the draft traceable to a pull request, a CHK item or a document line |
| Doctor | `hz system doctor` after setup: every check up, or why not |

## Clean up

Delete `<your login>/acme-checkout` and `hz-team-checkout` on GitHub, the `CHK` project in Jira and the three Google
files, then `hz system plugin remove heinzel-acme-payments-checkout` (and the other ACME plugins) and log `gws` in
again without `drive.file`.
