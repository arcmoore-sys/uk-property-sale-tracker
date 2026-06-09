---
name: client-report
description: >
  This skill should be used to generate and log client progress reports, the final
  closing report, and the fee invoice. Trigger when the user says "send the client
  update", "weekly report", "report to the client", "closing report", "wrap up the
  deal", "invoice the fee", or when run on a weekly schedule. It builds the report
  from the live tracker state, sends or stages it, and logs it.
metadata:
  version: "0.2.0"
---

# Client reporting

Generates the recurring client update and the end-of-deal closing pack from the
tracker, so reporting is a by-product of the state rather than a manual write-up.
Read `${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. Respect the deal's
`send_mode` (`auto` sends, `draft` stages for review).

## Output format

Every report this skill produces (the weekly update, the closing report, and the
fee invoice) is a formatted Microsoft Word document (`.docx`). Read the `docx`
skill's `SKILL.md` and follow it to build the file: use a clear heading hierarchy,
a letterhead-style title block (property name, report type, date, sending agent),
tables for the buyer pipeline, bid standings and data room status, and a clean
professional layout suitable to send straight to a client. Do not output the
report as Markdown or plain text. File the `.docx` into `05-reporting/`.

## Writing style

Never use em dashes (`—`) anywhere in the report text. Use a comma, a colon, a
full stop, or parentheses instead. This applies to the document body, tables,
headings and the email or covering note. Keep the prose tight, factual and
professional.

## Mode A: weekly progress report

1. Load `tracker.json` and read the current state across all blocks.
2. Compose a concise, professional client update as a formatted Word document (see
   Output format above): where the process is (stage and round), buyer activity
   since the last report (new parties, NDAs signed, buyers qualified), bid standings
   without breaching any confidentiality the client expects, data room readiness, the
   next milestones and dates, and anything needing the client's decision. Keep it
   tight and factual.
3. Send the `.docx` from the agent's email in `auto` mode, or stage it in `draft`
   mode. File the `.docx` into `05-reporting/`.
4. Append a row to `reporting` (`type: Weekly update`, period, sent to, method) and
   log it in `correspondence-log.md`.

## Mode B: closing report and fee invoice

Run at completion.
1. Produce a closing report as a formatted Word document (see Output format above):
   final price and terms, the process run (parties, rounds, timetable), and the
   outcome against the mandate. File the `.docx` into `05-reporting/`.
2. Prepare the fee invoice as a formatted Word document from the `deal.fee_basis` and
   the agreed price, plus any disbursements. Stage the `.docx` for the agent to issue.
3. Append a `reporting` row (`type: Closing report`) and mark the phase 7 `tasks`
   complete.

## After running

Write `tracker.json`, run
`python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`, regenerate
`tracker-snapshot.md`, and confirm what was sent or staged and logged.
