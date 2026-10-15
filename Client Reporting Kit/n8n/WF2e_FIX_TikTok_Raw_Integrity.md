# WF2e fix — `Daily_Raw_TikTok_Ads` is duplicating rows and destroying Ad_IDs

Found while building the Client Reporting Kit on top of the pipeline, 15 Oct 2026.
This is **not** a kit bug — the kit works around it — but it corrupts the source
data every scheduled run, so it is worth 20 minutes to fix.

Everything below was measured against a live client raw sheet
(`14nlX_slJeGVJX7jV2SMqnqdUHDSV5InMuZYBLMWy-2I`, tab `Daily_Raw_TikTok_Ads`,
135 data rows at the time of writing).

---

## The two symptoms

### 1. Thirteen `(Date, Ad_ID)` pairs are stored twice

| Date | Ad_ID | copies | `Pulled_At` | Ad name |
|---|---|---|---|---|
| 2026-10-01 | 1877512861125682 | 2 | 10-12, 10-15 | vid - my new fav product |
| 2026-10-02 | 1877512861125682 | 2 | 10-12, 10-15 | vid - my new fav product |
| 2026-10-03 | 1877983550185729 | 2 | 10-12, 10-15 | because a good |
| 2026-10-04 | 1877983550185729 | 2 | 10-12, 10-15 | because a good |
| 2026-10-05 | 1877983550185729 | 2 | 10-12, 10-15 | because a good |
| 2026-10-06 | 1878341510800817 | 2 | 10-12, 10-15 | vid - mariam akkad |
| 2026-10-07 | 1878342326409249 | 2 | 10-12, 10-15 | VID - DR BAHR |
| 2026-10-08 | 1878342326409249 | 2 | 10-12, 10-15 | VID - DR BAHR |
| 2026-10-09 | 1878342326409249 | 2 | 10-12, 10-15 | VID - DR BAHR |
| 2026-10-10 | 1878673321732129 | 2 | 10-12, 10-15 | DR BAHR |
| 2026-10-11 | 1878673321732129 | 2 | 10-12, 10-15 | DR BAHR |
| 2026-10-12 | 1878673321732129 | 2 | 10-12, 10-15 | DR BAHR |
| 2026-10-13 | 1878673321732129 | 2 | 10-13, 10-15 | DR BAHR |

**Overstated by 1,545.07 EGP spend, 4,935.00 EGP revenue and 8 purchases.**

The arithmetic proves the upsert matched *nothing* on the 15 Oct run:

```
rows before the run   115   (Pulled_At 10-12: 108, 10-13: 7)
rows written          +20   (Pulled_At 10-15)
                      ---
rows now              135   <- exactly 115 + 20, so not one row was overwritten
```

13 of those 20 collided with a `(Date, Ad_ID)` that already existed. Had matching
worked, the sheet would hold **122** rows. It holds 135.

### 2. Two Ad_IDs have been permanently corrupted

16 rows store `Ad_ID` as a **number** instead of text — 119 rows are text, 16 are float:

| stored value | rows | ad name | 16 digits? | ends in 0? |
|---|---|---|---|---|
| `1870013048613970` | 8 | vid - mariam akkad | yes | **yes** |
| `1878341789686930` | 8 | vid - restocking my bag | yes | **yes** |

Google Sheets keeps **15 significant digits**. A 16-digit TikTok ad ID written as a
number therefore loses its last digit — and both surviving values ending in `0` is
the signature of exactly that. Neither ID exists anywhere in the sheet as text, so
**the true IDs are gone**; they cannot be recovered from this sheet.

It has already caused a fork. On **2026-10-06**, `vid - mariam akkad` has **three**
rows: two under the text ID `1878341510800817` (one per pull) and one under the
corrupted numeric ID `1870013048613970`. A numeric key can never equal a text key,
so these rows will be re-appended on every future run forever.

---

## Root cause

