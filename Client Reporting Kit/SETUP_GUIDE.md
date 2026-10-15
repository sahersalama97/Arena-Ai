# Setup Guide — complete, in order, with the checks at each step

This is the single document to follow to get the whole system running. It covers
**your own install** (Part A), the **no-n8n path** (Part B), the **TikTok repair**
(Part C), and the **operating rhythm** afterwards (Part D).

Every step has a check. If a check fails, stop and fix it — don't continue and
debug three problems at once.

**Time:** Part A is about 90 minutes. Part B is 20. Part C is 30.

---

## Part A — Automated install (n8n)

### A0. Prerequisites — confirm before you start

| You need | Why | Check |
|---|---|---|
| An n8n instance you can edit | Runs WF4 and WF5 | You can open the workflow list |
| A Google account for the credentials | Sheets + Drive OAuth | — |
| A Brand Registry sheet | WF4 reads brands from it | It has the columns below |
| The four raw tabs being written by your pipeline | WF5 reads them | `Daily_Raw_Meta`, `Daily_Raw_TikTok`, `Daily_Raw_Meta_Ads`, `Daily_Raw_TikTok_Ads` |
| SMTP or Gmail credential | Failure alerts | — |

**If you don't have the four raw tabs, stop.** The kit is a reporting layer on top of a
data source. Part B works without n8n but still needs somewhere for the numbers to come
from — either a pipeline or you pasting them.

Registry columns (row 1):

```
A Brand_Name    B Platform    C Meta_Ad_Account_ID    D TikTok_Advertiser_ID
E Report_Email  F Raw_Sheet_ID  G Current_Month_Report_Sheet_ID
H Status        I Discovered_At J Kit_Sheet_ID   <-- YOU ADD THIS ONE
```

### A1. Add `Kit_Sheet_ID` to the registry — 2 min

Type `Kit_Sheet_ID` into **J1**. Leave the column below it empty; WF4 fills it.

**Why it's first:** WF4 creates a dashboard per brand and writes its ID to column J. WF5
then reads column J to know which sheet to fill. Without the header, WF4 provisions a
dashboard and has nowhere to record it, so WF5 can never find it — and you get an orphan
sheet with no obvious error.

✔ **Check:** J1 reads exactly `Kit_Sheet_ID`. No trailing space, no lowercase.

### A2. Fix `Report_Email` — 2 min

Every row currently holds `PASTE_YOUR_EMAIL@example.com`. WF4 **deliberately skips
sharing** while that placeholder is present — so dashboards will be created but not shared,
and nothing will tell you why.

Either put real client addresses in column E, or accept that sharing is off and do it by
hand. Don't leave it and wonder later.

✔ **Check:** for each brand you want provisioned, column E is either a real address or
you've decided sharing is manual.

### A3. Upload the dashboard template — 5 min

Upload `01_Google_Sheets_Reporting_Dashboard.xlsx` to Google Drive and let it convert to a
Google Sheet. Open it and copy the ID from the URL:

```
https://docs.google.com/spreadsheets/d/<THIS PART>/edit
```

This is `KIT_TEMPLATE_ID`. WF4 copies it once per brand, so **treat it as read-only** —
edit the template and every future client gets your edit; break it and every future client
gets the break.

✔ **Check:** you can open the ID in a browser and it shows 11 tabs — Start Here,
Fundamentals, Ad Data, KPI Calc, `_Control`, Dashboard, Meta Dashboard, TikTok Dashboard,
Ad Performance, Benchmarks, Health Check.

### A4. Set the eight constants — 10 min

They're at the top of `_build/build_n8n_workflows.py`:

| Constant | Set it to |
|---|---|
| `REGISTRY_ID` | Your registry sheet ID |
| `KIT_TEMPLATE_ID` | The ID from A3 |
| `OWNER_EMAIL` | Your inbox — gets failure alerts |
| `SHEETS` | Your Google Sheets OAuth credential `id` and `name` |
| `DRIVE` | Your Google Drive OAuth credential |
| `SMTP` | Your outbound email credential |
| `GMAIL` | Your Gmail OAuth — only if you import TikTok reports by email |
| `RAW_TABS` | Only if your upstream names the four tabs differently |

