"""
Build a LIVE dashboard from GOFRESH's real pipeline data.

Reads the exported Raw Data workbook (all four tabs) and writes a filled copy of
the dashboard xlsx. Nothing is invented except the three business-cost cells,
which are labelled in the file as assumptions that must be replaced.
"""
import datetime as dt
import os
from openpyxl import load_workbook
from openpyxl.styles import Font

SRC_RAW = "/tmp/gofresh.xlsx"
SRC_KIT = "/home/user/Arena-Ai/Client Reporting Kit/01_Google_Sheets_Reporting_Dashboard.xlsx"
OUT = "/home/user/Arena-Ai/google_drive/GOFRESH - Reporting Dashboard (LIVE).xlsx"

CUR = "EGP"
BRAND_NAME = "GOFRESH"
# ---- THE ONLY INVENTED NUMBERS. Labelled as assumptions in the file. ----
ASSUMED_COGS_PCT = 0.30
ASSUMED_OTHER_VAR_PCT = 0.04
ASSUMED_SHIP_PER_ORDER = 65
# -------------------------------------------------------------------------


def as_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str) and len(v) >= 10 and v[4] == "-":
        return dt.date.fromisoformat(v[:10])
    return None


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


raw = load_workbook(SRC_RAW, data_only=True)
meta = raw["Daily_Raw_Meta"]
tiktok = raw["Daily_Raw_TikTok"]
meta_ads = raw["Daily_Raw_Meta_Ads"]
tt_ads = raw["Daily_Raw_TikTok_Ads"]

# ============================================================ FUNDAMENTALS
# Kit columns: Date, Platform, Spend, Impressions, Reach, Clicks,
#              Landing Page Views, Add to Cart, Initiate Checkout, Purchases, Revenue
fund = []
for r in range(2, meta.max_row + 1):
    d = as_date(meta.cell(r, 1).value)
    if not d:
        continue
    fund.append([d, "Meta",
                 num(meta.cell(r, 2).value),   # Spend
                 num(meta.cell(r, 3).value),   # Impressions
                 num(meta.cell(r, 4).value),   # Reach
                 num(meta.cell(r, 7).value),   # Clicks
                 None,                          # LPV: Meta account level does not report it
                 num(meta.cell(r, 9).value),   # Adds_to_Cart
                 num(meta.cell(r, 10).value),  # Initiate_Checkout
                 num(meta.cell(r, 11).value),  # Purchases
                 num(meta.cell(r, 12).value)])  # Purchases_Value

for r in range(2, tiktok.max_row + 1):
    d = as_date(tiktok.cell(r, 1).value)
    if not d:
        continue
    fund.append([d, "TikTok",
                 num(tiktok.cell(r, 2).value),   # Spend
                 num(tiktok.cell(r, 3).value),   # Impressions
                 num(tiktok.cell(r, 4).value),   # Reach
                 num(tiktok.cell(r, 6).value),   # Clicks  (note: TikTok order differs)
                 None,                            # LPV: TikTok does not report it
                 num(tiktok.cell(r, 11).value),  # Adds_to_Cart
                 num(tiktok.cell(r, 12).value),  # Initiate_Checkout
                 num(tiktok.cell(r, 13).value),  # Purchases
                 num(tiktok.cell(r, 14).value)])  # Purchases_Value

# The account-level Meta tab has no LPV column, but the AD-level tab does, and
# the kit's click-to-landing-page metric needs it. Sum the ad-level LPV by date.
meta_lpv = {}
for r in range(2, meta_ads.max_row + 1):
    d = as_date(meta_ads.cell(r, 1).value)
    if not d:
        continue
    meta_lpv[d] = meta_lpv.get(d, 0.0) + num(meta_ads.cell(r, 14).value)   # N = LPV
filled = 0
for row in fund:
    if row[1] == "Meta" and meta_lpv.get(row[0]):
        row[6] = meta_lpv[row[0]]
        filled += 1

fund.sort(key=lambda x: (x[0], x[1]))

