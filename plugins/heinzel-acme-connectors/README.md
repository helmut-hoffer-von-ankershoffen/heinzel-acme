# heinzel-acme-connectors

ACME's own connectors: how a company implements every Heinzelmännchen connector in its private plugin repository.
Every adapter runs on dummy data and reaches it through one seam, shaped for a company MCP gateway with one local
launcher per tool. Replace the seam and the adapters read your tools.

| Capability | Core protocol | What the dummy does | What a real company replaces |
| --- | --- | --- | --- |
| `calendar` | `Calendar` | ACME's week: events with attendees and a video call, free/busy, create, move, cancel; `respond` is unsupported | `_backend.connect("calendar")`, and the tool names in `CONNECTORS` |
| `mail` | `Mail` | Nadia's mailbox: search, read, threads, drafts, labels; mail bodies in an untrusted envelope, one of them hostile; `send_draft` is unsupported | `_backend.connect("mail")` |
| `documents` (drive) | `Documents` | Adapter `acme-connectors-docs`: `docs.acme.example` links and `doc-…` ids, read only | `_backend.connect("docs")` |
| `documents` (wiki) | `Documents` | Adapter `acme-connectors-wiki`: `wiki.acme.example` links and page ids, read only | `_backend.connect("wiki")` |
| `tracker` | `Tracker` | The Checkout project `CHK`: read, create, claim (not atomic), move, comment, close; `attach` is unsupported | `_backend.connect("tracker")`; an atomic claim needs a gateway tool that assigns only if unassigned |
| `chat` | `Chat` | Two backends, chosen by `acme-connectors.chat_backend`: `memory`, Slack-like channels with `messages`, `post`, `notify_self` and `ask_self`; or `command`, which runs `acme-chat` for `notify_self` and `ask_self` only | `_backend.connect("chat")`, or `acme-connectors.chat_command` set to your own chat command |
| `meetings` | `Meetings` | Zoom-like meetings; only the recorded one has a transcript | `_backend.connect("meetings")` |
| `code-host` | `CodeHost` | Merged pull requests of `acme/acme-checkout` | `_backend.connect("code-host")` |
| `directory` | `Directory` | Who reports to whom in Payments | `_backend.connect("directory")` |
| `ai-models` | `AiModels` (ADR 0159) | ACME Fast and ACME Deep, dummy models that answer offline; one model switched off. Registered on a Core with the capability | `AcmeModels.model`: build a Pydantic AI model on your own HTTP client for your model gateway |

ACME keeps documents in two stores, so it ships two documents adapters. That is the pattern for any capability with
two sources: one adapter per source, each declaring with `links` the host of the addresses people open. Core 0.9.43
(ADR 0161) binds both (`hz system config set capabilities.documents '["acme-connectors-docs", "acme-connectors-wiki"]'`),
sends each link to the adapter whose `links` name its host, and fans a search out to both. An older Core binds one.

Everything is fictional: ACME at acme.example, org Payments, team Checkout, site Lisbon, and its people (Nadia
Moreira, Tomas Leal, Priya Raman), in the week of 2 November 2026.

## Pick them

