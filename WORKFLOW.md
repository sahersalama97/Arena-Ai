# GoFresh Ads Report — n8n workflow breakdown

Workflow: 40 nodes · 3 triggers · 13 Code nodes · 22 Google Sheets nodes (4 read · 9 clear · 9 append) · 1 email.
Spreadsheet: `1ENZCyFBgTNiPuE7nRz5ofic5pao_zjdhwiFLIEyo5LE` (13 tabs).

---

## 1. What the workflow does, stage by stage

```
STAGE 0  TRIGGER              Manual Test  |  Weekly Trigger (0 7 * * 1)  |  Monthly Trigger (15 7 1 * *)
                                    \              |              /
STAGE 1  DEFINE PERIOD      Set Manual Period   Set Weekly Period   Set Monthly Period
                                    \              |              /
                            Set Period  (NoOp — joins the 3 paths into one node name)
                                             |
STAGE 2  READ RAW        ┌───────────────────┼───────────────────┬───────────────────┐
                   Read Daily_Raw_Meta  Read Daily_Raw_Meta_Ads  Read Daily_Raw_TikTok  Read Daily_Raw_TikTok_Ads
                             |       \            |      \             |    |   \             |      \
STAGE 3  AGGREGATE   Meta Overview   Meta Weekly  Meta Ad Perf  Meta Creative  TikTok Overview/Weekly  TikTok Ad Perf/Creative  Combined
                             |             |             |             |             |             |             |             |             \
STAGE 4  CLEAR       Clear R_Meta_Overview ...one per report tab, 9 total...          Clear Report_Combined
                             |             |             |             |             |             |             |             |             |
STAGE 4  WRITE       Write R_Meta_Overview ...append, 9 total...                       Write Report_Combined
                             \             |             |             |             |             |             |             /
STAGE 5  EMAIL                              Compose Report Email → Send Report Email
```

**Stage 0 — 3 triggers, one pipeline.** `Weekly Trigger` = `0 7 * * 1` → Monday 07:00 (workflow/instance timezone). `Monthly Trigger` = `15 7 1 * *` → 1st of month 07:15. `Manual Test` is the "run it now" door.

**Stage 1 — pick the date window.** Each path emits `{reportType, periodStart, periodEnd, periodLabel}`:

| path | window | label example |
|---|---|---|
| Manual | yesterday back 6 days (7 days) | `Manual test - last 7 days` |
| Weekly | last Mon–Sun (`minus({weeks:1}).startOf('week')`) | `Sep 14 - Sep 20, 2026` |
| Monthly | full previous month | `August 2026` |

The `Set Period` NoOp is the join point so every downstream Code node can say `$('Set Period').first().json` regardless of which trigger fired. Good design.

**Stage 2 — read raw, never write raw.** 4 read nodes pull the *whole* tab of the 4 `Daily_Raw_*` sheets (account-level and ad-level, per platform). All 4 carry `onError: continueRegularOutput` + `alwaysOutputData: true` — i.e. "if the read fails, keep going anyway" (see §4.1).

**Stage 3 — 9 aggregators, all same shape.**
1. `filter(r => r.Date >= periodStart && r.Date <= periodEnd)` → restrict raw daily rows to the window.
2. `num()` coerces each measure, `+=` into totals (missing/garbage cell = `0`).
3. derive `CPM = spend/impr*1000`, `CTR = clicks/impr`, `Frequency = impr/reach`, `ROAS = value/spend`, `AOV = value/purchases`, `CVR = purchases/clicks`, all guarded against divide-by-zero.
4. `round(...)`; then `sort` + attach `Rank`.

| aggregator | groups by | sorted by |
|---|---|---|
| Meta/TikTok Overview | nothing (period totals) | fixed metric list, 13–14 rows |
| Meta/TikTok Weekly | ISO week | **ROAS desc** |
| Meta/TikTok Ad Performance | `Ad_ID \|\| Ad_Name` | Spend desc |
| Meta/TikTok Creative Rollup | `Creative_Key` (counts distinct Ad_IDs as `Instances`) | Spend desc |
| Combined | nothing — Meta vs TikTok vs combined, share-of-spend | fixed 7 rows |