Both symptoms come from one node: `Upsert Daily_Raw_TikTok_Ads`
(`googleSheets` v4.7, `operation: appendOrUpdate`,
`columns.mappingMode: autoMapInputData`, `matchingColumns: ["Date","Ad_ID"]`).

The Sheets node lets Google **interpret** every value it writes:

- `Date` arrives from WF2e's `Normalize TikTok rows to raw-sheet headers` as the
  ISO string `2026-10-01`, and Google parses it into a real datetime. On the next
  run the incoming value is still the string `2026-10-01` but the sheet reads back a
  datetime — the two never compare equal, so **matching fails and the row is
  appended**. That is symptom 1.
- `Ad_ID` arrives as the digit string `1870013048613970`. Google parses a
  numeric-looking string as a number and rounds it to 15 significant digits.
  That is symptom 2.

**WF1bu does not have either problem, and the reason is already in your repo.** It
never uses `appendOrUpdate`. It does:

1. `Read existing ad rows` — HTTP `values:batchGet` with `UNFORMATTED_VALUE`
2. `Plan row writes` — a Code node with `normDate()` and `normId()`, which forces
   `Ad_ID` to `String(v)` on write and counts pre-existing duplicates
3. `Write ad rows` — HTTP `values:batchUpdate` with `valueInputOption: 'RAW'`,
   which stores exactly what it is given and parses nothing

Result: `Daily_Raw_Meta_Ads` has **zero** duplicate `(Date, Ad_ID)` pairs and
**zero** mixed-type Ad_IDs.

---

## The fix

`WF2e_PATCH_TikTok_Ads_Upsert.json` in this folder is that trio, ported to
`Daily_Raw_TikTok_Ads`. Import it as a scratch workflow and copy the three nodes
into WF2e, or rebuild them by hand — the Code node is also saved standalone as
`code_plan_tiktok_ad_writes.js`.

### Wiring

Replace the single node `Upsert Daily_Raw_TikTok_Ads` with:

```
Explode ad rows
      |
      v
Read existing TikTok ad rows     (httpRequest, GET values:batchGet)
      |            \ error -> Send a message
      v
Plan TikTok ad row writes        (code, runOnceForAllItems)
      |
      v
Write TikTok ad rows             (httpRequest, POST values:batchUpdate)
      |            \ error -> Send a message
      v
(whatever "Upsert Daily_Raw_TikTok_Ads" was connected to)
```

Then **delete** `Upsert Daily_Raw_TikTok_Ads`.

Both HTTP nodes reference `$('Loop Brands Ads').first().json.Raw_Sheet_ID` — that is
WF2e's loop node for the ads branch. Both use credential
`SBl4DBB9PIqzy5w0` ("Ai Saher Google Sheets"), the same one WF1bu uses.

### What the Code node changes relative to WF1bu's version

- Reads incoming rows from `$('Explode ad rows').all()` (one item per row) instead
  of `$('Collect rows').first().json.rows` (one item holding an array).
- Writes `Date` as a **serial number**, not text, because this column already holds
  real dates — the point is to stop mixing types, not to start. `normDate()` still
  accepts serials, ISO strings and datetimes on read, so matching works regardless
  of what is already in the column.
- When a `(Date, Ad_ID)` already exists more than once, it keeps the row with the
  **newest `Pulled_At`**. This matters: the newer row is usually *first* in this
  sheet, so a naive last-wins rule would keep the stale copy.
- Collapses duplicates **within** the incoming batch too, so a single run cannot
  create one.
- Validates every write range before returning. A malformed range throws instead of
  reaching the API — a partial `batchUpdate` is worse than a failed one.
- Returns four counters worth logging or alerting on:
  `updated`, `appended`, `existing_duplicates`, `numeric_ids_repaired`.

### Verified

The Code node was executed under Node v22 against a `batchGet` payload built from
the real client sheet, in two scenarios:

