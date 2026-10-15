# Delivery Runbook

What you do after someone pays. One section per tier, then the intake form that all three
use. Every step names the actual file, tab or cell — no "configure as appropriate."

---

## Before anything: the eight constants a buyer must replace

The shipped `WF4` and `WF5` JSONs contain **your** sheet IDs and credential IDs. They will
not work in anyone else's n8n until these are changed. This is the single biggest install
friction point, so put it first in every Tier 2 and Tier 3 handover.

All eight live at the top of `_build/build_n8n_workflows.py`. Change them there and
regenerate (`python3 _build/build_n8n_workflows.py`) rather than hand-editing the JSON —
the generator is the source of truth and hand-edits get overwritten.

| Constant | What it is | Where they find theirs |
|---|---|---|
| `REGISTRY_ID` | Their Brand Registry spreadsheet | The URL of their registry sheet |
| `KIT_TEMPLATE_ID` | The dashboard that gets copied per client | They upload `01_…xlsx` to Drive, open it, copy the ID from the URL |
| `OWNER_EMAIL` | Who gets failure alerts | Their own inbox |
| `SHEETS` | Google Sheets OAuth credential id + name | n8n → Credentials → create → copy the ID from the URL |
| `DRIVE` | Google Drive OAuth credential | Same |
| `SMTP` | Outbound email credential | Same (or swap for `GMAIL`) |
| `GMAIL` | Gmail OAuth, only if they import TikTok reports by email | Same |
| `RAW_TABS` | The four raw tab names | Only changes if their upstream pipeline names tabs differently |

If a buyer can't run Python, they can find-and-replace the old IDs directly in the two JSON
files — the IDs appear verbatim. Tell them to check the node count afterwards (WF4 = 13
nodes, WF5 = 17) so they know nothing got mangled.

---

## Tier 1 — The Kit (self-serve)

**Your time: ~5 minutes per buyer, and zero if the FAQ does its job.**

1. Delivery is automatic through Gumroad / Lemon Squeezy: the six files plus `samples/`.
   Put `LICENCE.md` on the download page, not in an email — they'll read it there.
2. Send the welcome email. Four lines, no more:
   - Start at **`README.md` → "Quick start (20 minutes)"**.
   - The dashboard is **Google Sheets only**. `IMPORTRANGE` does not exist in Excel — if
     they're in Excel, say so now, before they blame the product.
   - Set their currency in one cell before entering data (README → *Customising*).
   - FAQ link. Support boundary: community + FAQ, no direct email.
3. Nothing else. Do not offer a call. If they want one, that's a Tier 3 conversation.

**What Tier 1 buyers ask first**, in order — all already answered in the repo:

| Question | Answer location |
|---|---|
| "How do I connect my data?" | README → manual path, the `LET`/`VSTACK`/`HSTACK` formula on the **Start Here** tab |
| "Why is everything zero?" | Their `Daily_Raw_Meta_Ads` dates are **text**. README → "Why TEXT() is in there" |
| "Landing page views are blank" | Correct. TikTok doesn't report LPV; Meta only at ad level. README → "Known limit, handled honestly" |
| "There's a `#REF!` on Start Here" | Two documentation cells hold example formulas as plain text on purpose. Don't paste into them |
| "Benchmarks say PLACEHOLDER" | By design. `Benchmarks!B28` ships `PLACEHOLDER`; they type `TUNED` once they've set their own |

---

## Tier 2 — Kit + Automation (they install, you support)

**Your time: 1–2 hours of email spread over their first week.**

Send, in this order:

1. **Everything in Tier 1**, plus the `n8n/` folder: `WF4…json`, `WF5…json`,
   `AUTOMATION_GUIDE.md`, the three `code_*.js` files, and `WF2e_FIX_TikTok_Raw_Integrity.md`
   + `WF2e_PATCH_TikTok_Ads_Upsert.json` if they import TikTok by email.
2. **The constants table above.** Lead with it.
3. **The prerequisite they will skip:** their Brand Registry needs a `Kit_Sheet_ID` column
   at **J1**. WF4 writes the new dashboard's ID there and WF5 reads it. Without it, WF4
   provisions a dashboard and then has nowhere to record it, so WF5 can never find it.
4. **The install order** — `AUTOMATION_GUIDE.md` has the detail, this is the shape:
   1. Replace the eight constants, regenerate or find-and-replace
   2. Upload `01_…xlsx` to Drive → copy its ID into `KIT_TEMPLATE_ID`
   3. Add `Kit_Sheet_ID` to registry **J1**
   4. Import WF4, run it **manually** on one test brand, confirm a dashboard appears and its
      ID lands in column J
   5. Import WF5, run it **manually**, confirm `Fundamentals` and `Ad Data` fill
   6. Only then set the schedules
