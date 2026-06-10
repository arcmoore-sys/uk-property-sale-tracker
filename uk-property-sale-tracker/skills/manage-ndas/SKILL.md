---
name: re-sales-manage-ndas
description: >
  This skill should be used to send NDAs to prospective buyers and to chase those
  who have not returned a signed copy. Trigger when the user says "send the NDA",
  "send NDAs to new buyers", "chase the NDAs", "who hasn't signed", "follow up on
  outstanding NDAs", or when run on a schedule for the every-2-days chaser. It
  pulls the NDA template from the deal folder, emails it to buyers who need it, and
  sends a polite chaser every 2 days to non-responders.
metadata:
  version: "0.1.0"
---

# Manage NDAs (send and chase)

Handles the NDA leg of the pipeline. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. Respect the deal's `send_mode`:
`auto` means send immediately; `draft` means stage a draft and tell the user to
review. This deal defaults to `auto`.

## Identify the deal and template

Load the deal's `tracker.json`. Locate the NDA template in `nda/`. If no template
is present, do not fabricate a binding legal document: tell the user to drop their
template into `nda/`, and only fall back to the generic example at
`${CLAUDE_PLUGIN_ROOT}/assets/NDA-template-EXAMPLE.docx` (clearly labelled as a
placeholder for solicitor review) if they ask you to proceed anyway.

## Mode A: send NDAs to buyers who need them

For every buyer with `nda_status: not_sent`:

1. Personalise the NDA template with the buyer's name/company and the property.
2. Send it from `~~email` with a brief, professional covering message inviting them
   to sign and return. UK tone: courteous and concise.
3. Set `nda_status: sent`, `nda_sent_date` = today, `last_chase_date` = today,
   `chase_count` = 0.
4. Log it in `correspondence-log.md` (type `nda`).

## Mode B: chase non-responders (the every-2-days job)

This mode runs from the daily scheduled task created by `setup-deal`. For every
buyer with `nda_status: sent` (i.e. sent but not yet `signed`):

1. Compute days since `last_chase_date` (or `nda_sent_date` if never chased).
2. If **2 or more days** have passed, send a polite chaser from `~~email`:
   friendly, low-pressure, restating that returning the signed NDA unlocks the
   information pack / next steps. Vary wording slightly each time so it does not
   read as a robot. Re-attach the NDA for convenience.
3. Set `last_chase_date` = today and increment `chase_count`.
4. Log it in `correspondence-log.md` (type `chase`).
5. Never chase a buyer whose `nda_status` is `signed`.

Consider easing off after several unanswered chases (e.g. flag buyers at
`chase_count >= 5` for the agent to decide rather than chasing forever) and mention
these in the summary.

## After running

Update `tracker.json`, regenerate `tracker-snapshot.md`, and report who was sent an
NDA and who was chased. If signed NDAs have come back, point the user to
`review-inbox` (or note it already filed them if run as part of that flow).
