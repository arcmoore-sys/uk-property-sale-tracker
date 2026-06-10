---
name: re-sales-onboard-mandate
description: >
  This skill should be used to capture the commercial terms of a new sale mandate
  and run vendor onboarding. Trigger when the user says "onboard the mandate",
  "record the mandate terms", "set up the fee", "log the instruction", "run vendor
  AML", "we have been instructed on [address]", or right after setup-deal. It writes
  the fee basis, sale structure, VAT position and key dates into the tracker, runs
  the vendor AML/KYC prompts, and files the signed mandate into 00-mandate.
metadata:
  version: "0.1.0"
---

# Onboard the mandate

Front of the pipeline. Records what the agent has agreed with the client and
completes vendor onboarding before marketing starts. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first.

## Steps

1. **Identify the deal** and load its `tracker.json`. If no deal folder exists yet,
   run `setup-deal` first.

2. **Capture mandate terms** into the `deal` block. Confirm with the user, do not
   guess: mandate type (sole, joint, multiple), instruction date, fee basis and any
   abort fee, sale structure (asset vs share/SPV sale), VAT position (option to tax,
   TOGC eligibility), process type (private treaty, informal or formal tender,
   auction), quoting price, target net initial yield, and the key dates (launch,
   target exchange, target completion). Where the client has not decided a term,
   record it as blank rather than inventing it. Flag VAT and TOGC as items the
   client's accountant should confirm.

3. **Run vendor AML / KYC.** Identify the legal seller and any beneficial owners.
   Prompt the user for the standard checks (entity verification, beneficial owners,
   source of funds for the transaction, sanctions/PEP screening) and record the
   outcome and date. File evidence into `00-mandate/`. If anything is unresolved,
   note it as outstanding and do not mark the mandate ready to launch.

4. **File the signed mandate** and fee agreement into `00-mandate/` when supplied.

5. **Update the workbook.** Write the changes to `tracker.json`, mark the relevant
   phase 1 rows of `tasks` as `Complete` or `In progress`, then run
   `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>` and
   regenerate `tracker-snapshot.md`. Confirm the refresh completed with no formula
   errors.

## Output

Summarise the mandate terms captured, the vendor AML/KYC status, and anything still
outstanding before launch. Offer to run `build-dataroom` next.

## Completion checklist

The skill is done only when all of these are true:

- [ ] Deal identified and `tracker.json` loaded (`setup-deal` run first if no folder existed).
- [ ] Mandate terms captured into the `deal` block: `mandate_type`, `instruction_date`,
      `fee_basis`, `abort_fee`, `sale_structure`, `vat_position`, `process_type`,
      `quoting_price`, `target_niy`, `launch_date`, `target_exchange`, `target_completion`
      with undecided terms left blank (not invented), VAT/TOGC flagged for the accountant.
- [ ] Vendor AML/KYC run (entity verification, beneficial owners, source of funds,
      sanctions/PEP); outcome and date recorded; evidence filed in `00-mandate/`.
- [ ] Any unresolved AML/KYC item noted as outstanding and the mandate **not** marked
      ready to launch.
- [ ] Signed mandate and fee agreement filed in `00-mandate/` when supplied.
- [ ] Phase-1 `tasks` rows updated; `tracker.json` written; `refresh_tracker.py` ran with
      no formula errors; `tracker-snapshot.md` regenerated.
- [ ] Summary delivered covering terms, AML/KYC status, and what is outstanding before
      launch; `build-dataroom` offered.
