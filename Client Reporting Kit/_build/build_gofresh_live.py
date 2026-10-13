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
# Meta: 1 Date, 3 Ad_Name, 4 AdSet_Name, 5 Campaign_Name, 6 Creative_Key,
#       7 Spend, 8 Impressions, 12 Clicks, 17 Purchases, 18 Purchases_Value
for r in range(2, meta_ads.max_row + 1):
    d = as_date(meta_ads.cell(r, 1).value)
    if not d:
        continue
    ads.append([d, "Meta",
                meta_ads.cell(r, 3).value, meta_ads.cell(r, 5).value, meta_ads.cell(r, 4).value,
                meta_ads.cell(r, 6).value,
                num(meta_ads.cell(r, 7).value), num(meta_ads.cell(r, 8).value),
                num(meta_ads.cell(r, 12).value), num(meta_ads.cell(r, 17).value),
                num(meta_ads.cell(r, 18).value)])

# TikTok: 1 Date, 3 Ad_Name, 4 Campaign_Name, 5 AdGroup_Name, 6 Creative_Key,
#         7 Spend, 8 Impressions, 11 Clicks, 17 Purchases, 18 Purchases_Value
for r in range(2, tt_ads.max_row + 1):
    d = as_date(tt_ads.cell(r, 1).value)
    if not d:
        continue
    ads.append([d, "TikTok",
                tt_ads.cell(r, 3).value, tt_ads.cell(r, 4).value, tt_ads.cell(r, 5).value,
                tt_ads.cell(r, 6).value,
                num(tt_ads.cell(r, 7).value), num(tt_ads.cell(r, 8).value),
                num(tt_ads.cell(r, 11).value), num(tt_ads.cell(r, 17).value),
                num(tt_ads.cell(r, 18).value)])

ads.sort(key=lambda x: (x[0], x[1]))

# ============================================================== period choice
# The pipeline's first day is 2026-10-01 and it ran at 03:09 on the 13th, so
# 10-12 and 10-13 are still filling in. Use 10-01..10-12, split into two equal
# six-day halves so the comparison is like-for-like.
all_dates = sorted({f[0] for f in fund})
first = all_dates[0]
usable_last = dt.date(2026, 10, 12)
USABLE = [d for d in all_dates if d <= usable_last]
half = len(USABLE) // 2
CMP_START, CMP_END = USABLE[0], USABLE[half - 1]
CUR_START, CUR_END = USABLE[half], USABLE[-1]

tot = lambda rows, s, e, p=None: sum(x[2] for x in rows if s <= x[0] <= e and (not p or x[1] == p))
rev = lambda rows, s, e: sum(x[10] for x in rows if s <= x[0] <= e)
sp = tot(fund, CUR_START, CUR_END)
rv = rev(fund, CUR_START, CUR_END)

print(f"GOFRESH data: {all_dates[0]} to {all_dates[-1]}  ({len(fund)} account rows, {len(ads)} ad rows)")
print(f"Oct 13 partial (pipeline ran 03:09) -- excluded; usable to {usable_last}")
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
ws["B4"], ws["C4"] = CUR_START, CUR_END
ws["B5"], ws["C5"] = CMP_START, CMP_END
for ref, fmt in (("B4", "yyyy-mm-dd"), ("C4", "yyyy-mm-dd"), ("B5", "yyyy-mm-dd"), ("C5", "yyyy-mm-dd")):
    ws[ref].number_format = fmt
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

ws = wb["Ad Performance"]
for r in range(6, ws.max_row + 1):
    for c in range(1, 15):
        ws.cell(r, c).value = None
