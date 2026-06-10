---
name: re-sales-build-dataroom
description: >
  This skill should be used to assemble and track the data room for a sale. Trigger
  when the user says "build the data room", "what documents do we still need", "data
  room checklist", "set up the data room", "chase the missing docs", or "is the data
  room ready". It maintains the document checklist, mines the deal's email for
  document attachments and files them automatically, tracks what is in versus
  outstanding, files documents into the 01-dataroom subfolders, and flags gaps
  before launch.
metadata:
  version: "0.2.0"
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

2. **Mine email for data room documents.** If an email connector is available,
   search the agent's mailbox for messages about this deal (by property
   name/address from `deal.name`/`deal.address`, within the recent window) that carry
   attachments (`has:attachment`). For each attachment, classify it against the
   checklist using its filename and the message context, mapping common documents to
   the right checklist item and category, for example:
   - title register / title plan / TR1 / official copy → `title`
   - lease / agreement for lease / licence / tenancy schedule / rent deposit deed /
     AGA → `leases`
   - service charge accounts / budget / apportionments → `financial`
   - EPC / asbestos register or survey / fire risk assessment / FRA → `compliance`
   - planning permission / decision notice / building regs / completion certificate →
     `planning`
   - management agreement / managing agent → `management`
   - building survey / measured survey / structural / M&E / warranty / collateral
     warranty / vendor due diligence / CPSE replies → `diligence`
   Download each matched attachment and file it into the matching `01-dataroom/`
   subfolder, **renaming it to the convention in "File naming" below**, then set that
   checklist item `received: Yes` with the email's date and a
   note recording the source (sender and date). If an attachment does not map to any
   checklist item, list it as an unmatched document for the user to place rather than
   forcing a category, and never invent a document that was not actually attached. If
   no connector is available or nothing relevant is found, skip silently and move on.

3. **Reconcile anything else the user has.** For each remaining document the user
   provides directly (uploads or names), set `received: Yes`, record the date, and
   file it into the matching `01-dataroom/` subfolder (`title/`, `leases/`,
   `financial/`, `compliance/`, `planning/`, `management/`, `diligence/`), **renaming
   it to the convention in "File naming" below**. When an item is uploaded to the
   actual data room platform, set `in_dataroom: Yes`.

4. **Flag the gaps.** List every item still `received: No`, grouped by category, so
   the agent can chase the client or solicitor. Call out anything that blocks launch
   (for example missing EPC, unsigned leases, no title).

5. **Update the workbook.** Write `tracker.json`, update the phase 2 rows of
   `tasks`, run `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`,
   and regenerate `tracker-snapshot.md`. Confirm the refresh completed with no formula
   errors. If any documents were sourced from email, append a row to
   `correspondence-log.md` (type `dataroom-doc-filed`) for each.

## File naming

Every file saved into a `01-dataroom/` subfolder is renamed to a consistent
convention so the data room reads cleanly:

```
<asset>_<file type>_<date>.<ext>
```

- `<asset>` is the deal's short name (`deal.name`), e.g. `Rugby 345`.
- `<file type>` is the checklist item the document satisfies, e.g. `EPC`, `Title`,
  `Lease`, `Fire Risk Assessment`.
- `<date>` is the document's own date where known, otherwise the email date or
  today, written `YYYY-MM-DD`.
- `<ext>` is the original file extension, preserved unchanged.

For example an EPC attachment filed today becomes
`Rugby 345_EPC_2026-06-09.pdf`. If more than one file maps to the same checklist
item, append a numeric suffix before the extension (`…_2026-06-09_2.pdf`). Record
the new filename in the item's `notes` so the workbook shows what was filed.

## Output

Report the data room readiness (count in versus total), the outstanding items by
category, and any launch blockers. Offer to draft a chase note to the client or
solicitor for the missing documents.

End every run with this notice, verbatim, as the final line of the response:

> ⚠️ Please review each document manually to confirm it is correct, complete and the
> right version before sending anything to the lawyers. This skill files and names
> documents but does not verify their contents.

## Completion checklist

The skill is done only when all of these are true:

- [ ] Deal identified and `tracker.json` loaded; `dataroom` seeded from the standard
      checklist if empty, and tailored to the asset (e.g. headlease/ground lease or
      sector-specific consents added).
- [ ] Email mined for document attachments (or skipped because no connector / no
      matches); each matched attachment classified, filed into the matching
      `01-dataroom/` subfolder, and its checklist item set `received: Yes` with a
      source note; unmatched attachments surfaced rather than force-filed; no document
      invented.
- [ ] Every other document the user has is set `received: Yes` with a date and filed
      into the matching `01-dataroom/` subfolder; `in_dataroom: Yes` set for anything
      already on the data room platform.
- [ ] Every filed document renamed to `<asset>_<file type>_<date>.<ext>` (original
      extension preserved, numeric suffix on collisions), with the new filename
      recorded in the item's `notes`.
- [ ] Outstanding items (`received: No`) listed grouped by category; launch blockers
      (e.g. missing EPC, no title, unsigned leases) explicitly called out.
- [ ] Phase-2 `tasks` rows updated; `tracker.json` written; `refresh_tracker.py` ran with
      no formula errors; `tracker-snapshot.md` regenerated; `correspondence-log.md`
      updated for any email-sourced documents.
- [ ] Readiness reported (in versus total) and a chase note to client/solicitor offered.
- [ ] Closing notice shown, reminding the user to manually review each document before
      sending anything to the lawyers.
