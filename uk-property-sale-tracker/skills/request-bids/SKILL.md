---
name: re-sales-request-bids
description: >
  This skill should be used to issue a process letter (request for bids / call for
  offers) to all parties on a deal, for either the first or a subsequent round.
  Trigger when the user says "send the process letter", "issue the process letter",
  "request bids", "send out the call for offers", "ask for best and final", "open
  round 2", "go to second round", or when run on a schedule for the agreed process
  letter date. It emails the process letter with a bid deadline to all qualified
  parties and records that the request went out.
metadata:
  version: "0.2.0"
---

# Issue the process letter (request for bids)

Sends the process letter to everyone on the list and marks the round as requested.
In UK practice the request for bids is called a **process letter**; use that term
in correspondence and when talking to the user. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. Respect the deal's `send_mode`
(`auto` = send; `draft` = stage drafts). This deal defaults to `auto`.

## Determine the round

Load `tracker.json`. If the user named a round, use it. Otherwise: if no round has
been requested yet, this is round 1; if round 1 bids exist and the user is asking
again, this is round 2 (best-and-final). Set `deal.current_round` accordingly and
record the date in `bid_request_date_round_<N>`.

## Choose the recipient list

- **Round 1:** all parties who have a signed NDA (`nda_status: signed`). Parties
  without a signed NDA do not receive the process letter; note them as excluded and
  offer to chase their NDA via `manage-ndas`.
- **Round 2:** by default, all parties who submitted a round-1 bid
  (`bid_status_round_1: received`). Allow the user to narrow this (e.g. only the top
  N) if they say so.

## Send the process letter

For each recipient:

1. Compose a clear process letter from `~~email` covering: the asset, the bid
   submission requirements (offer price, and for investment assets the implied net
   initial / equivalent yield, funding position and proof of funds, any conditions
   such as subject to investment-committee or board approval, due-diligence
   requirements, proposed timescale to exchange/completion, and solicitor details),
   the **bid deadline**, and how to submit. For round 2, frame it as a best-and-final
   process letter and, where appropriate, reference that it follows an initial round
   without disclosing other parties' figures.
2. Send to all recipients individually (never expose the bidder list to others; no
   group email or visible CC list). Use `~~email` to send or stage each letter per
   the deal's `send_mode`.
3. Set `bid_status_round_<N>: requested` on each buyer record in `tracker.json`.
4. Log each send in `correspondence-log.md` (type `process-letter`).

## After running

Update `tracker.json`. Update the following `tasks` entry using the exact task name
for the round just issued (it must match the workbook's seeded name exactly for
`refresh_tracker.py` to update the right row):
- Round 1: `"Issue round 1 process letter"` → `"Complete"` (phase
  `"4. Bids & offers"`, `automated_by` `"request-bids"`).
- Round 2: `"Issue round 2 best-and-final process letter"` → `"Complete"` (phase
  `"4. Bids & offers"`, `automated_by` `"request-bids"`).

Run `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>` and
regenerate `tracker-snapshot.md`. Confirm the refresh completed with no formula errors.

## Output

Report how many process letters were sent (or staged), to which parties, and the bid
deadline. Name any excluded parties and the reason (unsigned NDA, not yet qualified).
Offer to run `process-bids` once bids start coming in.

## Completion checklist

The skill is done only when all of these are true:

- [ ] Deal identified, round determined, `deal.current_round` set and
      `bid_request_date_round_<N>` recorded in `tracker.json`.
- [ ] Recipient list built using the correct round rule (signed NDA for round 1;
      round-1 bid received for round 2); excluded parties noted with reason.
- [ ] Process letter composed per the template above, sent or staged individually for
      each recipient; no bidder list exposed; `bid_status_round_<N>: requested` set
      for each.
- [ ] Each send logged in `correspondence-log.md` (type `process-letter`).
- [ ] `tracker.json` written with `"Issue round 1 process letter"` or `"Issue round 2
      best-and-final process letter"` task set to `"Complete"` (matching the round
      issued); `refresh_tracker.py` ran with no formula errors; `tracker-snapshot.md`
      regenerated.
- [ ] Summary delivered: count sent, parties named, bid deadline stated, exclusions
      noted; `process-bids` offered.