`Combined Aggregator` ignores its own input items and instead re-reads `$('Read Daily_Raw_Meta').all()` + `$('Read Daily_Raw_TikTok').all()`. It uses the *account-level* tabs, not the ad-level ones — correct, that avoids double-counting duplicate ad rows.

**Stage 4 — truncate & reload the 9 report tabs.** `Clear Report_X` then `Write Report_X` (`append`, `autoMapInputData`).

**Stage 5 — one summary email.** Subject/body built from `$('Combined Aggregator')` + a link to the spreadsheet.

---

## 2. Why the Clear node is there — the actual answer

**Yes: each Clear node wipes the report tab this same run is about to rewrite.** Verified programmatically — the set of cleared tabs and the set of appended tabs are *identical* (9 `Report_*` tabs), and **no tab is ever both read and cleared**:

```
clear set == write set: True
non-Report tab cleared: NONE     <-- raw data never wiped
read ∩ cleared:        NONE     <-- nothing is both read and cleared
```

So it clears the sheets it wrote before, and only those. The `Daily_Raw_*` history is never touched — this workflow only reads it. That distinction is the whole point: **the raw tabs are the archive, the `Report_*` tabs are a view.**

The mechanical reason it's needed: the write is `append`, not `update`. Append always lands below the last row. Without a clear, Monday's run bolts week 2 under week 1, week 3 under that, and after a month the "weekly" tab is a pile of overlapping periods — a reader can't tell which rows are current, and any chart pointed at it goes wrong. So `Clear + Append` = *"this tab always contains exactly one thing: the period just computed."*

Two properties of n8n's Clear worth knowing (read from the node source, `Google/Sheet/v2/actions/sheet/clear.operation.ts`):

- It uses `spreadsheets.values.clear`, which removes **values only**. Your number formats, colors, conditional formatting and column widths on the report tab survive every run.
- The node **passes its input items straight through** (`return items`). So placing it between the aggregator and the write loses nothing — the wipe happens as the last possible moment before the rewrite, which minimises the "empty tab" window a human might catch in a refresh.

Also: `Clear` in n8n means *empty the cells*, not *delete rows* — the row count and sheet dimensions stay, only contents go.

**One consequence to accept:** nothing from a previous run is kept. Last week's report is gone the moment this week's runs. If you want a growing history of weekly reports, that needs a separate archive tab keyed on `Period_Start` with **Append or Update** (match on `Period_Start`), not a clear.

### What the current Clear settings do — check this

All 9 Clear nodes have **no `options` block**, so every option is default:

| param | effective value | effect |
|---|---|---|
| `Clear` | `Whole Sheet` | wipes the entire tab, all columns, all rows |
| `Keep First Row` | `false` | **the header row is wiped too** |

That is *survivable* here, because `append` self-heals an empty sheet (from `append.operation.ts`: if `sheetData` is empty, n8n forces auto-map mode, writes the input field names as row 1, data from row 2). So headers are rebuilt from the **code's field names** on every run. Consequence: hand-edits to a report tab's header text are reverted every Monday — and if you rename `Purchases_Value` to `Purchases Value` in the sheet for readability, your rename disappears on the next run.

If you prefer to protect the header, set `Keep First Row = true` — but do it **together with** the Execute-Once fix in §4.4, because that option costs 2 extra API calls *per item*.

---

## 3. Why this design is actually a good one

- **Idempotent / re-runnable.** Because every report is recomputed from the full raw history and then swapped in whole, you can re-run any period any number of times and the tabs stay correct. No dedupe logic, no "which rows did I already write" bookkeeping. That is the correct pattern for derived reports.
- **Reconciliation built in.** `Combined` re-derives Meta and TikTok totals from the same read nodes the per-platform tabs use, so the summary and the tabs can't disagree.
- **Period-agnostic.** Manual / weekly / monthly all share one pipeline; only the window differs.
- **Wide tables, not long ones.** Overview tabs as `Metric | Value` rows make adding a metric a one-line change and keep charts pointed at a stable shape.

---

## 4. Real problems, in order of how much they will bite