for i, ((plat, name), info) in enumerate(top):
    r = 6 + i
    ws.cell(r, 1).value = name
    ws.cell(r, 2).value = plat
    ws.cell(r, 3).value = info["camp"]
    ws.cell(r, 4).value = info["ck"]
    ws.cell(r, 5).value = f"={('SUMIFS' if True else '')}('Ad Data'!$G$2:$G$6000,'Ad Data'!$C$2:$C$6000,$A{r},'Ad Data'!$A$2:$A$6000,\">=\"&'KPI Calc'!$B$4,'Ad Data'!$A$2:$A$6000,\"<=\"&'KPI Calc'!$C$4)"
    ws.cell(r, 6).value = f"=SUMIFS('Ad Data'!$H$2:$H$6000,'Ad Data'!$C$2:$C$6000,$A{r},'Ad Data'!$A$2:$A$6000,\">=\"&'KPI Calc'!$B$4,'Ad Data'!$A$2:$A$6000,\"<=\"&'KPI Calc'!$C$4)"
    ws.cell(r, 7).value = f"=SUMIFS('Ad Data'!$I$2:$I$6000,'Ad Data'!$C$2:$C$6000,$A{r},'Ad Data'!$A$2:$A$6000,\">=\"&'KPI Calc'!$B$4,'Ad Data'!$A$2:$A$6000,\"<=\"&'KPI Calc'!$C$4)"
    ws.cell(r, 8).value = f"=IFERROR(G{r}/F{r},0)"
    ws.cell(r, 9).value = f"=SUMIFS('Ad Data'!$J$2:$J$6000,'Ad Data'!$C$2:$C$6000,$A{r},'Ad Data'!$A$2:$A$6000,\">=\"&'KPI Calc'!$B$4,'Ad Data'!$A$2:$A$6000,\"<=\"&'KPI Calc'!$C$4)"
    ws.cell(r, 10).value = f"=SUMIFS('Ad Data'!$K$2:$K$6000,'Ad Data'!$C$2:$C$6000,$A{r},'Ad Data'!$A$2:$A$6000,\">=\"&'KPI Calc'!$B$4,'Ad Data'!$A$2:$A$6000,\"<=\"&'KPI Calc'!$C$4)"
    ws.cell(r, 11).value = f"=IFERROR(J{r}/E{r},0)"
    ws.cell(r, 12).value = f"=IFERROR(E{r}/I{r},0)"
    ws.cell(r, 13).value = f"=IFERROR(J{r}/I{r},0)"
    ws.cell(r, 14).value = (f'=IF(E{r}=0,"No spend in period",'
                            f'IF(K{r}>=MAX(\'KPI Calc\'!$B$35*1.3,0.01),"Scale — put more budget here",'
                            f'IF(K{r}>=\'KPI Calc\'!$B$35,"Working — maintain and refresh creative",'
                            f'"Below breakeven — fix the page or cut it")))')

# --- Dashboard: honest warning about attribution maturity
ws = wb["Dashboard"]
warn = (
    "READ THIS BEFORE ACTING ON THE COMPARISON. The current period is more recent than the comparison "
    "period, and Meta and TikTok keep attributing purchases for days after a click. On Oct 1 and Oct 2 "
    "GOFRESH recorded revenue with zero spend -- those were sales from September still landing. The same "
    "effect is working in reverse on the current period: its purchases are still arriving, so its ROAS and "
    "conversion rate are understated. Your pipeline already handles this by re-pulling a rolling 7-day "
    "window every night; the numbers will settle over the next week. Do not cut budget on this comparison yet."
)
ws["A36"] = warn
ws.merge_cells("A36:H39")
ws["A36"].alignment = __import__("openpyxl").styles.Alignment(horizontal="left", vertical="top", wrap_text=True)
ws["A36"].font = Font(name="Inter", size=10, bold=True, color="B91C1C")
ws["A36"].fill = __import__("openpyxl").styles.PatternFill("solid", fgColor="FEE2E2")
for row in range(36, 40):
    for col in range(1, 9):
        ws.cell(row=row, column=col).fill = __import__("openpyxl").styles.PatternFill("solid", fgColor="FEE2E2")

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
print(f"  Ad Data rows:      {len(ads)}")
print(f"  Top ads written:   {len(top)} (ranked on {CUR_START}..{CUR_END})")
print(f"  Meta LPV filled:   {filled} of {len([f for f in fund if f[1]=='Meta'])} Meta days")
