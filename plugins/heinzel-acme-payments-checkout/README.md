# heinzel-acme-payments-checkout

The team layer of [heinzel-acme](../../README.md), Heinzelmännchen's made-up reference company: **Checkout**, a team
of the org `acme-payments` at the site `acme-lisbon`. Installing it installs its stack: `acme`, `acme-payments`,
`acme-lisbon`.

It brings the weekly report playbook:

- asset types `weekly-report` (the rolling report document, kept by the template), `engineering-tracker` (the
  tracker sheet), `tracker-project` (the Jira project key) and `code-repo` (the repository), with hints where a
  capability can confirm one;
- the template contract `acme-payments-checkout:weekly-report`: a draft ready by Friday 17:00 Lisbon time from the
  week's merged pull requests (code host), changed items (tracker), the engineering tracker and the previous report
  (documents), in the previous report's structure and tone, saved locally for the report owner;
- the draft tags for approving in place (core ADR 0038), shown by `hz acme-payments-checkout info`.

```bash
hz heinzel new weekly-report --template acme-payments-checkout:weekly-report --asset weekly-report=<id> ...
hz heinzel run weekly-report --dry-run
```