Credential IDs come from n8n → Credentials → open the credential → the ID is in the URL.

Then regenerate:

```bash
python3 "_build/build_n8n_workflows.py"
```

**Can't run Python?** Find-and-replace the old IDs directly in the two JSON files — they
appear verbatim. Afterwards confirm the node counts, because a bad find-and-replace can
quietly mangle JSON: **WF4 = 13 nodes, WF5 = 17 nodes.**

✔ **Check:** the two JSONs import into n8n without an error, and the node counts match.

### A5. Import WF4 and run it manually — 20 min

Import `n8n/WF4 Provision Client Reporting Kit.json`. **Do not activate it yet.**

Set a manual trigger and run it once. Watch the execution.

✔ **Checks, in order:**
1. It read the registry and filtered to `Status = active`
2. For one brand: a new spreadsheet was created in Drive, named for that brand
3. Its ID landed in **column J** of the registry
4. If column E held a real address, the sheet was shared with it

If a brand is silently skipped, it's almost always `Status` ≠ `active` — WF4 gates on it
and reports nothing.

### A6. Import WF5 and run it manually — 20 min

Import `n8n/WF5 Client Reporting Kit Nightly Refresh.json`. **Still not activated.**

Run it once.

✔ **Checks:**
1. Exactly **three** Sheets API calls per brand: one `values:batchGet`, one `values:clear`,
   one `values:batchUpdate`. Nothing else touches the sheet — that's deliberate, so a
   refresh cannot break a formula.
2. Open the dashboard WF4 just made. `_Control` rows 2–8 are populated:

   | Cell | Key | Should show |
   |---|---|---|
   | `B2` | `Current_Start` | First day of the reporting window |
   | `B3` | `Current_End` | Last day |
   | `B4` | `Compare_Start` | First day of the prior window |
   | `B5` | `Compare_End` | Last day of the prior window |
   | `B6` | `Brand_Name` | The brand |
   | `B7` | `Last_Refresh` | Today |
   | `B8` | `Rows_Synced` | A number greater than zero |

3. `Fundamentals` and `Ad Data` have rows.
4. **The platform tabs are actually separate.** Meta Dashboard shows only Meta; TikTok
   Dashboard only TikTok. Neither should equal the combined figure.

`Rows_Synced = 0` means the batchGet returned nothing — check `Raw_Sheet_ID` in the
registry for that brand.

### A7. Look at the numbers before you trust them — 15 min

This is the step people skip and then get surprised.

1. **`KPI Calc!J5/J6/J7`** — COGS %, other variable %, shipping per order. These are
   assumptions until the client confirms them, and **`KPI Calc!I4` shows red to say so**.
   Get real numbers; the whole breakeven-ROAS pitch rests on them.
2. **Health Check rows 17–29.** Rows 23–24 reconcile ad-level against account-level totals.
   If they read `CHECK`, that's a real gap in the data — not a broken sheet. Row 29 stays
   `CHECK` until you set `Benchmarks!B28` to `TUNED`.
3. **Benchmarks rows 7–21.** Columns C/D/E/F are Weak / Watch / Target / Strong. They ship
   as labelled placeholders. Replace them with the client's trailing 90 days, **per
   platform** — Meta and TikTok have very different CPM and frequency norms, so one shared
   threshold set is worse than none. Then set `B28` to `TUNED`.

### A8. Activate the schedules — 5 min

Only now. The order matters:

| Time | Workflow | Constraint |
|---|---|---|
| 05:00 | WF0 brand discovery | |
| 06:00 | WF1u Meta account-level | |
| 06:15 | WF1bu Meta ad-level | |
| 10:00 | WF_Provision brand sheets | |
| **10:30** | **WF4 kit provision** | must run *after* WF_Provision |
| 12:00 | WF2e TikTok import | |
| 13:00 | WF3 reports | |
| **14:00** | **WF5 kit refresh** | must run *after every data-collection workflow* |

Those are the only two ordering rules. If your pipeline runs at different times, keep WF4
after provisioning and WF5 after the last data write — the clock times are irrelevant.

