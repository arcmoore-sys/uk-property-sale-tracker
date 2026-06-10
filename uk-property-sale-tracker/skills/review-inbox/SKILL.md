---
name: re-sales-review-inbox
description: >
  This skill should be used to scan the agent's email for a property deal and
  refresh the live buyer tracker and dashboard. Trigger when the user says "review
  my inbox", "check email for [deal]", "update the tracker", "refresh the
  dashboard", "any new buyers / signed NDAs / bids", or "what's the status of
  [property]". It reads the inbox, detects new buyers, signed NDAs and incoming
  bids, updates tracker.json, files documents, refreshes the master workbook, and
  rebuilds the live dashboard artifact.
metadata:
  version: "0.2.0"
---

# Review inbox and refresh the tracker

This is the hub skill. It reconciles email against the deal's `tracker.json`,
refreshes the master workbook, and rebuilds the live dashboard. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first.

## Steps

1. **Identify the deal.** If the user named a property, use it; otherwise list the
   deal folders and ask which one (or offer "all"). Load that deal's `tracker.json`.

2. **Pull recent email** from the agent's account related to this deal, searching by
   property name/address and by the known buyer email addresses, plus anything new
   since the last review. Read bodies and attachments.

3. **Classify each relevant message** and update `tracker.json`:
   - **New prospective buyer** -> add a buyer record with `nda_status: not_sent`,
     `aml_status: pending`, `pof_status: pending`. Hand to `manage-ndas` so the NDA
     goes out.
   - **Signed NDA received** -> save the attachment to
     `nda/signed/<buyer-slug>-signed-NDA.<ext>`, set `nda_status: signed` and
     `nda_signed_date`, stop chasing that buyer, and prompt `qualify-buyer` to run
     AML and proof of funds before they receive the process letter.
   - **Bid received** -> save the document into `bids/round-<N>/`, set
     `bid_status_round_<N>: received`, and hand to `process-bids` to log the terms
     into `tracker.json.bids`.
   - **Other replies** (questions, scheduling) -> note in the buyer's `notes`.

4. **Append to `correspondence-log.md`** every message you acted on (date, buyer,
   direction, type).

5. **Refresh the records.** Write `tracker.json`, run
   `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>` to
   repopulate `mandate-tracker.xlsx`, then regenerate `tracker-snapshot.md`.

6. **Rebuild the live dashboard artifact** (see below).

7. **Summarise** what changed since last review and flag anything needing the user:
   new buyers needing NDAs, signed NDAs needing qualification, bids needing logging,
   data room gaps, or legal critical-path items. Offer to run the relevant skill, or
   do it automatically when send mode is `auto`.

## The live dashboard artifact

Create a persistent live artifact titled for the deal, e.g.
"<Deal name> mandate dashboard". It is the window onto the whole mandate, not just
the buyer list, mirroring the seven tabs of `mandate-tracker.xlsx`. Embed the
current `tracker.json` as the baseline so it renders even if the email call returns
nothing. On load it should call the connected email tool to pull recent deal email
and classify the latest status per buyer, so it reflects the inbox between full
runs. Design:

- **Deal header.** Property, client, stage, current round, quoting price and target
  NIY, key dates (launch, round 1, round 2, target exchange and completion).
- **Pipeline funnel.** A row of counts: buyers on list, NDAs issued, NDAs signed,
  buyers qualified (AML clear and proof of funds verified), round 1 bids, round 2
  bids, and the current highest offer. These mirror the workbook's Live Status
  block.
- **Buyer table.** Name, company, NDA status, last chase and chase count, AML/KYC,
  proof of funds, bid status round 1, bid status round 2, latest note. Use clear
  status pills (not sent / sent / signed; pending / clear / flagged; pending /
  verified / insufficient; none / requested / received / declined).
- **Data room readiness.** Documents in versus total, with the outstanding items by
  category called out.
- **Bid summary.** A compact view of logged bids by round, sorted by price, with
  the key conditions, so the agent can see standings at a glance.
- **Legal and completion strip.** The milestone list with status, highlighting the
  next critical-path item and the live exchange and completion targets. Only show
  this section once the deal has reached the legal phase.
- **Reporting.** The date of the last client report and the next one due.

Probe the email tool's real response shape once in chat before wiring it into the
artifact, then parse what you actually observed. The view header already provides a
Reload button; do not add your own. Keep the authoritative records in the files; the
artifact and the workbook are both views onto `tracker.json`.