# ================================================================== AD DATA
# Kit columns: Date, Platform, Ad Name, Campaign, Ad Group / Ad Set,
#              Creative Key, Spend, Impressions, Clicks, Purchases, Revenue
ads = []
# De-duplicate on (Date, Ad_ID), keeping the most recently PULLED copy. The Meta
# ad-level sync upserts on that key upstream; the TikTok CSV import appends
# instead, so one ad-day arrives once per sync run and quietly doubles its spend
# and revenue. The two copies are NOT identical -- TikTok restates reach and
# conversions as attribution matures -- and in the raw sheet the newer row is
# usually FIRST, so "last row wins" would keep the stale numbers.
DUPLICATE_AD_ROWS_REMOVED = 0


def collect_ad_rows(ws, platform, clicks_col, pulled_col):
    """One row per (date, Ad_ID), newest pull winning."""
    global DUPLICATE_AD_ROWS_REMOVED
    best, rank = {}, {}
    for r in range(2, ws.max_row + 1):
        d = as_date(ws.cell(r, 1).value)
        name = ws.cell(r, 3).value
        if not d or not name:
            continue
        ad_id = str(ws.cell(r, 2).value or "").strip()
        key = (d, ad_id or str(name))
        pulled = str(ws.cell(r, pulled_col).value or "")
        row = [d, platform,
               name, ws.cell(r, 5).value if platform == "Meta" else ws.cell(r, 4).value,
               ws.cell(r, 4).value if platform == "Meta" else ws.cell(r, 5).value,
               ws.cell(r, 6).value,
               num(ws.cell(r, 7).value), num(ws.cell(r, 8).value),
               num(ws.cell(r, clicks_col).value), num(ws.cell(r, 17).value),
               num(ws.cell(r, 18).value)]
        if key in best:
            DUPLICATE_AD_ROWS_REMOVED += 1
            if pulled < rank[key]:
                continue                      # older pull: ignore it
        best[key], rank[key] = row, pulled
    return list(best.values())


# Meta: 1 Date, 2 Ad_ID, 3 Ad_Name, 4 AdSet_Name, 5 Campaign_Name, 6 Creative_Key,
#       7 Spend, 8 Impressions, 12 Clicks, 17 Purchases, 18 Purchases_Value, 22 Pulled_At
ads += collect_ad_rows(meta_ads, "Meta", 12, 22)
# TikTok: 1 Date, 2 Ad_ID, 3 Ad_Name, 4 Campaign_Name, 5 AdGroup_Name,
#         6 Creative_Key, 7 Spend, 8 Impressions, 11 Clicks, 17 Purchases,
#         18 Purchases_Value, 22 Pulled_At
ads += collect_ad_rows(tt_ads, "TikTok", 11, 22)

ads.sort(key=lambda x: (x[0], x[1]))

# ============================================================== period choice
# Adaptive. The pipeline re-pulls a rolling window every night, so the newest
# row can be a partial day. We drop a trailing day only when it is obviously
# incomplete (impressions recorded but reach zero), then report the last
# WINDOW_DAYS complete days against the WINDOW_DAYS before them.
WINDOW_DAYS = 7

by_date = {}
for row in fund:
    d, plat = row[0], row[1]
    e = by_date.setdefault(d, {})
    e[plat] = row

def looks_partial(d):
    """A day where a platform posted impressions but no reach is mid-sync."""
    for plat, row in by_date[d].items():
        if row[3] > 0 and row[4] == 0:      # impressions > 0, reach == 0
            return True
    return False

all_dates = sorted(by_date)
dropped = []
while all_dates and looks_partial(all_dates[-1]):
    dropped.append(all_dates.pop())

if len(all_dates) < WINDOW_DAYS * 2:
    raise SystemExit(f"need {WINDOW_DAYS*2} complete days, have {len(all_dates)}")

CUR_START, CUR_END = all_dates[-WINDOW_DAYS], all_dates[-1]
CMP_START, CMP_END = all_dates[-WINDOW_DAYS * 2], all_dates[-WINDOW_DAYS - 1]
USABLE = all_dates

tot = lambda rows, s, e, p=None: sum(x[2] for x in rows if s <= x[0] <= e and (not p or x[1] == p))
rev = lambda rows, s, e: sum(x[10] for x in rows if s <= x[0] <= e)
sp = tot(fund, CUR_START, CUR_END)
rv = rev(fund, CUR_START, CUR_END)

