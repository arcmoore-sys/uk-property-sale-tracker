---
name: client-report
description: >
  This skill should be used to generate and log client progress reports, the final
  closing report, and the fee invoice. Trigger when the user says "send the client
  update", "weekly report", "report to the client", "closing report", "wrap up the
  deal", "invoice the fee", or when run on a weekly schedule. It builds the report
  from the live tracker state, sends or stages it, and logs it.
metadata:
  version: "0.1.0"
---

# Client reporting

Generates the recurring client update and the end-of-deal closing pack from the
tracker, so reporting is a by-product of the state rather than a manual write-up.
Read `${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. Respect the deal's
`send_mode` (`auto` sends, `draft` stages for review).

## Mode A: weekly progress report

1. Load `tracker.json` and read the current state across all blocks.
2. Compose a concise, professional client update: where the process is (stage and
   round), buyer activity since the last report (new parties, NDAs signed, buyers
   qualified), bid standings without breaching any confidentiality the client
   expects, data room readiness, the next milestones and dates, and anything needing
   the client's decision. Keep it tight and factual.
3. Send from the agent's email in `auto` mode, or stage it in `draft` mode. File a
   copy into `05-reporting/`.
4. Append a row to `reporting` (`type: Weekly update`, period, sent to, method) and
   log it in `correspondence-log.md`.

## Mode B: closing report and fee invoice

Run at completion.
1. Produce a closing report: final price and terms, the process run (parties,
   rounds, timetable), and the outcome against the mandate. File into
   `05-reporting/`.
2. Prepare the fee invoice from the `deal.fee_basis` and the agreed price, plus any
   disbursements. Stage it for the agent to issue.
3. Append a `reporting` row (`type: Closing report`) and mark the phase 7 `tasks`
   complete.

## After running

Write `tracker.json`, run
`python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`, regenerate
`tracker-snapshot.md`, and confirm what was sent or staged and logged.