### 4.1 ⚠️ A failed read silently publishes an all-zeros report over your real numbers
This is the sharpest edge of the Clear node and the thing to fix first. Chain: read fails → `continueRegularOutput` emits an error item instead of stopping → aggregator's period filter matches nothing → `rows = []` → every sum is `0` → **Clear wipes the good report** → zeros are written.

Two failure shapes, both silent:
- Overview / Combined tabs: 13–14 rows of `0` — looks like a dead ad account.
- Weekly / Ad / Creative tabs: aggregators return 0 items, and `append` early-returns (`if (!items.length || dataMode === 'nothing') return []`) → the tab is left **completely blank** after the clear.

Fix — a 3-line gate at the end of every aggregator, before the Clear can fire:

```js
if (!rows.length) throw new Error(
  `Aborting: 0 raw rows matched ${period.periodStart}..${period.periodEnd} on Daily_Raw_Meta ` +
  `(check the tab, the Date format, and that ingestion ran)`);
```

and keep `onError: continueRegularOutput` only where you genuinely want a graceful skip.

### 4.2 ⚠️ The period filter depends on the raw `Date` column being exactly `yyyy-mm-dd`
`r.Date >= period.periodStart && r.Date <= period.periodEnd` is a **string** compare, and n8n reads cells as `FORMATTED_VALUE`, i.e. what the tab *displays*. If the raw sheet shows `3/9/2026`, `9/3/2026` or `٩/٣/٢٠٢٦`, the comparison silently matches **nothing** → same outcome as §4.1 but every run, not just bad runs. The weekly tabs hit the same wall via `DateTime.fromISO(r.Date)` → invalid date → garbage labels.

Normalize instead of assuming:

```js
const iso = (v) => {
  if (v == null || v === '') return '';
  if (/^\d{4}-\d{2}-\d{2}/.test(v)) return v.slice(0, 10);
  const n = Number(v);
  if (Number.isFinite(n) && n > 20000 && n < 60000)          // Sheets serial number
    return DateTime.fromMillis(Date.UTC(1899, 11, 30) + n * 864e5).toISODate();
  const d = DateTime.fromFormat(v, 'M/d/yyyy')                                     // adjust to your display format
           || DateTime.fromFormat(v, 'd/M/yyyy');
  return d && d.isValid ? d.toISODate() : '';
};
const rows = items.map(i => i.json)
  .map(r => ({ ...r, _d: iso(r.Date) }))
  .filter(r => r._d >= period.periodStart && r._d <= period.periodEnd);
```

Same class of bug for money: `Number('1,234.56')` → `NaN` → `num()` → `0`. Thousands separators, `$`, `د.م`/`EGP` suffixes all become invisible zeros. Use `Number(String(v).replace(/[^0-9.\-]/g, ''))`.

