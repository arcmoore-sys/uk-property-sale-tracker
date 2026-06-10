---
name: re-sales-process-bids
description: >
  This skill should be used to find, log and compare received bids. Trigger when the
  user says "log this bid", "record the offer", "update the bid log", "check email
  for new bids", "any new offers in", "download the bids from my inbox", "summarise
  the bids", "compare round 1 and round 2", "compare the rounds", "what changed
  between rounds", or when review-inbox detects an incoming bid. It can sweep the
  agent's email for new bid emails and download their attachments, extracts the key
  terms of each bid into tracker.json, renders the three-round comparison on the Bid
  Log tab, and builds a round-over-round change narrative.
metadata:
  version: "0.3.0"
---

# Process bids (log terms and compare up to three rounds)

Turns received bid documents into structured data and a change narrative, and keeps
the client-ready comparison on the Bid Log tab current. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. Bids are held in
`tracker.json.bids`, one record per buyer per round, with `round` in {1, 2, 3}.

## Mode A0: sweep email for new bids

Run this when the user asks to check email for bids, or at the start of any bid run
when no document was supplied, so received offers are pulled in automatically rather
than waiting to be pasted.

1. Identify the deal and load its `tracker.json`. Determine the open round from
   `deal.current_round` (treat round 1 as the default if it is still 0).
2. Search the agent's email with the connected email tool for offers on this deal:
   query by property name/address, by the known buyer email addresses in
   `tracker.json.buyers`, and for offer language ("offer", "bid", "best and final",
   "subject to contract", a price, a yield). Restrict to messages newer than the
   most recent `bid-received` entry in `correspondence-log.md` so nothing is
   double-counted.
3. For every message that is a bid, download its attachments (offer letter, heads of
   terms, proof of funds) and save them into `bids/round-<N>/`, named
   `<buyer-slug>-<round>-<short-desc>.<ext>`. If the offer is in the email body only,
   save the body as `bids/round-<N>/<buyer-slug>-<round>-email.md`. Skip any bid
   already filed for that buyer and round (dedupe by buyer + round).
4. Match each bid to a buyer record by email or name; if the sender is not yet a
   buyer, add a buyer record (as `review-inbox` would) before logging.
5. Hand each downloaded bid to Mode A to extract terms and log it. Keep the raw files
   as the audit trail.
6. If no email tool is connected, say so and fall back to Mode A with a
   user-supplied or pasted bid.

After the sweep, report which messages were found, which were filed as new bids, and
which were skipped as already logged, then continue into Mode A for each new one.

## Mode A: log a received bid

For each new bid (swept from email in Mode A0, passed from `review-inbox`, or
supplied by the user):

1. Identify the buyer and round. Save the raw document into `bids/round-<N>/` if not
   already filed.
2. Extract the key terms: offer price, net initial yield, deposit, funding type and
   proof of funds, conditions (subject to survey / board / IC / planning, etc.),
   proposed completion, exclusivity request, solicitor, and any material notes.
   Where a term is not stated, record it as blank rather than guessing.
3. Append a record to `tracker.json.bids` with the round set. Keep money and
   percentages as real numbers so they sort and compute.
4. Set the buyer's `bid_status_round_<N>: received` in `tracker.json`.
5. Log it in `correspondence-log.md` (type `bid-received`).

## Mode B: compare rounds

Run when a later round's bids are in, or on request. The Bid Log tab already shows
the side-by-side matrix with price deltas and movement flags. In chat, produce a
short narrative to accompany it:

- For every bidder, describe what moved between the relevant rounds (for example
  price plus £1,500,000, yield in by 19 basis points, "subject to survey" removed,
  completion brought forward two weeks), and whether their position strengthened or
  weakened.
- Flag drop-outs (bid in an earlier round, silent in the current round; the matrix
  marks these Withdrawn) and new entrants (first bid after round 1; marked New).
- End with the standing: current highest offer, the leader, and any conditions that
  materially affect deliverability rather than headline price alone.

## After running

Write `tracker.json`. Update the following `tasks` entries using these exact task
names (they must match the workbook's seeded names exactly):
- `"Receive and log round 1 bids"` → `"In progress"` while round 1 is open;
  `"Complete"` once all round-1 bids are in (phase `"4. Bids & offers"`,
  `automated_by` `"process-bids"`).
- `"Analyse bids, report to client"` → `"In progress"` once any bids are logged
  (phase `"4. Bids & offers"`, `automated_by` `"process-bids"`).
- `"Log round 2 bids and compare rounds"` → `"In progress"` while round 2 is open;
  `"Complete"` once all round-2 bids are in and compared (phase `"4. Bids & offers"`,
  `automated_by` `"process-bids"`). Only include this entry if a round-2 bid has been
  logged.

Run `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>` to
repopulate the Bid Log matrix, and regenerate `tracker-snapshot.md`. The Bid Log tab
carries a title and subtitle block and is ranked and formatted so the agent can select
it and paste a clean comparison into the client report between rounds. Offer to run
`client-report` to send the round update, or `select-and-hot` once the client picks
a preferred bidder.
