# Intent

## Why this repository exists

Heinzelmännchen's core knows nothing about any company: a company's structure, tools and rituals are its plugins,
stacked as layers (core ADR 0040). heinzel-acme shows what that looks like for one made-up company, ACME, end to end,
so that

1. a company can copy the shape into its own private repository (docs/PORT_TO_YOUR_COMPANY.md),
2. the core's layer, playbook and onboarding mechanisms have a test bed that breaks when they do, and
3. the first slice, the team's weekly report, can be rehearsed against a real but made-up world (docs/REHEARSAL.md).

It works when a fresh session can port it to a company in hours, and when the rehearsal ends in a weekly report draft
the report owner changes little.

## Scope

- In: ACME's four layers (company `acme`, org `acme-payments`, site `acme-lisbon`, team `acme-payments-checkout`),
  their bindings, playbooks and calendar; the rehearsal seed; the porting runbook.
- Out: anything generic, which belongs in the core; any real company, team, product or person.

## Tenets

This repository follows [Heinzelmännchen's tenets](https://github.com/helmut-hoffer-von-ankershoffen/heinzel/blob/main/INTENT.md#tenets): done, not
nagged; humans own, with lineage; composable; open and independent.
