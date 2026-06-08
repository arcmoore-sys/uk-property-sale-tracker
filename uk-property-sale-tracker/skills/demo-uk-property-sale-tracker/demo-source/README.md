# demo-source, the dummy inbox + staging engine

This folder powers the `demo-uk-property-sale-tracker` run skill. It is a self-contained
demo of a fictional UK industrial deal, **Quantum 245, Tamworth** (single-let logistics,
vendor Helix Real Estate Partners, tenant GXO Logistics), driven from instruction to
completion. Everything here is invented and every document is a clearly-labelled placeholder.

## What's inside

| Path | Purpose |
|---|---|
| `_inbox/` | The **dummy inbound feed**, documents that "arrive" during a live mandate and only get pulled into the deal folder when the skill runs. Grouped by stage: `00-mandate`, `01-dataroom`, `02-enquiries`, `03-signed-ndas`, `04-qualification`, `05-bids-round-1`, `06-bids-round-2`, `07-legals`. |
| `_produced/` | **Agent-produced outputs** filed during the run: teaser, IM and buyer list (`02-marketing`), the two process letters (`bids`), Heads of Terms + exclusivity (`04-legals`), and the client reports + fee invoice (`05-reporting`). |
| `demo-script.json` | The **14-stage plan**: per-stage narration, which `_inbox` / `_produced` documents to pull, the simulated schedules, and the tracker patch that stage applies. |
| `apply_stage.py` | The **staging engine**. Applies one stage to a live deal folder: pulls that stage's files, merges its tracker patch into `tracker.json`, runs the plugin's `refresh_tracker.py`, updates the snapshot and correspondence log, and prints a JSON summary. |

## Running it directly (outside the skill)

```bash
export CLAUDE_PLUGIN_ROOT="<path-to>/uk-property-sale-tracker"   # the folder with shared/ and assets/
cd "$CLAUDE_PLUGIN_ROOT/skills/demo-uk-property-sale-tracker/demo-source"

python apply_stage.py --list                       # list the 14 stage ids
python apply_stage.py /path/to/quantum-DEMO 00-setup   # run one stage
python apply_stage.py /path/to/quantum-DEMO all        # run the whole deal to completion
```

The normal entry point is the skill itself ("run the demo"), which advances one stage at a
time and pauses with a recap after each. The `all` mode is for testing or an unattended
full run.

## The story (what the workbook ends up showing)

Six buyers enquire; five sign NDAs and qualify (Barings never returns its NDA and drops
out); five round-1 offers (£52.0m–£54.5m); four best-and-final (abrdn withdraws);
**Prologis UK wins at £57.6m unconditional** (4.7% above the £55.0m quoting price); exchange
and completion on 5 June 2026; closing report and fee invoice (£576,000 + VAT) issued.

## Notes

- **Nothing here is created for real.** The schedules in `00-setup` are *shown*, not
  created; no email is sent; no document is a binding instrument.
- Re-running against the same deal folder **resets it**, that is expected.
- `tracker.json` is canonical; `mandate-tracker.xlsx` and `tracker-snapshot.md` are rendered
  views. The engine never hand-edits the workbook.