5. **The schedule map.** WF5 must run *after* the raw data lands, or it reports yesterday:

   | Time | Workflow |
   |---|---|
   | 05:00 | WF0 brand auto-discovery |
   | 06:00 | WF1u Meta account-level |
   | 06:15 | WF1bu Meta ad-level |
   | 10:00 | WF_Provision brand sheets |
   | **10:30** | **WF4 — kit provision** |
   | 12:00 | WF2e TikTok import |
   | 13:00 | WF3 reports |
   | **14:00** | **WF5 — kit nightly refresh** |

   If their pipeline runs at different times, WF4 goes after their provisioning step and WF5
   after their last data-collection step. Those are the only two constraints.

**Set expectations honestly on the first email.** The workflow logic is unit-tested — the
ingest node was executed against a real client sheet and its output matched a delivered
workbook exactly, 28 fund rows and 387 ad rows. But nobody has watched these two workflows
run on a schedule for a month. Ask them to run steps 4 and 5 manually first and send you the
execution log if anything looks off. Buyers tolerate "supervised first run" far better than
discovering it themselves.

---

## Tier 3 — Done for you (you install)

**Your time: 6–10 hours across two weeks. Cap yourself at 3–4 concurrent installs.**

### Kickoff call — 60 min

- Walk their pipeline. Confirm the four raw tabs exist and are named as in `RAW_TABS`.
  If they aren't, that's a `RAW_TABS` change, not a rebuild.
- Collect the intake form (§ below). **Do not proceed without cost inputs** — breakeven
  ROAS is the product's headline feature and it's meaningless without them.
- Agree the two onboarding brands. Pick one Meta-heavy and one TikTok-heavy so both
  platform dashboards get exercised.
- Get access per `08` §4. They create every credential; you never receive a token.

### Install — days 2–4

1. **Registry.** Add `Kit_Sheet_ID` at **J1**. Check `Status` = `active` on the rows they
   want provisioned — WF4 gates on it and silently skips anything else.
2. **`Report_Email`.** The shipped registry has `PASTE_YOUR_EMAIL@example.com` on every row.
   WF4 **deliberately skips sharing** while that placeholder is present. Either set real
   addresses or tell them the dashboard won't be shared until they do.
3. **Template.** Upload `01_…xlsx` to their Drive, copy the ID into `KIT_TEMPLATE_ID`.
4. **Constants.** All eight, per the table above. Regenerate. Verify node counts
   (WF4 = 13, WF5 = 17) and that the connection graph has no unreachable nodes.
5. **Import WF4.** Run manually on one brand. Confirm: a dashboard was created, its ID is in
   column J, and — if a real email was set — it was shared.
6. **Import WF5.** Run manually. Confirm three Sheets API calls per brand and nothing else.
   Then open the dashboard and check `_Control` rows 2–8 populated: `Current_Start`,
   `Current_End`, `Compare_Start`, `Compare_End`, `Brand_Name`, `Last_Refresh`, `Rows_Synced`.

### Onboard two clients — days 5–7

For each brand:

1. **Cost inputs.** `KPI Calc!J5` COGS %, `J6` other variable %, `J7` shipping per order.
   These feed contribution margin → breakeven ROAS → POAS. Until they're real,
   **`KPI Calc!I4` shows red** and the breakeven is labelled an estimate. Leave it red if
   the client hasn't confirmed — that's the feature working, not a bug.
2. **Period.** `_Control!B2:B5`, or `KPI Calc!B4/C4/B5/C5` which read from it with text-date
   coercion. WF5 sets these automatically from the data; only touch them for a manual or
   custom window.
3. **Brand name.** `_Control!B6`.
4. **Verify the split.** Meta Dashboard and TikTok Dashboard must each show *only* their own
   platform. Sanity check: the Combined tab's total spend should equal Meta + TikTok, and
   neither platform tab should ever equal the combined figure.
5. **Health Check.** Read rows 17–29. Rows 23–24 reconcile ad-level against account-level;
   if they read `CHECK`, that's a real gap in their data — explain it in writing, don't hide
   it. Row 29 stays `CHECK` until `Benchmarks!B28` says `TUNED`.
6. **First nightly cycle, on a call.** Watch the execution log together. This is deliverable
   5 in the proposal and it's the one you must not skip.

### Tune and hand over — days 8–14

1. **Benchmarks.** Rows 7–21; columns C/D/E/F are Weak / Watch / Target / Strong. Replace
   placeholders with their trailing 90-day data, **per platform** — Meta and TikTok have
   very different CPM and frequency norms and one shared threshold set is worse than none.
   Then set `B28` to `TUNED`.
2. **Integrity review.** Deliver in writing: does ad-level reconcile to account-level on both
   platforms, what Health Check flagged, and what you recommend about each flag.
3. **WF2e patch**, if they import TikTok by email. `n8n/WF2e_FIX_TikTok_Raw_Integrity.md`
   has the wiring, the evidence and the one-off cleanup of rows already duplicated. Do the
   cleanup **before** installing the patch so they can see the row count drop.
