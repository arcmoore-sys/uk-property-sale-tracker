---
name: select-and-hot
description: >
  This skill should be used to select the preferred bidder, draft Heads of Terms,
  record exclusivity, and notify unsuccessful bidders. Trigger when the user says
  "select the preferred bidder", "we are going with [buyer]", "draft Heads of
  Terms", "agree HoT", "set up exclusivity", "notify the underbidders", or "tell the
  others they were unsuccessful". It records the selection, drafts the HoT, and sends
  the unsuccessful-bidder notes.
metadata:
  version: "0.1.0"
---

# Select preferred bidder and agree Heads of Terms

Bridges the bid process and the legal phase. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. Respect the deal's `send_mode`
(`auto` sends, `draft` stages for review).

## Steps

1. **Identify the deal** and load `tracker.json`. Confirm the preferred bidder with
   the user (do not infer it from highest price alone; deliverability and
   conditionality matter). Record `preferred_bidder` with buyer, price and notes, and
   set `deal.preferred_bidder_date`.

2. **Draft the Heads of Terms.** Start from the deal's HoT template if present in
   `04-legals/` (the firm's own, or the bundled `HOT-template-EXAMPLE.md` placed there
   at setup; fall back to `${CLAUDE_PLUGIN_ROOT}/assets/HOT-template-EXAMPLE.md`).
   Produce a clear, non-binding (subject to contract) HoT covering the parties, the
   property, price, deposit, conditions, exclusivity period, the timetable to exchange
   and completion, and each side's solicitors. Save the drafted HoT into `04-legals/`
   (do not overwrite the blank template). In `auto` mode send it to the preferred bidder; in
   `draft` mode stage it for the agent. Mark it clearly as subject to contract and
   for the client's solicitor to settle.

3. **Record exclusivity.** If a lockout or exclusivity period is agreed, record the
   end date in `preferred_bidder.exclusivity_until` and reflect the milestone in
   `legals`.

4. **Notify unsuccessful bidders.** For every other party who bid, send a courteous
   note that they were not selected, without disclosing the winning figure or other
   parties' positions. Set their `bid_status_round_<current>` to `declined`. Log
   each in `correspondence-log.md`.

5. **Update the workbook.** Set the phase 5 `tasks` and the early `legals`
   milestones (preferred bidder confirmed, HoT agreed, exclusivity in place), write
   `tracker.json`, run
   `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`, and
   regenerate `tracker-snapshot.md`.

## Output

Confirm the preferred bidder, that the HoT was drafted and sent or staged, the
exclusivity position, and that underbidders were notified. Offer to run
`track-legals` to manage the path to exchange.
