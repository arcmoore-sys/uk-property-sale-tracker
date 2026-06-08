# UK Property Sale Tracker

A Cowork plugin that runs a UK property agent's sell-side mandate from instruction to
completion. It onboards the mandate, builds and chases the data room, keeps a live
buyer tracker plus a master Excel workbook, issues and chases NDAs, qualifies buyers,
runs multi-round bids with a round-over-round change log, selects the preferred bidder
and drafts Heads of Terms, tracks the legals through exchange and completion, and
produces client progress and closing reports.

## What it does

- **Mandate onboarding** - captures fee basis, sale structure, VAT position and key
  dates, runs vendor AML/KYC, and files the signed mandate.
- **Data room** - maintains an indexed document checklist, files documents into the
  numbered data-room subfolders, and flags gaps before launch.
- **Live buyer tracker + master workbook** - `tracker.json` is canonical; the
  `mandate-tracker.xlsx` workbook (and a markdown snapshot) are rendered from it via
  the shared refresh routine, so the workbook is accurate from day one.
- **NDA automation** - sends each new buyer the NDA from the deal folder, files signed
  copies, and chases non-responders every 2 days.
- **Buyer qualification** - runs AML/KYC and proof-of-funds checks before a buyer
  receives the process letter.
- **Process letter (request for bids)** - issues the call for offers to qualified
  parties for round 1 and again for a best-and-final round 2.
- **Bid logging + change log** - records each bid's key terms and shows exactly what
  each buyer changed between rounds, plus drop-outs and new entrants.
- **Preferred bidder + Heads of Terms** - records the selection, drafts HoT, sets
  exclusivity, and notifies unsuccessful bidders.
- **Legals to completion** - tracks the conveyancing milestones and completion
  checklist from instruction of solicitors through exchange and completion.
- **Client reporting** - generates and logs weekly progress reports, the closing
  report, and the fee invoice.
- **Deal Desk agent** - an orchestrator that reads the live tracker, tells you where
  the deal is and what is next, runs the inbox-to-pipeline loop, drafts buyer
  follow-up and chaser emails, and books meetings with buyers and the client at the
  relevant stages, stopping at the judgment gates for your approval.

## Components

| Type | Name | Purpose |
|---|---|---|
| Skill | `setup-deal` | Create the per-property folder/filing system, install the workbook, init the tracker, schedule the chaser and round-1 process letter |
| Skill | `onboard-mandate` | Record mandate commercial terms, run vendor AML/KYC, file the signed mandate |
| Skill | `build-dataroom` | Maintain the data-room checklist, file documents, flag missing items |
| Skill | `review-inbox` | Scan email, update the tracker, file signed NDAs/bids, refresh the workbook and live dashboard |
| Skill | `manage-ndas` | Send NDAs to new buyers and chase non-responders every 2 days |
| Skill | `qualify-buyer` | Run buyer AML/KYC and proof-of-funds checks before bidding |
| Skill | `request-bids` | Issue the process letter (request for bids) to qualified parties (round 1 or 2) |
| Skill | `process-bids` | Log bid terms to the Bid Log and build the round-over-round change log |
| Skill | `select-and-hot` | Select the preferred bidder, draft Heads of Terms, notify underbidders |
| Skill | `track-legals` | Track conveyancing from solicitor instruction through exchange and completion |
| Skill | `client-report` | Generate/log client progress reports, the closing report, and the fee invoice |
| Agent | `deal-desk` | Orchestrates the running mandate: status + next step, inbox-to-pipeline routing, drafts buyer emails, books buyer/client meetings, gates decisions |
| Asset | `assets/NDA-template-EXAMPLE.md`, `assets/HOT-template-EXAMPLE.md` | Example NDA and Heads of Terms copied into every deal folder as placeholders for solicitor review |
| Shared | `shared/data-model.md` | Folder structure, tracker schema, workbook tabs and write pattern all skills follow

## Connectors

Connect one **email** provider (Microsoft 365 / Outlook or Gmail) and one **calendar**
provider (Outlook Calendar or Google Calendar). Email reads the inbox and sends NDAs,
chasers, bid requests and client correspondence; calendar lets the Deal Desk agent book
buyer and client meetings. See `CONNECTORS.md` for details. Document storage is local to
your Cowork folder; scheduling and the live dashboard use built-in Cowork features.
