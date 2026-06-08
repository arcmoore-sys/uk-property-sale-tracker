---
name: qualify-buyer
description: >
  This skill should be used to run AML/KYC and proof-of-funds checks on a
  prospective buyer once their NDA is signed and before they receive the process
  letter. Trigger when the user says "qualify [buyer]", "run buyer AML", "check
  proof of funds", "is [buyer] cleared to bid", or after a signed NDA comes back. It
  records the AML and proof-of-funds status per buyer and files evidence into
  03-buyers.
metadata:
  version: "0.1.0"
---

# Qualify a buyer

Gates a buyer between signed NDA and the process letter. A party should be cleared
on AML and proof of funds before being invited to bid. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first.

## Steps

1. **Identify the deal and buyer.** Load `tracker.json` and find the buyer record.
   Only qualify buyers with `nda_status: signed`. If the NDA is not signed, say so
   and point to `manage-ndas`.

2. **Run AML / KYC.** Prompt the user for the standard checks on the buyer entity
   and its beneficial owners, plus sanctions/PEP screening. Set `aml_status` to
   `clear` or `flagged` and note the date. File evidence into
   `03-buyers/<buyer-slug>/`.

3. **Verify proof of funds.** Confirm the funding position (equity, debt, fund
   allocation) and evidence (bank statement, fund confirmation, lender term sheet).
   Set `pof_status` to `verified` or `insufficient`. File evidence into the same
   buyer subfolder.

4. **Set the gate.** A buyer is qualified when `aml_status: clear` and
   `pof_status: verified`. Flag any buyer who is not yet qualified so they are not
   sent the process letter prematurely. `request-bids` should only include qualified
   parties in round 1.

5. **Update the workbook.** Write `tracker.json`, run
   `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`, and
   regenerate `tracker-snapshot.md`.

## Output

Report each buyer's AML and proof-of-funds status, who is now cleared to bid, and
anyone still outstanding. The Mandate Summary tab's "Buyers qualified" count updates
automatically.
