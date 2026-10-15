# Automating the Client Reporting Kit with n8n

Two workflows. **WF4** gives each client its own dashboard, once. **WF5** fills
every dashboard from the raw sheets, every night, with no pasting.

```
WF4 Provision Client Reporting Kit.json          run once per brand (also daily, 10:30)
WF5 Client Reporting Kit Nightly Refresh.json    every night, 14:00
code_flatten_to_kit_shape.js                     the WF5 transform, kept as a file so you can read it
code_summarise_run.js                            the WF5 summary email, same reason
```

The two `.js` files are not separate steps — they are the exact source of the two
Code nodes inside WF5, kept outside the JSON so they can be read, diffed and
tested. `python3 _build/build_n8n_workflows.py` rebuilds the JSON from them.

---

## Where they sit in your existing schedule

Nothing here competes with what already runs. WF4 and WF5 slot in after the
workflows they depend on:

| Time | Workflow | What it does |
|---|---|---|
| 05:00 | WF0 Brand Auto-Discovery | finds new ad accounts, adds them to the registry |
| 06:00 | WF1u Meta Account-Level Sync | writes `Daily_Raw_Meta` |
| 06:15 | WF1bu Meta Ad-Level Sync | writes `Daily_Raw_Meta_Ads` |
| **10:00** | WF_Provision Brand Sheets | creates each brand's Raw + monthly report sheets |
| **10:30** | **WF4 Provision Client Reporting Kit** | **creates each brand's dashboard** |
| 12:00 | WF2e TikTok Email Import | writes `Daily_Raw_TikTok`, `Daily_Raw_TikTok_Ads` |
| 13:00 | WF3 Ads Reports | monthly/weekly client report sheets |
| **14:00** | **WF5 Kit Nightly Refresh** | **fills every dashboard from the raw sheets** |

WF4 runs at 10:30 because it needs `Raw_Sheet_ID`, which WF_Provision writes at
10:00. WF5 runs at 14:00 because it needs TikTok's ad-level rows, which only
arrive with the 12:00 email import. Move WF5 earlier and TikTok will be missing
from every dashboard.

---

## Setup — seven steps, about ten minutes

### 1. Add one column to the Brand Registry

Open the registry (`1ytFhXwRpANDR5HB1NnKFcmeQspVZ-Ves3h03dsFq4xU`, tab
`Sheet1`) and in the first empty header cell — column J — type exactly:

```
Kit_Sheet_ID
```

Spelling and capitalisation matter; both workflows match on that string. Leave
the cells below it empty. WF4 fills them in.

### 2. Import WF4

n8n → **Workflows** → **⋯** → **Import from File** →
`WF4 Provision Client Reporting Kit.json`.

The credentials are already referenced by name and ID, matching your other
workflows: *Ai Saher Google Sheets*, *Ai Saher Google Drive*, *Report Email
SMTP*, *n8n Gmail TikTok Reports*. If your n8n is a different install, open each
node and re-pick the credential.

### 3. Check the template ID

WF4's **Copy kit template** node points at:

```
1TQax9tFM_cFk8c15Mt60xPcJj3TGqh0ZSP68i1Z6dX4
```

That is `TEMPLATE - Client Reporting Dashboard (Meta + TikTok)` in your Drive. If
you ever move, rename or re-upload that file, update this node — otherwise every
copy fails and you get an email saying so.

### 4. Run WF4 once by hand

Click **Execute Workflow**. It copies the template once per active brand that has
a `Raw_Sheet_ID` and no `Kit_Sheet_ID`, names it
`<Brand> - Reporting Dashboard (LIVE)`, writes the new ID back to the registry,
and shares it with the brand's `Report_Email`.

Re-running is safe: the filter skips any brand that already has a
`Kit_Sheet_ID`, so it will never create a second dashboard for the same client or
overwrite edits you made to their Benchmarks or business inputs.

> **One thing it will not do yet.** All twelve registry rows still hold
> `Report_Email = PASTE_YOUR_EMAIL@example.com`. WF4 detects that placeholder and
> skips the share step rather than failing twelve times. Put real addresses in
> and the sharing starts working on the next run.

### 5. Import WF5 and run it by hand

Same import. **Execute Workflow** once and watch the summary email land. First
run against a real brand is the moment to check three things:

