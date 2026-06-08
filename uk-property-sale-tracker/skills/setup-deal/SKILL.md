---
name: setup-deal
description: >
  This skill should be used to start tracking the sale of a new property. Trigger
  when the user says "set up a new deal", "start tracking [address]", "new
  property sale", "create a deal folder", "onboard a new listing", or otherwise
  begins selling a new property and wants the buyer/NDA/bid process tracked. It
  creates the per-deal folder structure and filing system, installs the
  mandate-tracker workbook, initialises tracker.json, prompts for the NDA template,
  and schedules the recurring chaser and the round-1 process letter.
metadata:
  version: "0.2.0"
---

# Set up a new deal

Initialise everything needed to track one property sale. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. It defines the folder
structure, the `tracker.json` schema, the master workbook and the refresh routine
that every skill depends on. Follow it exactly.

## Steps

1. **Collect deal basics.** You need the property name/address, the agent's sending
   email account (the address that will send NDAs and bid requests), the intended
   round-1 process letter date, and the send mode. If any are missing, ask. Default
   send mode is `auto` (send without asking); confirm the user is comfortable with
   automatic sending and note they can switch any deal to `draft`.

2. **Create the filing system.** Inside the user's connected Cowork folder, create
   the deal folder (slug: lowercase, hyphens) and the full structure from the data
   model. **If a folder with that slug already exists, stop and confirm with the user
   before writing anything; never overwrite a live deal.** This filing system is
   aligned with the workbook tabs and the skills, so every document has an obvious
   home:
   - `00-mandate/` (onboard-mandate)
   - `01-dataroom/` with `title/`, `leases/`, `financial/`, `compliance/`,
     `planning/`, `management/`, `diligence/` (build-dataroom)
   - `02-marketing/` (teaser and IM)
   - `nda/` and `nda/signed/` (manage-ndas, review-inbox)
   - `03-buyers/` (qualify-buyer AML and proof-of-funds evidence)
   - `bids/` with `round-1/` and `round-2/` (request-bids, process-bids)
   - `04-legals/` (select-and-hot, track-legals)
   - `05-reporting/` (client-report)
   - an empty `correspondence-log.md`

3. **Install the mandate tracker and example documents.** Copy
   `${CLAUDE_PLUGIN_ROOT}/assets/mandate-tracker-template.xlsx` into the deal folder
   as `mandate-tracker.xlsx`. This is the master document for the mandate and is
   added to every project folder at this step. Also copy the bundled example
   documents into the deal so they form part of the project from day one:
   `${CLAUDE_PLUGIN_ROOT}/assets/NDA-template-EXAMPLE.md` into `nda/` and
   `${CLAUDE_PLUGIN_ROOT}/assets/HOT-template-EXAMPLE.md` into `04-legals/`. Both are
   clearly labelled placeholders for solicitor review; the agent replaces them with
   the firm's own wording when available.

4. **Write `tracker.json`** with the `deal` block populated from what you collected
   and empty `buyers`, `bids`, `dataroom`, `tasks`, `legals` and `reporting` arrays
   (the workbook seeds the standard checklists for the empty arrays). Then run
   `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>` so the
   installed workbook reflects the deal header, and generate `tracker-snapshot.md`.
   **Confirm the refresh completed with no formula errors before moving on; if it
   errors, fix the cause rather than leaving a broken workbook in the deal folder.**

5. **Capture mandate terms.** Offer to run `onboard-mandate` now to record the
   fee basis, sale structure, VAT position and vendor AML/KYC, and to file the
   signed mandate into `00-mandate/`. If the user declines, leave those fields blank
   for later.

6. **Handle the NDA template.** Check `nda/` for a template file.
   - If one is present, use it.
   - If not, tell the user to drop their NDA template into `nda/` (Word or PDF) and
     that until then you fall back to the generic UK NDA example copied into `nda/` in
     step 3 (`NDA-template-EXAMPLE.md`), clearly labelled as a placeholder for
     solicitor review. The example Heads of Terms (`04-legals/HOT-template-EXAMPLE.md`)
     is handled the same way by `select-and-hot`. Do not invent a binding legal
     document silently.

7. **Set up the recurring chaser.** Create a scheduled task that runs the
   `manage-ndas` chaser daily for this deal, so any buyer overdue by 2 or more days
   since their last NDA contact gets a polite chase. Confirm the task was created. If
   scheduling is unavailable, tell the user and note that chasers must be run manually.

8. **Schedule the round-1 process letter.** If the round-1 date is known, create a
   one-off scheduled task that fires `request-bids` for this deal on that date. If the
   date is undecided, skip the task and flag that it is pending a date; if scheduling
   is unavailable, tell the user it must be triggered manually.

9. **Offer the live dashboard.** Tell the user they can run `review-inbox` any time
   to scan email and refresh the live tracker dashboard, and offer to run it now.

## Output

Confirm in plain language: the deal folder and filing system created (list the
domain folders), that `mandate-tracker.xlsx` was installed, where to drop the NDA
template, the chaser schedule, and the date the process letter will go out.

## Completion checklist

The skill is done only when all of these are true:

- [ ] Confirmed the deal slug is new, no existing folder would be overwritten.
- [ ] Deal folder created with every domain folder: `00-mandate/`, `01-dataroom/`
      (+ `title/`, `leases/`, `financial/`, `compliance/`, `planning/`, `management/`,
      `diligence/`), `02-marketing/`, `nda/` + `nda/signed/`, `03-buyers/`,
      `bids/round-1/` + `bids/round-2/`, `04-legals/`, `05-reporting/`, and an empty
      `correspondence-log.md`.
- [ ] `mandate-tracker.xlsx` installed; `NDA-template-EXAMPLE.md` copied into `nda/`
      and `HOT-template-EXAMPLE.md` into `04-legals/`.
- [ ] `tracker.json` written with the `deal` block populated and `buyers`, `bids`,
      `dataroom`, `tasks`, `legals`, `reporting` arrays present (empty is fine).
- [ ] `refresh_tracker.py` ran and reported **no formula errors**; `tracker-snapshot.md`
      generated.
- [ ] NDA template located, or the user told where to drop it and which fallback applies.
- [ ] Daily NDA chaser scheduled (or the user told scheduling is unavailable and chasers
      are manual).
- [ ] Round-1 process letter scheduled for the agreed date (or flagged as pending a date).
- [ ] Closing summary delivered: folders, workbook, NDA drop location, chaser cadence,
      and process-letter date.
