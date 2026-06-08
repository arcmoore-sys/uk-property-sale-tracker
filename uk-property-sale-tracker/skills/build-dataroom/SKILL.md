---
name: build-dataroom
description: >
  This skill should be used to assemble and track the data room for a sale. Trigger
  when the user says "build the data room", "what documents do we still need", "data
  room checklist", "set up the data room", "chase the missing docs", or "is the data
  room ready". It maintains the document checklist, tracks what is in versus
  outstanding, files documents into the 01-dataroom subfolders, and flags gaps
  before launch.
metadata:
  version: "0.1.0"
---

# Build the data room

Owns the information-gathering leg. Turns the standard UK commercial information
list into a tracked checklist and tells the agent what is still missing. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first.

## Steps

1. **Identify the deal** and load `tracker.json`. If `dataroom` is empty, seed it
   from the standard checklist (the same list the workbook seeds): title, leases,
   tenancy schedule, service charge accounts, EPC, asbestos, fire risk assessment,
   surveys, deposits and AGAs, planning, building regs, warranties, management
   agreement, vendor due diligence, and CPSE replies. Tailor it to the asset (for
   example add ground lease or headlease documents, or sector-specific consents).

2. **Reconcile what is in.** For each document the user has, set `received: Yes`,
   record the date, and file it into the matching `01-dataroom/` subfolder
   (`title/`, `leases/`, `financial/`, `compliance/`, `planning/`, `management/`,
   `diligence/`). When it is uploaded to the actual data room platform, set
   `in_dataroom: Yes`.

3. **Flag the gaps.** List every item still `received: No`, grouped by category, so
   the agent can chase the client or solicitor. Call out anything that blocks launch
   (for example missing EPC, unsigned leases, no title).

4. **Update the workbook.** Write `tracker.json`, update the phase 2 rows of
   `tasks`, run `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`,
   and regenerate `tracker-snapshot.md`.

## Output

Report the data room readiness (count in versus total), the outstanding items by
category, and any launch blockers. Offer to draft a chase note to the client or
solicitor for the missing documents.
