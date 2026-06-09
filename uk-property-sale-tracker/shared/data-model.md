# Data model (v0.2.0)

This file is the single source of truth for the plugin. Every skill reads it
first. v0.2.0 supersedes v0.1.0: it keeps the existing `tracker.json` field names
and the `nda/` and `bids/` folder conventions, and adds the master workbook, the
numbered domain folders, and the new state blocks used by the onboarding,
data room, qualification, Heads of Terms, legals and reporting skills.

## Two records, one authoritative

1. **`tracker.json` is canonical.** All skills read and write state here. It is
   structured, robust to parse, and never depends on reading back from Excel.
2. **`mandate-tracker.xlsx` is the master human-facing document.** It is the firm's
   styled template (`assets/mandate-tracker-template.xlsx`) copied verbatim into the
   deal folder at setup and then populated from `tracker.json`, never hand-parsed by
   a skill. After any skill changes `tracker.json` it calls the shared refresh
   routine, which writes the live values into the existing workbook IN PLACE,
   preserving the template's formatting, formulas, dropdowns and layout. The workbook
   is never rebuilt from code, so the template is the single source of styling: edit
   it and every future deal inherits the new look.
3. `tracker-snapshot.md` remains a lightweight markdown mirror for quick reading.

So the write pattern for every skill is: update `tracker.json`, then run
`python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`, then
regenerate `tracker-snapshot.md`.

## Folder structure (the filing system)

`setup-deal` creates this for every mandate. The numbered domain folders map one to
one onto the workbook tabs and the skills that own them, so a file always has an
obvious home.

```
<deal-slug>/
  mandate-tracker.xlsx        master workbook (rendered from tracker.json)
  tracker.json                canonical state
  tracker-snapshot.md         markdown mirror
  correspondence-log.md       running log of every message acted on
  00-mandate/                 onboard-mandate: signed mandate, fee agreement, vendor AML/KYC
  01-dataroom/                build-dataroom: the indexed data room
    title/
    leases/
    financial/
    compliance/
    planning/
    management/
    diligence/
  02-marketing/               teaser, Information Memorandum, buyer list
  nda/                        NDA template (existing convention)
    signed/                   signed NDAs, one per buyer (existing convention)
  03-buyers/                  qualify-buyer: per-buyer AML/KYC and proof-of-funds evidence
  bids/                       (existing convention)
    round-1/
    round-2/
  04-legals/                  track-legals: Heads of Terms, contract pack, replies, searches
  05-reporting/               client-report: sent client reports, closing report, fee invoice
```

Folder-to-tab-to-skill map:

| Folder        | Workbook tab            | Owning skill        |
|---------------|-------------------------|---------------------|
| 00-mandate    | Mandate Summary         | onboard-mandate     |
| 01-dataroom   | Information & Data Room | build-dataroom      |
| 02-marketing  | (Task Checklist)        | manual / review-inbox |
| nda, nda/signed | Buyer Pipeline        | manage-ndas, review-inbox |
| 03-buyers     | Buyer Pipeline          | qualify-buyer       |
| bids/round-N  | Bid Log                 | request-bids, process-bids |
| 04-legals     | Legal & Completion      | select-and-hot, track-legals |
| 05-reporting  | Client Reporting        | client-report       |

## tracker.json schema