✔ **Check:** the next morning, `Last_Refresh` in `_Control!B7` shows today's date on every
active brand.

---

## Part B — Manual install, no n8n (20 min)

For a single client, or before you're ready to run automation.

1. Copy `01_…xlsx` into Google Drive and open it as a Google Sheet. **Google Sheets only** —
   `IMPORTRANGE` does not exist in Excel, not even Excel 365.
2. On the **Start Here** tab there's one `LET` / `VSTACK` / `HSTACK` / `CHOOSECOLS` formula.
   Copy it.
3. Put your Raw Data sheet ID in **`Fundamentals!N1`**.
4. Paste the formula into **`Fundamentals!A2`**. It fills both platforms, labels included.
5. **Approve the IMPORTRANGE prompt.** Once. If you don't see the prompt, the formula reads
   `#REF!` — click the cell and look for the "Allow access" button.
6. Set the period in **`_Control!B2:B5`** (or `KPI Calc!B4/C4/B5/C5`, which read from it).
7. Set the brand name in **`_Control!B6`**.
8. Fill the cost inputs at **`KPI Calc!J5/J6/J7`**.

**Landing Page Views will be blank.** That's correct, not broken. Meta reports LPV only at
*ad* level (`Daily_Raw_Meta_Ads!N`), never account level, and TikTok doesn't report it at
all. Start Here has an `ARRAYFORMULA` + `SUMIF` snippet for `Fundamentals!G2` that sums Meta
LPV up by date. Note it wraps the criteria in `TEXT(...,"yyyy-mm-dd")` — `Daily_Raw_Meta_Ads`
stores dates as *text*, and `SUMIF` will not match a real date against text, so without the
wrapper it silently returns 0 and your click-to-landing-page rate reads 0.0%.

For the **client report**, open `02_…xlsx` → `_Inputs`. Fill the cover block (B5–B10), paste
your platform overviews into the Meta block (rows 22–33) and TikTok block (rows 38–50) and
Combined block (rows 13–18), then fill the six CONTEXT lines (54–60). Every other tab reads
from `_Inputs` — you never type a number twice.

---

## Part C — TikTok raw-sheet repair (30 min)

**Do this if you import TikTok by scheduled email.** Skip it if you don't — but read
`n8n/WF2e_FIX_TikTok_Raw_Integrity.md` anyway, because it explains a failure mode that will
otherwise cost you a client conversation.

The bug: `Daily_Raw_TikTok_Ads` accumulates duplicate `(Date, Ad_ID)` rows, and two Ad_IDs
have been stored as 16-digit *numbers*, which Google Sheets rounds to 15 significant digits
— destroying the last digit permanently.

**Order matters — clean first, then patch,** so you can see the row count drop:

1. **Clean the existing duplicates.** Helper column `=A2&"|"&TEXT(B2,"0")`, sort by it then
   by `Pulled_At` descending, delete the lower row of each duplicated pair, delete the
   helper. The `TEXT(...,"0")` stops a numeric Ad_ID rendering as `1.87E+15`.
2. **Set column B to Plain text.** Format → Number → Plain text. This doesn't replace the
   patch — n8n's `appendOrUpdate` coerces types regardless of cell format — but it stops
   manual pastes re-introducing it.
3. **Install the patch.** Copy the three nodes from
   `n8n/WF2e_PATCH_TikTok_Ads_Upsert.json` into WF2e, replacing
   `Upsert Daily_Raw_TikTok_Ads`:

   ```
   Explode ad rows → Read existing TikTok ad rows → Plan TikTok ad row writes
                   → Write TikTok ad rows → (where the old node went)
   ```

   Both HTTP nodes reference `$('Loop Brands Ads').first().json.Raw_Sheet_ID` and the same
   Sheets credential WF1bu uses.
4. **Run WF2e manually once.** The Code node returns four counters — `updated`, `appended`,
   `existing_duplicates`, `numeric_ids_repaired`. After step 1, `existing_duplicates` should
   be **0**. If it isn't, your cleanup missed some.