### 4.3 ⚠️ Up to 9 duplicate emails
All 9 `Write` nodes feed `Compose Report Email`. n8n ≥1.0 "executes each branch in turn, completing one branch before starting another" (canvas order: topmost first), so a junction node fires once per arriving branch rather than once with everything merged — the Merge node exists precisely because data is *not* auto-merged at a fan-in. Worst case: 9 emails, each with the same content (content comes from `$('Combined Aggregator')`, not from `$json`, so they're all identical).

Fix, cheapest first:
1. Route the email off **one** branch only — make the 9 writes a single chain `Write1 → Write2 → … → Write9 → Compose → Send`, or simply connect only `Write Report_Combined` to `Compose`.
2. Or insert a `Merge` node (Inputs 2, mode `Choose Branch`, *Wait for all inputs to arrive*) between the fan-in and `Compose`.
3. Or set `Execute Once` on `Compose Report Email`.

### 4.4 ⚠️ Every Clear runs once per row — wasted quota
`clear.operation.ts` loops `for (let i = 0; i < items.length; i++)` around `sheet.clearData(range)`. Each Clear therefore issues **N identical `values.clear` calls**, N = rows from its aggregator: 13 for Meta Overview, 14 for TikTok Overview, 7 for Combined, and *one per ad* for the Ad Performance tabs. 80 ad rows → 80 clear calls to empty an already-empty tab. Sheets write quota is 300/min/user — 9 tabs × row counts is how you get rate-limited and how a run turns into a partial write (which then looks like §4.1).

Fix: on all 9 Clear nodes → **Settings → Execute Once**. One clear call per tab. Do this before enabling `Keep First Row`.

### 4.5 ⚠️ `Combined Aggregator` reads a node that is not its ancestor
`$('Read Daily_Raw_Meta').all()` is a cross-branch lookup — the Meta read lives on another branch and is **not** upstream of `Combined Aggregator` (verified: graph check reports `!! NOT an ancestor`). It works today only because branch order follows canvas position top-to-bottom and `Read Daily_Raw_Meta` sits at y = −336, above the TikTok branch at y = 144. Drag those nodes and Meta silently reads as empty → the Combined tab's Meta column goes to 0 while TikTok looks fine.

Fix: feed `Combined` from an explicit join — tag each read (`Source: 'meta'` / `'tiktok'`) in a small Code node, pass both into a `Merge` (Append), and have `Combined` group `items` by `Source` instead of reaching into other branches.

### 4.6 The weekly tabs are sorted by ROAS, so your time series is out of order
`Meta/TikTok Weekly Aggregator` does `list.sort((a,b)=>(b.ROAS===''?-1:b.ROAS)-(a.ROAS===''?-1:a.ROAS))`. Sorting *spend/ROAS* rankings is right for Ad/Creative tabs, but for a weekly trend table the reader (and any chart) expects chronological rows, and `Rank` here then means "ROAS rank", not "week order". Fix: `list.sort((a,b)=>a.Period_Start.localeCompare(b.Period_Start))`, and drop `Rank` or add it after a ROAS sort on a copy.

### 4.7 Triggers fire before ingestion may have finished
Weekly runs Monday 07:00 and computes **last Mon–Sun**; monthly runs on the 1st at 07:15 and computes the **previous month**. If the workflow that fills `Daily_Raw_*` writes "yesterday" later than those times, the report publishes with the last day missing — and it looks complete, because it's silent totals. Move the report triggers to after the ingestion job (or run the monthly on the 2nd), or add a guard that asserts a row exists for `periodEnd` and otherwise aborts per §4.1.

### 4.8 Cosmetic / housekeeping
- `Send Report Email` has **no credentials block** and still holds `PASTE_ALERT_SENDER_EMAIL@example.com` / `PASTE_YOUR_REPORT_EMAIL@example.com` → it will fail on the first real run.
- The email body's `Full report: <spreadsheet>` link opens the *whole workbook*, including `Daily_Raw_*`. Link the specific tab: `.../edit#gid=<sheetId>`.
- `Compose` prints raw numbers with no formatting: `Combined Spend: 12345.6789`, `ROAS: undefined` when Combined returns nothing (which §4.1 can cause). Wrap: `$formatNumber(v, 2)`, and `?? 'n/a'`.
- Timezone: cron is evaluated in the workflow's timezone setting, not Cairo's by default. Confirm `Settings → Timezone` (e.g. `Africa/Cairo`) or your Monday 07:00 is someone else's 05:00.
- No `settings.errorWorkflow` on any of these runs: with §4.1 unresolved, a broken report is indistinguishable from a quiet week. Add an error-workflow that emails you on failure.

---

## 5. Priority list

| # | action | why |
|---|---|---|
| 1 | Throw on `!rows.length` in each aggregator (§4.1) | stops zeros/blank tabs overwriting good reports |
| 2 | Normalize `Date` + currency parsing (§4.2) | silent zero-data, every run |
| 3 | `Execute Once` on the 9 Clears (§4.4) | quota, partial writes |
| 4 | Single chain or Merge before `Compose` (§4.3) | duplicate emails |
| 5 | Join both reads before `Combined` (§4.5) | position-dependent correctness |
| 6 | Sort weekly by `Period_Start` (§4.6) | readable trend |
| 7 | Move triggers after ingestion; fill SMTP creds + real addresses (§4.7, §4.8) | completeness of data, deliverability |
| 8 | Decide header policy: default (code owns headers) or `Keep First Row` (§2) | your manual edits get reverted otherwise |
