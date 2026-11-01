# Threat model

What the ACME plugins touch, whose login they use, and what stays on your machine. Report problems through
[SECURITY.md](../SECURITY.md).

| Part | Reads | With whose login | Writes | Never leaves the machine |
| --- | --- | --- | --- | --- |
| Layers (`acme`, `acme-payments`, `acme-lisbon`, `acme-payments-checkout`) | Nothing outside the plugin: settings, the Lisbon calendar, role and binding recommendations | None | Nothing; bindings apply only after your yes in `hz setup` | Everything |
| Weekly-report contract | Merged pull requests, tracker items, the engineering tracker and the previous report, through the adapters you bound | Yours, through `gh`, `acli` and `gws` | The draft, in your local Heinzelmännchen data directory | The draft: nothing is posted or sent for you. Inputs go only to the agent runner you configured |
| `hz acme seed` | Your accounts, to find what exists | Yours | A demo repository, a Jira project and three Google files, only with `--yes` | The dry-run plan |
| Development scripts | Local files and Git history | Yours | Lockfile, changelog, tool manifest | Everything: input comes from a developer or Git hook, never from a network or plugin |

## Rules

- Plugins run with your rights, so install only plugins you trust.
- Use `hz acme seed` only with trial accounts, never a company account.
- Development scripts run frozen installs without builds. Do not widen scanner exclusions or suppress a finding
  without a finding-specific reason.
