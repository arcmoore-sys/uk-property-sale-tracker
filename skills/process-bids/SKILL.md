---
name: process-bids
description: >
  This skill should be used to log received bids and compare bid rounds. Trigger
  when the user says "log this bid", "record the offer", "update the bid log",
  "summarise the bids", "compare round 1 and round 2", "compare the rounds", "what
  changed between rounds", or when review-inbox detects an incoming bid. It extracts
  the key terms of each bid into tracker.json, renders the three-round comparison on
  the Bid Log tab, and builds a round-over-round change narrative.
metadata:
  version: "0.2.0"
---

# Process bids (log terms and compare up to three rounds)

Turns received bid documents into structured data and a change narrative, and keeps
the client-ready comparison on the Bid Log tab current. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. Bids are held in
`tracker.json.bids`, one record per buyer per round, with `round` in {1, 2, 3}.

## Mode A: log a received bid

For each new bid (passed from `review-inbox` or supplied by the user):

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

Write `tracker.json`, run
`python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>` to repopulate
the Bid Log matrix, and regenerate `tracker-snapshot.md`. The Bid Log tab carries a
title and subtitle block and is ranked and formatted so the agent can select it and
paste a clean comparison into the client report between rounds. Offer to run
`client-report` to send the round update, or `select-and-hot` once the client picks
a preferred bidder.
