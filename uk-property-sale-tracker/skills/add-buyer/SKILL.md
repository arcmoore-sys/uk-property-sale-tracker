---
name: add-buyer
description: >
  This skill should be used to add a prospective buyer to a deal by filling out a
  short form. Trigger when the user says "add a buyer", "add buyer", "new buyer",
  "add a prospective buyer", "log a new interested party", "add [name] to the buyer
  list", or "register an enquiry". It presents a form with three fields, Buyer
  (contact name), Company, and Contact Email, pre-filled with suggestions mined
  from the deal's email correspondence, lets the user pick a suggestion or enter
  details manually, writes the buyer into tracker.json, refreshes the workbook, and
  hands off to manage-ndas.
metadata:
  version: "0.2.0"
---

# Add a buyer

Captures a new prospective buyer onto a deal's Buyer Pipeline. Read
`${CLAUDE_PLUGIN_ROOT}/shared/data-model.md` first. A buyer record uses the schema
in that file; this skill writes one new entry into `tracker.json.buyers` with the
form's three fields mapped as: **Buyer → `name`, Company → `company`, Contact Email
→ `email`**.

## Steps

1. **Identify the deal** and load its `tracker.json`. If the user named a property,
   use it; otherwise list the active deal folders and ask which one. Note the
   existing `buyers` so you can de-duplicate.

2. **Mine email for candidate buyers (suggestions).** If an email connector is
   available, search the agent's mailbox for messages about this deal (by property
   name/address from `deal.name`/`deal.address`, and within the recent window).
   From senders who are **not already** in `tracker.json.buyers` (match on email
   address, case-insensitive), extract candidate values:
   - **Buyer**: the sender's display/contact name, or a name in the signature.
   - **Company**: from the signature, sending domain, or message body.
   - **Contact Email**: the sender address.
   De-duplicate candidates and keep the most recent/complete version of each. If no
   connector is available or nothing relevant is found, skip silently and go straight
   to manual entry; never invent a buyer or an address.

3. **Present the add-buyer form.** Show an elicitation form titled "Buyer details"
   with the three fields. For each field, surface the mined candidates as selectable
   suggestions **and** allow free-text manual entry, so the user can either pick a
   detected enquiry or type their own. If several distinct people were detected,
   present them as pickable cards (name + company + email) at the top so one click
   fills all three fields, with the individual fields below for editing. If no
   candidates were found, present the three empty fields for manual entry and say the
   suggestions came up empty.

4. **Validate (lightly).** A **Buyer name** is the only hard requirement. Company
   and Contact Email are both optional, and the email is **not** validated for
   format: record whatever the user provides verbatim (or leave it empty). Never
   block a manual add because an email is missing or looks malformed. If a provided
   email exactly matches an existing buyer's (case-insensitive), flag it as a likely
   duplicate and ask whether to add anyway or open the existing buyer, but do not
   hard-stop. Only ask the user to supply a missing field when the **Buyer name**
   itself is blank.

5. **Write the buyer record.** Append one entry to `tracker.json.buyers`:
   - `name`, `company`, `email` from the form.
   - `slug`: lowercase-hyphen from company (or name if no company).
   - `enquiry_date`: today (or the enquiry email's date if sourced from one).
   - `nda_status: not_sent`, `nda_sent_date: ""`, `last_chase_date: ""`,
     `chase_count: 0`, `nda_signed_date: ""`.
   - `aml_status: pending`, `pof_status: pending`.
   - `bid_status_round_1/2/3: none`.
   - `notes`: record the source ("added from enquiry email dated …" or "added
     manually").

6. **Refresh the records.** Write `tracker.json`, run
   `python ${CLAUDE_PLUGIN_ROOT}/shared/refresh_tracker.py <deal-folder>`, and
   regenerate `tracker-snapshot.md`. Confirm the refresh completed with no formula
   errors. If sourced from an email, append a row to `correspondence-log.md`
   (type `buyer-added`).

7. **Hand off.** The new buyer has `nda_status: not_sent`, so offer to run
   `manage-ndas` to send their NDA (auto-send if the deal's `send_mode` is `auto`).

## Output

Confirm the buyer added (name, company, email), whether it came from a detected
enquiry or manual entry, that the Buyer Pipeline and "Buyers on list" count
refreshed, and offer to send the NDA via `manage-ndas`. Mention the user can run the
skill again to add another buyer.

## Completion checklist

The skill is done only when all of these are true:

- [ ] Deal identified and `tracker.json` loaded; existing buyers noted for de-duplication.
- [ ] Email mined for candidate buyers (or manual entry used because no connector /
      no matches); no buyer or email address invented.
- [ ] Form presented with the three fields (Buyer, Company, Contact Email), offering
      mined suggestions **and** manual entry.
- [ ] Buyer name present (the only hard requirement); Company and Contact Email
      optional and accepted as-typed without format validation; an exact-match
      duplicate email flagged for the user but not auto-blocked.
- [ ] One buyer record appended to `tracker.json.buyers` with the full schema:
      `nda_status: not_sent`, `aml_status: pending`, `pof_status: pending`,
      `chase_count: 0`, `bid_status_round_1/2/3: none`, a slug, an enquiry date, and a
      source note.
- [ ] `tracker.json` written; `refresh_tracker.py` ran with no formula errors;
      `tracker-snapshot.md` regenerated; `correspondence-log.md` updated if email-sourced.
- [ ] Confirmation delivered and `manage-ndas` offered to send the NDA.