print(f"GOFRESH data: {all_dates[0]} to {all_dates[-1]}  ({len(fund)} account rows, {len(ads)} ad rows)")
print(f"Partial trailing day(s) dropped: {dropped if dropped else 'none'}")
print(f"Current period  {CUR_START} to {CUR_END}: spend {sp:,.0f}  revenue {rv:,.0f}  ROAS {rv/sp:.2f}x")
print(f"Compare period  {CMP_START} to {CMP_END}: spend {tot(fund,CMP_START,CMP_END):,.0f}  "
      f"revenue {rev(fund,CMP_START,CMP_END):,.0f}")

# ================================================================ build file
wb = load_workbook(SRC_KIT)

# --- Fundamentals
ws = wb["Fundamentals"]
for r in range(ws.max_row, 1, -1):
    for c in range(1, 12):
        ws.cell(r, c).value = None
for i, row in enumerate(fund):
    for j, v in enumerate(row):
        ws.cell(2 + i, 1 + j).value = v
for i in range(len(fund)):
    r = 2 + i
    ws.cell(r, 1).number_format = "yyyy-mm-dd"
    for c in (3, 11):
        ws.cell(r, c).number_format = '#,##0.00" EGP"'
    for c in (4, 5, 6, 7, 8, 9, 10):
        ws.cell(r, c).number_format = "#,##0"
ws.auto_filter.ref = f"A1:K{1+len(fund)}"
ws["M1"] = "Source: GOFRESH - Raw Data"
ws["M1"].font = Font(name="Inter", size=9, bold=True, color="B91C1C")

# --- Ad Data
ws = wb["Ad Data"]
for r in range(ws.max_row, 1, -1):
    for c in range(1, 12):
        ws.cell(r, c).value = None
for i, row in enumerate(ads):
    for j, v in enumerate(row):
        c = ws.cell(2 + i, 1 + j)
        c.value = v
        if j == 0:
            c.number_format = "yyyy-mm-dd"
        elif j in (6, 10):
            c.number_format = '#,##0.00" EGP"'
        elif j in (7, 8, 9):
            c.number_format = "#,##0"
ws.auto_filter.ref = f"A1:K{1+len(ads)}"
ws["M1"] = "Source: GOFRESH - Raw Data (ad-level tabs)"

# --- KPI Calc: periods + labelled business assumptions
ws = wb["KPI Calc"]
# Periods live on _Control now (KPI Calc B4:C5 read from there), so that both a
# human and the n8n refresh workflow change the period in exactly one place.
ws = wb["_Control"]
ws["B2"], ws["B3"] = CUR_START, CUR_END
ws["B4"], ws["B5"] = CMP_START, CMP_END
for ref in ("B2", "B3", "B4", "B5"):
    ws[ref].number_format = "yyyy-mm-dd"
# These three are what the n8n refresh workflow stamps on every run. Writing
# them here means this file looks exactly like one the automation produced.
ws["B6"] = BRAND_NAME
ws["B7"] = dt.datetime.now().replace(microsecond=0)
ws["B7"].number_format = "yyyy-mm-dd hh:mm"
ws["B8"] = len(ads)
ws = wb["KPI Calc"]
ws["J5"] = ASSUMED_COGS_PCT
ws["J6"] = ASSUMED_OTHER_VAR_PCT
ws["J7"] = ASSUMED_SHIP_PER_ORDER
# make it impossible to miss
ws["I4"] = "  ⚠ ASSUMED COSTS — REPLACE"
ws["I4"].font = Font(name="Inter", size=10, bold=True, color="B91C1C")

# --- Ad Performance: replace the sample roster with the real top 10 by spend
in_period = [a for a in ads if CUR_START <= a[0] <= CUR_END]
by_ad = {}
for a in in_period:
    k = (a[1], a[2])
    d = by_ad.setdefault(k, dict(spend=0.0, rev=0.0, camp=a[3], ck=a[5]))
    d["spend"] += a[6]
    d["rev"] += a[10]
    if a[3]:
        d["camp"] = a[3]
    if a[5]:
        d["ck"] = a[5]
# Rank on the period being reported, NOT lifetime spend -- otherwise ads that
# only ran in the comparison weeks outrank the ones that won this period, and
# they show up with zeroes in the table.
top = sorted(by_ad.items(), key=lambda kv: -kv[1]["spend"])[:10]

# Ad Performance is NOT written here any more. Column A of that tab is a live
# QUERY over Ad Data that ranks ad names by spend inside the selected period, so
# it re-ranks itself whenever _Control changes. Writing a static list here was
# the original bug: it froze one period's winners into a table that then summed
# a different period against them. `top` below is kept only so the build can
# print what the query is expected to return, and be checked against it.