- the dashboard's `_Control` tab shows today's timestamp in `Last_Refresh`;
- `Fundamentals` and `Ad Data` hold rows, not the sample data;
- the **Health Check** tab is mostly green.

### 6. Turn both on

Flip each workflow to **Active**. From then on WF4 picks up new clients at 10:30
and WF5 refreshes everyone at 14:00.

### 7. Fill in the business inputs — once per client

The automation writes data. It cannot know a client's margins. In each dashboard
open **KPI Calc** and set:

| Cell | What it is |
|---|---|
| `J5` | COGS % |
| `J6` | other variable cost % (fees, returns) |
| `J7` | shipping cost per order |

Until you do, every profit number is an estimate and the kit says so in red at
`KPI Calc!I4`. Breakeven ROAS, POAS and the scale/maintain/cut verdicts all
depend on these three cells.

---

## How the refresh actually works

Per brand, WF5 makes **three** Google Sheets API calls. That is deliberate — the
obvious design (read four tabs, write two) needs six or more, and twelve brands
would start bumping Google's per-minute limits.

**1 · Read everything at once.** One `values:batchGet` returns all four raw tabs
in a single response:

```
GET /v4/spreadsheets/{Raw_Sheet_ID}/values:batchGet
    ?ranges='Daily_Raw_Meta'!A:Z
    &ranges='Daily_Raw_TikTok'!A:Z
    &ranges='Daily_Raw_Meta_Ads'!A:Z
    &ranges='Daily_Raw_TikTok_Ads'!A:Z
    &valueRenderOption=UNFORMATTED_VALUE
    &dateTimeRenderOption=SERIAL_NUMBER
```

**2 · Flatten.** The `Flatten to kit shape` Code node turns those four tabs into
the two shapes the kit reads — `Fundamentals` (11 columns, account level) and
`Ad Data` (11 columns, ad level) — and decides which two periods to compare.

**3 · Clear, then write.** One `values:clear` wipes `Fundamentals!A2:K6000` and
`Ad Data!A2:K6000`; one `values:batchUpdate` writes both tabs plus `_Control`.

Everything else in the dashboard is a formula. Nothing else is touched, so a
refresh can't break a calculation, and any edit you made to Benchmarks, business
inputs or commentary survives it.

### Five decisions in the flatten step worth knowing about

**Columns are matched by header name, not position.** The node looks for
`Purchases_Value`, `AdSet_Name`, `AdGroup_Name` and so on. If a raw template ever
gains or reorders a column the kit keeps working. Positional mapping — which is
what the old build used — fails silently: it fills the wrong metric and nothing
looks wrong.

**Dates are written as serial numbers, not text.** The write uses
`valueInputOption: RAW`, which preserves JSON types, so a number lands in the
pre-formatted date column as a real date. An ISO string would land as *text* and
silently zero every date-bounded `SUMIFS` in the kit. This is not hypothetical:
`Daily_Raw_Meta_Ads` already has text dates, because WF1bu writes it with `RAW`
and ISO strings. `USER_ENTERED` would parse dates correctly but would also
reinterpret an ad named `50% off` as `0.5`, so serials are the safer fix.

**Meta's landing page views are summed up from ad level.** Meta reports LPV only
per ad, never per account, and TikTok doesn't report it at all. The node sums
`Daily_Raw_Meta_Ads!LPV` by date into the Meta rows, which is what makes the
click→landing-page rate real. Without it the metric reads 0.0% and looks broken.

**Duplicate ad-days are removed, keeping the newest pull.** The Meta ad-level
sync upserts on `(Date, Ad_ID)`; the TikTok CSV import appends instead, so the
same ad-day arrives once per sync run. On GOFRESH that was 13 duplicate rows.
They are not identical — TikTok restates reach and conversions as attribution
matures — and in the raw sheet the *newer* row usually comes first, so
"last row wins" would keep the stale copy. The node ranks on `Pulled_At`
explicitly.

**The reporting window is chosen from the data, not hardcoded.** A trailing day
is dropped only when it is obviously mid-sync (impressions recorded, reach zero).
Then the last 7 complete days are compared against the 7 before them. With fewer
than 14 days of history — a brand new client — it splits what exists in half
rather than failing.

### What the kit does with it

The moment `_Control` changes, everything downstream re-runs on its own:

