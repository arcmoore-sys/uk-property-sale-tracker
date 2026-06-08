---
name: track-legals
description: >
  This skill should be used to track the legal phase from instruction of solicitors
  through exchange and completion. Trigger when the user says "update the legals",
  "where are we on the legal side", "track to completion", "log the exchange",
  "contract pack issued", "CPSE replies sent", "we exchanged", "we completed", or
  asks for the conveyancing status. It maintains the legal milestones and the
  completion checklist.
metadata:
  version: "0.1.0"
---

# Track legals and completion

Owns the back end of the deal. Keeps the legal milestone tracker current and
chases the path to exchange and completion. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first.

## Steps

1. **Identify the deal** and load `tracker.json`. If `legals` is empty, seed it from
   the standard milestone list (the workbook seeds the same): solicitors instructed,
   contract pack issued, CPSE replies provided, searches submitted, enquiries
   answered, buyer approval and funding confirmed, contract engrossed, exchange,
   deposit received, completion, apportionments, tenant notices, managing agent
   handover.

2. **Update milestones.** For each milestone the user reports on, set the status
   (`In progress` or `Complete`), the actual date, and any note. File the underlying
   documents (HoT, contract pack, replies to enquiries, searches, completion
   statement) into `04-legals/`. When exchange and completion dates are set or hit,
   update `deal.target_exchange`, `deal.target_completion` and
   `deal.actual_completion`.

3. **Surface what is blocking.** Identify the critical-path item the deal is waiting
   on (for example outstanding enquiries or buyer funding) and who owns it, so the
   agent can chase the right party.

4. **Update the workbook.** Set the phase 6 `tasks`, write `tracker.json`, run
   `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`, and
   regenerate `tracker-snapshot.md`.

## Output

Report the current legal stage, the milestones completed this run, the next
critical-path item and its owner, and the live exchange and completion targets.
Offer to run `client-report` to update the client.