5. **Confirm your TikTok scheduled report sends CSV, not XLSX.** If the corrupted IDs came
   from an Excel attachment, Excel destroyed the 16th digit before n8n ever saw it, and
   `String(v)` cannot bring it back.

The two corrupted Ad_IDs are unrecoverable. Practical options: leave them (2 of ~30 ads, and
`Ad Performance` groups by ad *name*, not ID), or pull the real IDs from TikTok Ads Manager
and paste them into column B as text.

---

## Part D — Operating rhythm

**Every morning (30 seconds).** Open the dashboard. `_Control!B7` shows today. Glance at
Health Check. If a row flipped to `CHECK`, look at it before the client does.

**Every Monday (15 min).** Read Meta Dashboard and TikTok Dashboard **separately**. The
point of the split is that two platforms rarely fail for the same reason — a blended number
tells you to cut both when usually only one needs it. Run **prompt 3** (the weekly check-in)
from `05_AI_Prompts_Campaign_Performance.md`.

**Monthly, before you report (60–90 min).**
1. Confirm the cost inputs in `KPI Calc!J5:J7` are still right. If `I4` is red, breakeven is
   a guess — say so or fix it.
2. Read Health Check rows 17–29 end to end.
3. Fill the client report's `_Inputs` (or let WF5 do it) and run **prompt 1** for the
   narrative, **prompt 2** if ROAS moved, **prompt 12** for the platform split decision.
4. Export the PDF from `04_Monthly_Report_PDF_Template.pdf` and send it with the email
   **prompt 9** writes.
5. Run **prompt 11** — the self-audit — on your own account. It's the one that makes you
   better rather than faster.

**One rule that will save you.** Quote TikTok totals from `Fundamentals`, never from
`Ad Performance`. TikTok's ad-level export under-reports spend against its own account-level
total — 17.6% short on the reference account. `Ad Performance` is reliable for *ranking* ads
against each other, not for platform totals.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| WF4 creates sheets but column J stays empty | `Kit_Sheet_ID` header missing or misspelt | A1 |
| Dashboards created but not shared | `Report_Email` still `PASTE_YOUR_EMAIL` | A2 — by design, not a bug |
| A brand is skipped silently | `Status` isn't `active` | Registry column H |
| WF5 runs, dashboard empty, `Rows_Synced` = 0 | Wrong `Raw_Sheet_ID` for that brand | Registry column F |
| Everything is zero | Dates stored as **text**; date-bounded `SUMIFS` can't match | Wrap criteria in `TEXT(...,"yyyy-mm-dd")` |
| `#REF!` on Start Here | You pasted into one of the two documentation cells that hold example formulas as plain text | Don't paste there |
| Landing page views blank | Correct — TikTok has none, Meta only at ad level | Start Here's snippet |
| Health Check 23/24 read `CHECK` | Real ad-level vs account-level gap | Part C, and quote from `Fundamentals` |
| Duplicate rows in `Daily_Raw_TikTok_Ads` | Patch not installed | Part C |
| `KPI Calc!I4` is red | Cost inputs are assumed, not confirmed | A7 — get real numbers |
| Benchmarks row 29 always `CHECK` | Tuning flag still `PLACEHOLDER` | Set `B28` to `TUNED` |
| Bars in the funnel look empty | Expected for 1–2% steps; they're scaled to each step's own target | Not a bug |

---

## What "done" looks like

You're finished when all of these are true:

- [ ] Every active brand has a dashboard, and its ID is in registry column J
- [ ] `_Control!B2:B8` populated on each, `Last_Refresh` = today
- [ ] Meta Dashboard and TikTok Dashboard each show **only** their own platform
- [ ] Neither platform tab equals the combined figure
- [ ] `KPI Calc!I4` is **not** red — the cost inputs are confirmed, not assumed
- [ ] `Benchmarks!B28` reads `TUNED`
- [ ] Health Check rows 23/24 pass, or you know exactly why they don't and have written it down
- [ ] WF4 and WF5 have completed at least one **scheduled** run without you touching them
- [ ] `Daily_Raw_TikTok_Ads` has no duplicate `(Date, Ad_ID)` pairs

That last one is the acceptance test in the proposal. Get it confirmed in writing.
