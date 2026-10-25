# heinzel-acme-lisbon

The site layer of [heinzel-acme](../../README.md), Heinzelmännchen's made-up reference company: **Acme Lisbon**,
under the company layer `acme` and beside the org tree. It brings the site calendar as data: the time zone
(Europe/Lisbon, a setting `[acme-lisbon] time_zone` its playbook recommends), working hours, and the rhythm of
stand-up, planning, demo and the Friday 17:00 weekly report deadline.

```bash
hz acme-lisbon calendar --days 7     # at the site and on this machine
hz setup acme-lisbon
```