# --- Dashboard: honest warning about attribution maturity
ws = wb["Dashboard"]
# Find the days where revenue was booked with (almost) no spend. Those are sales
# from an earlier click still landing -- the reason a fresh period always reads
# low against a mature one. Derived from the data so the sentence stays true as
# the pipeline keeps running, instead of naming fixed dates that go stale.
LAG_DAYS = [r for r in fund
            if r[2] < 1 and r[10] > 0 and CMP_START <= r[0] <= CUR_END]
lag_note = ""
if LAG_DAYS:
    days = sorted({r[0] for r in LAG_DAYS})
    shown = ", ".join(d.strftime("%b %-d") if hasattr(d, "strftime") else str(d) for d in days[:4])
    if hasattr(days[0], "strftime"):
        shown = ", ".join(f"{d.month}/{d.day}" for d in days[:4])
    lag_note = (f" On {shown} GOFRESH booked revenue against effectively zero spend -- those were "
                f"sales from earlier clicks still landing.")
warn = (
    "READ THIS BEFORE ACTING ON THE COMPARISON. The current period is more recent than the comparison "
    "period, and Meta and TikTok keep attributing purchases for days after a click." + lag_note +
    " The same effect is working in reverse on the current period: its purchases are still arriving, so "
    "its ROAS and conversion rate are understated. Your pipeline re-pulls a rolling window every night, "
    "so these numbers will settle over the next week. Do not cut budget on this comparison yet."
)
ws["A36"] = warn
ws.merge_cells("A36:H39")
ws["A36"].alignment = __import__("openpyxl").styles.Alignment(horizontal="left", vertical="top", wrap_text=True)
ws["A36"].font = Font(name="Inter", size=10, bold=True, color="B91C1C")
ws["A36"].fill = __import__("openpyxl").styles.PatternFill("solid", fgColor="FEE2E2")
for row in range(36, 40):
    # The warning is ~700 characters across 8 columns: about five rendered lines.
    # Four default 15pt rows is 60pt and clips it mid-sentence, which reads as a
    # broken sheet. Give it room.
    ws.row_dimensions[row].height = 24
    for col in range(1, 9):
        ws.cell(row=row, column=col).fill = __import__("openpyxl").styles.PatternFill("solid", fgColor="FEE2E2")

# The same warning belongs on both platform dashboards -- they carry the same
# period-over-period comparison, so they carry the same attribution caveat.
from openpyxl.styles import Alignment, PatternFill
for tab in ("Meta Dashboard", "TikTok Dashboard"):
    ws = wb[tab]
    ws["A47"] = warn
    ws.merge_cells("A47:H50")
    ws["A47"].alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    ws["A47"].font = Font(name="Inter", size=10, bold=True, color="B91C1C")
    for row in range(47, 51):
        ws.row_dimensions[row].height = 24      # same clipping trap as A36
        for col in range(1, 9):
            ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor="FEE2E2")

# --- Start Here: stamp what this file actually is
ws = wb["Start Here"]
ws["B2"] = "GOFRESH — Reporting Dashboard"
ws["B3"] = f"LIVE DATA from GOFRESH - Raw Data   ·   {CUR_START} to {CUR_END} vs {CMP_START} to {CMP_END}   ·   built {dt.date.today()}"
ws["C6"] = "GOFRESH"
ws["C7"] = "Media Buyer Ops"
ws["C8"] = CUR

wb.active = 0
wb.save(OUT)
print("\nwrote", OUT)
print(f"  Fundamentals rows: {len(fund)}")
print(f"  Ad Data rows:      {len(ads)}   (duplicate ad-days dropped: {DUPLICATE_AD_ROWS_REMOVED}, newest pull kept)")
print(f"  Ad Performance:    live QUERY will rank {len(by_ad)} ad names "
      f"in-period; top spender is {top[0][0][1]!r} at {top[0][1]['spend']:,.0f} EGP")
print(f"  _Control stamped:  {BRAND_NAME}, {len(ads)} rows, period {CUR_START}..{CUR_END}")
print(f"  Meta LPV filled:   {filled} of {len([f for f in fund if f[1]=='Meta'])} Meta days")