| scenario | result |
|---|---|
| Replay the 15 Oct run against the sheet **as it was before it** (115 rows) | `updated: 13, appended: 7` → sheet ends at **122** rows, not 135. All 13 updates land on the row that already holds that `(Date, Ad_ID)`. Zero misaligned writes. |
| Replay against the sheet **as it is today** (135 rows) | `updated: 20, appended: 0`, and it correctly reports `existing_duplicates: 13` and `numeric_ids_repaired: 2` |

In both: all 20 written `Ad_ID`s are strings, none in exponential notation, all 20
`Date`s are serials, and no write overwrote a different day than the one it read.

> I could not execute n8n itself — there is no n8n in this sandbox. The Code node
> and the payload shapes are verified; the wiring you should eyeball once after
> importing.

---

## One-off cleanup of the rows already there

The patch stops new damage. It does not remove the 13 duplicates already in the
sheet — do that once, by hand, where you can see it:

1. Open `Daily_Raw_TikTok_Ads`. Add a helper column with
   `=A2&"|"&TEXT(B2,"0")` and copy it down. (The `TEXT(...,"0")` stops a numeric
   Ad_ID rendering as `1.87E+15`.)
2. **Data → Sort range** by that helper column, then by `Pulled_At` **descending**.
   Each duplicated pair now sits together with the newer pull on top.
3. Delete the **lower** row of each of the 13 pairs listed above — that is the one
   with the older `Pulled_At`.
4. Select column B → **Format → Number → Plain text**. This does not replace the
   patch (n8n's `appendOrUpdate` coerces types regardless of cell format), but it
   stops manual pastes from re-introducing the problem.
5. Delete the helper column.

For the two corrupted IDs there is no recovery — the 16th digit is gone. Practical
options, cheapest first:

- Leave them. They are 2 of ~30 ads; ad *names* still rank correctly, and
  `Ad Performance` groups by name, not ID.
- If you need the true IDs, pull them from TikTok Ads Manager for
  `vid - mariam akkad` and `vid - restocking my bag` and paste them into column B
  as text (after step 4).

### Also check whether the corruption is upstream

If those two ads' rows arrived from an **XLSX** attachment rather than the CSV
branch, Excel had already destroyed the 16th digit before n8n ever saw it, and
`String(v)` cannot bring it back. WF2e has `Is CSV attachment?` with legacy
XLS/XLSX fallbacks — worth confirming the scheduled report is configured to send
**CSV**. If it is CSV, the coercion happened on write and the patch fully fixes it.

---

## Effect on the Client Reporting Kit

**None — the kit is already immune.** WF5's flatten step (`code_flatten_to_kit_shape.js`)
deduplicates ad-days by newest `Pulled_At` before it writes `Fundamentals` and
`Ad Data`, which is why the delivered client workbook shows 387 ad rows
rather than 400.

Two consequences worth knowing:

- **Health Check rows 23–24 read `CHECK` for that account** (7.38% / 11.84% against
  tolerances of 5% / 8%). That is a *separate* issue — TikTok's ad-level export is
  missing spend (11,658.83 vs 14,142.87 account-level for 8–14 Oct, 17.6% short;
  25.8% short on revenue, 30.1% on purchases). Fixing the duplicates does not close
  that gap. **Quote TikTok totals from `Fundamentals`, never from `Ad Performance`**
  — the Ad Performance tab is reliable for ranking ads against each other, not for
  platform totals.
- Fixing WF2e is still worth doing: it stops the raw sheet growing without bound,
  and it removes a class of drift that will eventually confuse WF3's monthly
  reports, which read the raw tabs directly and do **not** deduplicate.

---

## Separate, not fixed here

`Upsert Daily_Raw_TikTok` (the **account-level** tab) uses the same
`appendOrUpdate` pattern, matching on `["Date"]` only. It currently has **no**
duplicates, because `Date` is the only key and re-pulls of the same day land on the
same row often enough. It is exposed to the same `Date` type mismatch in principle.
If you see `Daily_Raw_TikTok` start duplicating, apply the same three-node pattern
with `need` set to the account-level header list and `matchingColumns` on `Date`
alone.