ACME's company layer keeps binding its capabilities to the first-party plugins (GitHub, Google, Atlassian, Zoom;
`src/heinzel_acme/_bindings.py`), and its rehearsal uses those. This plugin is a separate worked example: installed,
it offers its connectors as alternatives you pick per capability, in the app (Settings, Connectors, "Which connector
serves what"; each change asks to restart and apply) or on the command line:

```sh
hz system config set capabilities.mail acme-connectors
hz system config set capabilities.documents acme-connectors-wiki
hz system config set acme-connectors.chat_backend command   # chat through acme-chat
hz system config set acme-connectors.sign_in_state expired  # show the expired sign-in
```

It never writes a binding and never overrides one: a binding you or a playbook set (`hz setup acme` writes
`capabilities.code_host = "github"` and the rest) stays as it is when this plugin is installed
(`tests/integration/connectors_bindings_test.py`). A capability nothing binds is served by its only installed adapter
(Core ADR 0055): without the first-party plugins that is this plugin for calendar, chat, code host, meetings and
tracker, which is what a demo wants; alongside them, it is so only for chat, which none of them provides.

## Connected and signed in

`hz system connector list` and the app's connector page show the sign-in through a dummy `SignInProvider`
(`_sign_in.py`, ADR 0136). It reports one of three states, chosen by `acme-connectors.sign_in_state`: signed in as
nadia@acme.example, signed out, or expired, with the problem in words. `sign_in` reports a made-up consent page at
login.acme.example, and `sign_out` forgets the sign-in, both for the running process. An offline health check
(launchers and sign-in) runs in `hz system doctor`. A live check starts every connector and checks its tools, on
`hz system connector test acme-connectors`. A real plugin asks its gateway launcher instead.

## The seams

`src/heinzel_acme_connectors/`:

- `_backend.py` is **the one file a company replaces**. Every gateway adapter reaches data only through
  `connect(name).call(tool, arguments)`, which returns a `Reply` (`data`, `text`, and `untrusted`, the segments the
  gateway marked), shaped like Core's `McpResult`. Each connector in `CONNECTORS` names its local stdio launcher
  (one per connector, holding the sign-in, so the plugin holds no secret), the tools its adapter calls (`McpTool`:
  name, read or write, aliases), and the untrusted-content markers its answers carry. Today `connect` serves the dummy
  data through `StandInConnector`, which checks at startup that every tool exists and takes the markers off. With
  Core's MCP helper (ADR 0159, `heinzel.connectors.mcp`) `connect` returns `McpConnector(launcher, tools=...,
  markers=...)` instead; the module docstring shows the code.
- `_markers.py` is the untrusted-content path. A gateway marks text people wrote inline
  (`«untrusted-data»…«/untrusted-data»`) or, for mail bodies, in an envelope with a fresh UUID
  (`<untrusted-mail-data-UUID>…</untrusted-mail-data-UUID>`), so text inside can't close it. The markers come off,
  any stray or forged marker is removed, and `_text.py` passes every string through Core's `clean_text`, as Core
  asks of every adapter. What the text says stays data, never an instruction.
- `_chat_command.py` and `acme_chat.py`: the chat command backend. The adapter runs the command with an argument
  list (never a shell), a timeout, nothing on stdin, and reads at most 64 KiB of one JSON object; a non-zero exit, a
  timeout or bad JSON is a clear error. `acme-chat` is a made-up command (`tell`, `question`) whose answers come from
  `ACME_CHAT_ANSWER` or the file in `ACME_CHAT_ANSWERS`, so it never blocks for real.
- `_compat.py`: stand-ins for what Core ships after 0.9.42: `NotSupportedError` and `unsupported` (ADR 0159),
  `ModelOffer` and `ModelUnavailableError` (ADR 0159), `SelfMessage` and `SelfAnswer` (the chat self channel, ADR
  0160). With that Core they are Core's own.
- One module per capability (`_mail.py`, `_calendar.py`, `_documents.py`, `_tracker.py`, `_chat.py`, `_meetings.py`,
  `_code_host.py`, `_directory.py`, `_ai_models.py`) maps the gateway's JSON to Core's models; keep them and change
  the mapping where your gateway answers differently.
- `_dummy.py`: the in-memory servers and their fixtures. A real plugin deletes it.

Modes are honest: an adapter declares `write` only when one of its capability's write methods works, so the
documents adapters are read only. What a connector can't do is listed in `unsupported` (per instance for chat,
whose backend decides) and refused with `NotSupportedError` before anything reaches the gateway.

## Make it your company's

1. Copy this directory into your company's private plugin repository (no remote needed) and rename it.
2. In `_backend.py`, point each connector's launcher at your gateway's, list the tools it really has, and return the
   MCP client from `connect`. Delete `_dummy.py` and the stand-in.
3. Set the hosts in `__init__.py` to your gateway's and your document stores', and adjust `unsupported` and the modes
   to what your gateway can do.
4. Install it from the folder: `hz system plugin add /path/to/your-repo` (Core 0.9.43 or later).

## Requirements

- Heinzelmännchen 0.9.41 or later; tested on 0.9.42. `ai-models`, the MCP helper, the chat self channel and
  `unsupported` handled by the kernel need the Core release that ships ADR 0159 and ADR 0160 (to be decided); until
  then the stand-ins in `_compat.py` keep the plugin working.
- Python 3.12 or later.

Tests (`tests/unit`, `tests/integration`) check each adapter against its Core protocol (signatures, honest modes,
`unsupported`, hosts), its behaviour on the dummy data, the chat command's timeout, bad JSON and failing exit, and
every capability bound through a kernel.
