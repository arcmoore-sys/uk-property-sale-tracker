---
name: request-bids
description: >
  This skill should be used to issue a process letter (request for bids / call for
  offers) to all parties on a deal, for either the first or a subsequent round.
  Trigger when the user says "send the process letter", "issue the process letter",
  "request bids", "send out the call for offers", "ask for best and final", "open
  round 2", "go to second round", or when run on a schedule for the agreed process
  letter date. It emails the process letter with a bid deadline to all qualified
  parties and records that the request went out.
metadata:
  version: "0.1.0"
---

# Issue the process letter (request for bids)

Sends the process letter to everyone on the list and marks the round as requested.
In UK practice the request for bids is called a **process letter** — use that term
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
  without a signed NDA do not receive the process letter — note them as excluded and
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
2. Send to all recipients (individually / via Bcc as appropriate — never expose the
   bidder list to o