- `KPI Calc` recomputes every metric for both periods;
- the three dashboards re-grade against `Benchmarks` and rewrite their commentary;
- `Ad Performance` re-ranks, because its column A is a live `QUERY` ordering ad
  names by spend *inside the selected period*;
- `Health Check` re-runs all thirteen checks.

There is no step where the automation has to write a number that a human would
otherwise have calculated.

---

## The summary email

One email per run, not one per client. It answers *"did every dashboard
refresh?"* without opening twelve sheets:

- a green or red banner with the count;
- one row per client: reporting period, comparison period, days, row counts,
  duplicates dropped, partial day dropped;
- an amber box for anything needing a human, worded as a consequence rather than
  a metric — *"13 duplicate ad rows were dropped… the Raw sheet still holds both
  copies, which means anything else reading `Daily_Raw_TikTok_Ads` at ad level is
  double-counting spend and revenue."*

Per-brand failures also send their own email immediately, and the run continues
with the next brand rather than stopping.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Every dashboard still shows Northwind Supply Co. | WF5 hasn't run, or no brand has a `Kit_Sheet_ID` | Run WF4, then WF5; check the registry column |
| `_Control` `Last_Refresh` is stale | WF5 is inactive or failing | Check the n8n execution log; the summary email says which brand failed |
| All numbers are zero but data is there | The period dates don't overlap the data | `Health Check` row 6 reads 0 — set `_Control` dates inside the data range |
| Dates show as `46303` | The date cells lost their format | Select `Fundamentals!A:A`, `Ad Data!A:A`, `_Control!B2:B5` → Format ▸ Number ▸ Date |
| `Ad Performance` is empty | `Ad Data` has no rows in the selected period, or ad names are blank | Check `_Control` dates; check the raw ad tabs have `Ad_Name` |
| `#REF!` after importing to Sheets | A tab was renamed | `Fundamentals`, `Ad Data`, `KPI Calc`, `_Control`, `Benchmarks` must keep their names |
| "cannot read raw data" email | Raw sheet not shared with the n8n Google account, or a raw tab renamed | Share it; check the four tab names |
| "write failed" email | A kit tab was renamed, or the dashboard was trashed | Restore the tab names; re-run WF4 if the file is gone |
| Same brand provisioned twice | `Save Kit_Sheet_ID` failed, so the registry never learned | The email contains the new sheet ID — paste it into `Kit_Sheet_ID` yourself |

---

## What this found on GOFRESH

Running the flatten logic against the live raw sheet surfaced two problems that
are in the pipeline, not in the kit. Both are worth fixing upstream, because WF3
reads the same tabs.

**1 · `Daily_Raw_TikTok_Ads` holds duplicate rows.** 13 ad-days appear twice,
once per sync run (`Pulled_At` 12 Oct and 15 Oct), double-counting **1,545 EGP of
spend and 4,935 EGP of revenue** across the fortnight. `Daily_Raw_Meta_Ads` is
clean, because WF1bu already upserts on `Date|Ad_ID`. WF2e appends instead. The
kit defends against it; the raw sheet still has it, so anything else reading
TikTok ad-level data is affected.

**2 · TikTok's ad-level export is missing spend.** In-period (8–14 Oct) the
account-level tab says 14,142.87 EGP; the ad-level rows add up to 9,290.54 —
**21% short**, and 31% short on purchases. Meta reconciles to the penny
(0.00%). This is not caused by the de-duplication: even *with* the duplicates the
gap was 17.6%. The worst days are 12 Oct (1,454 EGP missing) and 13 Oct (1,173),
while 14 Oct is complete, which points at the scheduled TikTok report itself
dropping rows rather than at attribution lag.

Consequence: `Health Check` rows 23 and 24 now read **CHECK** for GOFRESH. That
is the check working — before de-duplication the duplicate rows were padding the
ad-level totals and hiding it. The practical rule it implies: **quote TikTok
totals from `Fundamentals` (account level), never from `Ad Performance`.** The
ad-level table is still right for *ranking* which creative to scale; it just
isn't a complete spend ledger.

---

## Rebuilding the workflows

```bash
python3 "_build/build_n8n_workflows.py"
```

Regenerates both JSON files from this folder's two `.js` files plus the IDs at the
top of the script. Edit the `.js` files, not the JSON — the JSON is generated and
will be overwritten.