4. **Walkthrough.** 90 minutes, recorded, theirs to keep. Cover: changing the period, adding
   a brand, what Health Check means, and the rule *"quote TikTok totals from Fundamentals,
   never from Ad Performance."*
5. **Revoke your access.** Confirm in writing that no copy of client data is retained.

### Acceptance test

Both onboarded clients produce a correct dashboard on a **scheduled** nightly run. Get that
confirmed in writing — it's the acceptance criterion in `08` §9 and it's objectively
checkable, which protects you both.

---

## Buyer intake form

Send this with the proposal. It collects everything §4 of `08` asks for, in one pass, and
it pre-qualifies: a buyer who can't answer section 3 isn't ready for breakeven ROAS and
should be told so before they pay.

```
=== REPORTING SYSTEM INTAKE ===

1. ABOUT YOU
   Business name:
   Country / billing currency:
   How many clients do you report on?
   Which platforms?            [ ] Meta  [ ] TikTok  [ ] Google  [ ] other:
   Do you run n8n today?        [ ] yes, self-hosted  [ ] yes, cloud  [ ] no
   Who maintains it?

2. DATA SOURCES (per brand - duplicate this block)
   Brand name:
   Meta ad account ID:
   TikTok advertiser ID:
   Where does your data land today?
       [ ] a Google Sheet I fill manually
       [ ] an n8n pipeline writing raw tabs
       [ ] a third-party tool (which?):
       [ ] nowhere yet
   If n8n: what are your raw tab names?
       account-level Meta:      (default: Daily_Raw_Meta)
       account-level TikTok:    (default: Daily_Raw_TikTok)
       ad-level Meta:           (default: Daily_Raw_Meta_Ads)
       ad-level TikTok:         (default: Daily_Raw_TikTok_Ads)
   If TikTok arrives by scheduled email: is the attachment CSV, XLS or XLSX?
       (CSV strongly preferred - XLSX destroys 16-digit ad IDs before import)

3. COST STRUCTURE (per brand - this is the part most buyers skip)
   COGS as % of revenue:
   Other variable costs as % of revenue (payment fees, returns, packaging):
   Average shipping cost per order:
   Average order value (last 90 days):
   Are these confirmed by the client, or your estimate?
       [ ] confirmed   [ ] my estimate
   Contribution margin % (if you already know it):
   Target ROAS the client has agreed to (if any):

4. HISTORY
   Do you have trailing 90 days of results per platform?  [ ] yes  [ ] no
   Best month so far and why you think it happened:
   Worst month so far and what you told the client:
   Has a client ever disputed a number you reported?      [ ] yes  [ ] no
       (if yes, what was it? - this usually tells me what to instrument first)

5. REPORTING
   How do you report today, and how long does it take per client per month?
   Who reads the report at the client, and what do they ask about?
   Do you already send a PDF, or a spreadsheet link, or both?
   What language should client-facing text be in?  [ ] EN  [ ] AR  [ ] both

6. ACCESS
   Preferred install window:
   Named contact for data questions (same-day for two weeks):
   Will you sign our data clause / your own DPA?   [ ] ours  [ ] yours  [ ] neither needed

=== END INTAKE ===
```

**Two answers that change what you sell:**

- Section 2 = *"nowhere yet"* → they need the upstream pipeline first. That's a separate
  project. Scope it separately or sell Tier 1 and revisit. Do not take a Tier 3 install fee
  for a system with nothing to read.
- Section 3 = *"my estimate"* on every line → breakeven ROAS will be a guess, and `KPI
  Calc!I4` will show red for good reason. That's still useful — it forces the conversation
  with their client — but tell them before they pay, and offer to help them get the real
  numbers as part of the kickoff call.

---

## If something breaks after handover

| Symptom | First thing to check |
|---|---|
| WF5 runs but the dashboard is empty | `_Control!B7` (`Rows_Synced`). Zero means the batchGet returned nothing — wrong `Raw_Sheet_ID` in the registry |
| Dashboard filled but all metrics zero | Dates stored as **text**. Check `Daily_Raw_Meta_Ads` column A type |
| One brand fails, others fine | That brand's `Status` isn't `active`, or `Kit_Sheet_ID` is blank in column J |
| Dashboards not being shared | `Report_Email` still contains `PASTE_YOUR_EMAIL` — WF4 skips sharing on purpose |
| TikTok totals look ~20% low in Ad Performance | Expected. Quote from `Fundamentals`. Then read the WF2e integrity doc |
| Duplicate rows in `Daily_Raw_TikTok_Ads` | The WF2e patch isn't installed. Install it, then run the one-off cleanup |
| Health Check rows 23/24 say CHECK | Working as designed — a real ad-level vs account-level gap |
| Breakeven ROAS looks wrong and `KPI Calc!I4` is red | The cost inputs are assumed, not confirmed. That's the flag doing its job |