```json
{
  "deal": {
    "name": "", "slug": "", "address": "", "sector": "", "tenure": "",
    "client": "", "mandate_ref": "",
    "sale_structure": "", "vat_position": "",
    "mandate_type": "", "instruction_date": "",
    "agent": "", "agent_email": "", "fee_basis": "", "abort_fee": "",
    "process_type": "", "send_mode": "auto",
    "quoting_price": "", "target_niy": "",
    "launch_date": "",
    "bid_request_date_round_1": "", "bid_request_date_round_2": "",
    "preferred_bidder_date": "", "hot_date": "",
    "target_exchange": "", "target_completion": "", "actual_completion": "",
    "current_round": 0, "current_stage": ""
  },
  "buyers": [
    {
      "name": "", "company": "", "email": "", "slug": "", "enquiry_date": "",
      "nda_status": "not_sent", "nda_sent_date": "", "last_chase_date": "",
      "chase_count": 0, "nda_signed_date": "",
      "aml_status": "pending", "pof_status": "pending",
      "bid_status_round_1": "none", "bid_status_round_2": "none", "bid_status_round_3": "none",
      "notes": ""
    }
  ],
  "bids": [
    {
      "buyer": "", "round": 1, "offer_price": 0, "niy": 0, "deposit_pct": 0,
      "funding_type": "", "pof": "", "conditions": "", "completion": "",
      "exclusivity": "No", "solicitor": "", "date_received": "", "notes": ""
    }
  ],
  "dataroom": [
    { "category": "", "document": "", "received": "No", "in_dataroom": "No", "date": "", "notes": "" }
  ],
  "tasks": [
    { "phase": "", "task": "", "owner": "", "status": "Not started", "due": "", "done": "", "automated_by": "" }
  ],
  "legals": [
    { "milestone": "", "responsible": "", "status": "Not started", "target_date": "", "actual_date": "", "notes": "" }
  ],
  "reporting": [
    { "date": "", "type": "", "period": "", "sent_to": "", "method": "", "notes": "" }
  ],
  "preferred_bidder": {
    "buyer": "", "price": 0, "exclusivity_until": "", "hot_status": "", "notes": ""
  }
}
```

### Controlled values

- `nda_status`: `not_sent` | `sent` | `signed`
- `aml_status`: `pending` | `clear` | `flagged`
- `pof_status`: `pending` | `verified` | `insufficient`
- `bid_status_round_N`: `none` | `requested` | `received` | `declined` (N is 1, 2 or 3)
- `send_mode`: `auto` | `draft`
- task / legal `status`: `Not started` | `In progress` | `Complete` | `N/A` | `Blocked`

The refresh routine maps these to the workbook's title-case display values
(for example `signed` becomes `Signed`, `clear` becomes `Clear`).

## Seed lists

The standard checklists for the Task Checklist, Information & Data Room and Legal &
Completion tabs live in the template workbook itself, so a freshly copied workbook is
useful from day one even when those `tracker.json` arrays are empty. Skills overlay
real values onto these seeded rows by matching on `task`, `document` or `milestone`;
rows with no match are appended below the seeded band with the template's row styling
carried down.

## The refresh routine

`shared/refresh_tracker.py <deal-folder>` reads `<deal-folder>/tracker.json` and
**populates the existing `mandate-tracker.xlsx` in place**: it opens the workbook
that was copied verbatim from `assets/mandate-tracker-template.xlsx` at setup (copying
the template first if it is somehow missing), writes each state block into its tab by
fixed position (Mandate Summary key/values, the buyer, bid, reporting bands) or by
matching the seeded key cells (tasks, data room, legals), recalculates with the xlsx
skill's `recalc.py`, and leaves all template formatting, the live summary formulas and
the dropdowns untouched. It never regenerates the workbook from code, so the template
is the single source of styling. Skills must call it after writing `tracker.json`, and
must never edit the workbook cell by cell themselves.

## Bid Log is a three-round comparison matrix

From v0.2.0 bids live in `tracker.json.bids` (one record per buyer per round, with
`round` in {1, 2, 3}) and render to the master workbook's **Bid Log** tab. The tab
is not a flat transaction log: the refresh routine pivots the bids into one row per
bidder, with price and net initial yield shown side by side for rounds 1, 2 and 3,
formula-driven price deltas for each transition (round 1 to 2, round 2 to 3), a
latest-offer column, a movement flag (Improved / Held / Reduced / Withdrawn /
New entrant) derived against `deal.current_round`, and the latest round's
conditions, completion and funding. Rows are ranked by latest offer, the leader is
highlighted, and the tab carries a title and subtitle block so the agent can select
it and paste a clean comparison straight into a client report between rounds.

`process-bids` writes terms into `tracker.json.bids` for the relevant round (and
still files the raw bid document under `bids/round-N/`) rather than maintaining a
separate `bid-log.xlsx`. Its round comparison reads from `tracker.json.bids` and
covers each transition up to three rounds.
