"""
Builds 01_Google_Sheets_Reporting_Dashboard.xlsx

Tabs: Start Here · Fundamentals · Ad Data · KPI Calc · Dashboard ·
      Ad Performance · Benchmarks · Health Check

Live formulas throughout — change the two date cells and the whole dashboard moves.

Run:  python3 "_build/build_dashboard.py"
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openpyxl import Workbook
from openpyxl.utils import get_column_letter as L
from openpyxl.formatting.rule import FormulaRule, CellIsRule, ColorScaleRule
from openpyxl.styles import Font, Alignment

from kitstyle import *
from kitstyle import CURRENCY_CODE as CUR
import sample_data as SD

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "01_Google_Sheets_Reporting_Dashboard.xlsx")
M, M0 = money(), money0()

FUND = "Fundamentals"
AD   = "Ad Data"
KC   = "KPI Calc"
LROWS = 6000          # formula range depth


# ------------------------------------------------------------------ helpers
def S(col, sr="$B$4", er="$C$4", plat=None):
    """SUMIFS over Fundamentals for a column letter, bounded by the period cells."""
    f = (f'SUMIFS({FUND}!${col}$2:${col}${LROWS},{FUND}!$A$2:$A${LROWS},">="&{{SR}},'
         f'{FUND}!$A$2:$A${LROWS},"<="&{{ER}}')
    if plat:
        f += f',{FUND}!$B$2:$B${LROWS},"{plat}"'
    f += ")"
    return f.replace("{SR}", sr).replace("{ER}", er)


def SA(col, adcell, sr=f"'{KC}'!$B$4", er=f"'{KC}'!$C$4"):
    """SUMIFS over Ad Data for one ad name (col C) bounded by the KPI Calc period."""
    return (f"SUMIFS('{AD}'!${col}$2:${col}${LROWS},'{AD}'!$C$2:$C${LROWS},{adcell},"
            f"'{AD}'!$A$2:$A${LROWS},\">=\"&{sr},'{AD}'!$A$2:$A${LROWS},\"<=\"&{er})")


def period_label(sr, er):
    return f'TEXT({sr},"yyyy-mm-dd")&" → "&TEXT({er},"yyyy-mm-dd")'


# =============================================================== START HERE
def sheet_start(wb):
    ws = wb.create_sheet("Start Here")
    gridlines_off(ws)
    std_widths(ws, {"A": 3, "B": 30, "C": 100, "D": 3})

    put(ws, "B2", "Client Reporting Dashboard", f_title(18))
    put(ws, "B3", "The live view. Set four cells, get the whole picture.", f_italic(10))

    r = 5
    section_bar(ws, r, 2, 3, "  IDENTITY  —  these feed the titles on the Dashboard")
    r += 1
    for lab, val, fmt in [("Client / brand name", SD.BRAND, None),
                          ("Prepared by", SD.PREPARED_BY, None),
                          ("Currency code", CUR, None)]:
        put(ws, f"B{r}", lab, f_h2(10), align=A_LI)
        put(ws, f"C{r}", val, f_input(10), F_INPUT, fmt=fmt, align=A_LI, border=B_INPUT)
        r += 1
    r += 1

    section_bar(ws, r, 2, 3, "  HOW TO USE IT")
    r += 1
    steps = [
        ("1", "Set the period", "Open KPI Calc. In row 4 put the period you're reporting. In row 5 put what you're comparing it to. Everything else moves."),
        ("2", "Fill the business inputs", "KPI Calc, cells J5:J7 — COGS %, other variable cost %, and shipping per order. Without these the dashboard can show revenue but not profit."),
        ("3", "Feed the data", "Paste into Fundamentals (account level) and Ad Data (ad level). Column order matters — don't insert or reorder columns. See 'Link the Automation' below to skip the pasting entirely."),
        ("4", "Read the Dashboard", "That tab is the client-facing view. Tiles, platform split, funnel, and auto-written commentary you can paste straight into an email."),
        ("5", "Check Health Check first", "Before anything goes to a client. It proves the ad-level data reconciles to the account-level data and flags impossible numbers."),
        ("6", "Retune Benchmarks", "The status column is only as good as the thresholds. Put this client's own trailing 90-day numbers in after month two."),
    ]
    for n, t, d in steps:
        put(ws, f"B{r}", n, Font(name="Inter", size=13, bold=True, color=ACCENT))
        put(ws, f"C{r}", t, f_h2(10), align=A_LW)
        put(ws, f"C{r+1}", d, f_small(9), align=A_LW)
        ws.row_dimensions[r].height = 15
        ws.row_dimensions[r + 1].height = 28
        r += 2

    r += 1
    section_bar(ws, r, 2, 3, "  LINK THE AUTOMATION  —  if you run the n8n Ads Reporting System")
    r += 1
    put(ws, f"B{r}", "Why this is optional", f_h2(10), align=A_LI)
    put(ws, f"C{r}", "This kit works entirely by hand. But if you already run the automated pipeline, the Raw Data "
                     "sheet is the single source of truth — and the dashboard can read straight from it, so you "
                     "never paste anything.", f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 30
    r += 1

    put(ws, f"B{r}", "Step 1", f_h2(10), align=A_LI)
    put(ws, f"C{r}", "On the 'Fundamentals' tab, put your Raw Data sheet ID in cell N1. (It's the long string in the "
                     "Raw sheet's URL between /d/ and /edit.) Then delete the sample rows 2 onward.", f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 28
    r += 1
    put(ws, f"B{r}", "Step 2", f_h2(10), align=A_LI)
    put(ws, f"C{r}", "Paste this into Fundamentals!A2 — one formula, and the whole tab fills itself from the pipeline. "
                     "It stacks the four raw tabs, keeps the columns this kit needs, and labels each platform. "
                     "Approve the IMPORTRANGE access prompt the first time.", f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 30
    r += 1

    # ------------------------------------------------------------------
    # The pipeline link.
    #
    # Column mapping, verified against the n8n "ONE-OFF Template Prep" headers:
    #   Daily_Raw_Meta   (A:P) -> Date 1, Spend 2, Impr 3, Reach 4, Clicks 7,
    #                             ATC 9, IC 10, Purchases 11, Purchases_Value 12
    #   Daily_Raw_TikTok (A:R) -> Date 1, Spend 2, Impr 3, Reach 4, Clicks 6,
    #                             ATC 11, IC 12, Purchases 13, Purchases_Value 14
    #
    # Landing Page Views exist only on Daily_Raw_Meta_Ads (column N). They are
    # never on the Meta account-level tab and never on TikTok at all, so the
    # slot is emitted blank here and an optional formula below fills it in.
    #
    # Every HSTACK emits exactly 11 columns, matching the 11-column header row.
    # ------------------------------------------------------------------
    def clean(tab, rng):
        return ('QUERY(IMPORTRANGE($N$1,"\'Daily_Raw_%s\'!%s"),'
                '"select * where Col1 is not null",0)' % (tab, rng))

    def hstack(var, plat, picks_a, picks_b):
        return ("HSTACK("
                "CHOOSECOLS(%(v)s,1),"                                    # Date
                'IF(CHOOSECOLS(%(v)s,1)<>"","%(p)s",""),'                 # Platform
                "CHOOSECOLS(%(v)s,%(a)s),"                                # Spend, Impr, Reach, Clicks
                'IF(CHOOSECOLS(%(v)s,1)<>"","",""),'                      # Landing Page Views
                "CHOOSECOLS(%(v)s,%(b)s))"                                # ATC, IC, Purchases, Revenue
                % dict(v=var, p=plat, a=picks_a, b=picks_b))

    HDR = ('{"Date","Platform","Spend","Impressions","Reach","Clicks",'
           '"Landing Page Views","Add to Cart","Initiate Checkout","Purchases","Revenue"}')

    stack = ("=LET(\n"
             "  m, %s,\n"
             "  t, %s,\n"
             "  VSTACK(\n"
             "    %s,\n"
             "    %s,\n"
             "    %s\n"
             "  )\n"
             ")" % (clean("Meta", "A2:P"), clean("TikTok", "A2:R"),
                    HDR,
                    hstack("m", "Meta", "2,3,4,7", "9,10,11,12"),
                    hstack("t", "TikTok", "2,3,4,6", "11,12,13,14")))

    put(ws, f"B{r}", "Formula  ▸  copy this whole cell  (optional)", f_h2(10), align=A_LI)
    c = put(ws, f"C{r}", stack, Font(name="Consolas", size=8.5, color=INK), F_PANEL, align=A_LW,
            literal=True)
    autofit_row(ws, f"C{r}", stack)
    r += 1
    put(ws, f"B{r}", "Note", f_small(9), align=A_LI)
    put(ws, f"C{r}", "Google Sheets only — IMPORTRANGE does not exist in Excel, even Excel 365. In Excel, use "
                     "Power Query against the sheet instead, or just paste. Use this formula on ONE line: "
                     "Sheets accepts the line breaks, but if you paste from a PDF or chat window they can turn "
                     "into characters that break it, so delete any line break that isn't a real newline.",
        f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 40
    r += 1

    put(ws, f"B{r}", "Column mapping", f_small(9), align=A_LI)
    put(ws, f"C{r}", "Daily_Raw_Meta (A:P) gives Date, Spend, Impressions, Reach, Clicks, Adds_to_Cart, "
                     "Initiate_Checkout, Purchases, Purchases_Value. Daily_Raw_TikTok (A:R) gives the same, one "
                     "column apart. The formula maps them explicitly, so if your template ever gains a column, "
                     "the mapping is the thing to re-check — not the whole dashboard.",
        f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 40
    r += 1

    put(ws, f"B{r}", "About landing page views", f_small(9), align=A_LI)
    put(ws, f"C{r}", "Landing Page Views are left blank by the formula above, on purpose. Meta only reports LPV at "
                     "AD level, not account level, and TikTok does not report it at all. If you want the Meta "
                     "click-to-landing-page rate, put this in Fundamentals!G2 instead of the blank column — it sums "
                     "Daily_Raw_Meta_Ads by date:",
        f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 44
    r += 1

    lpv = ("=ARRAYFORMULA(IF($A$2:$A=\"\",\"\",\n"
           "  SUMIF(IMPORTRANGE($N$1,\"'Daily_Raw_Meta_Ads'!A$2:A\"),$A$2:$A,\n"
           "        IMPORTRANGE($N$1,\"'Daily_Raw_Meta_Ads'!N$2:N\"))))")
    put(ws, f"B{r}", "LPV formula", f_small(9), align=A_LI)
    put(ws, f"C{r}", lpv, Font(name="Consolas", size=8.5, color=INK_SOFT), F_PANEL, align=A_LW,
        literal=True)
    autofit_row(ws, f"C{r}", lpv)
    r += 1

    put(ws, f"B{r}", "If the numbers look wrong", f_small(9), align=A_LI)
    put(ws, f"C{r}", "Two things cause almost every problem. (1) Column A must be a real date, not text — select it "
                     "and check Format ▸ Number ▸ Date shows something sensible. If it is text, the date filters "
                     "silently return zero. (2) You must approve the IMPORTRANGE access prompt — the first paste "
                     "shows a #REF! and a button, and it only works after you click Allow. Run Health Check "
                     "afterwards: it reports the row count and first/last date, which tells you immediately whether "
                     "the link worked.",
        f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 56

    ws.row_dimensions[r].height = 44
    return ws


# ============================================================== FUNDAMENTALS
def sheet_fundamentals(wb):
    ws = wb.create_sheet(FUND)
    std_widths(ws, {"A": 12, "B": 11, "C": 13, "D": 13, "E": 12, "F": 11, "G": 18,
                    "H": 12, "I": 16, "J": 11, "K": 14, "M": 34, "N": 46})

    hdr = ["Date", "Platform", "Spend", "Impressions", "Reach", "Clicks",
           "Landing Page Views", "Add to Cart", "Initiate Checkout", "Purchases", "Revenue"]
    fmts = [F_DATE, None, M, F_INT, F_INT, F_INT, F_INT, F_INT, F_INT, F_INT, M]
    for i, (h, f) in enumerate(zip(hdr, fmts)):
        put(ws, f"{L(1+i)}1", h, Font(name="Inter", size=9.5, bold=True, color=WHITE), F_SECTION,
            fmt=f, align=A_C)
    ws.row_dimensions[1].height = 26

    for i, row in enumerate(SD.fundamentals_rows()):
        for j, v in enumerate(row):
            ws.cell(row=2 + i, column=1 + j).value = v
    last = 1 + len(SD.fundamentals_rows())

    for r in range(2, last + 1):
        ws.cell(row=r, column=1).number_format = F_DATE
        for c in (3, 11):
            ws.cell(row=r, column=c).number_format = M
        for c in (4, 5, 6, 7, 8, 9, 10):
            ws.cell(row=r, column=c).number_format = F_INT

    # side notes (row 1, off to the right so they never collide with automation)
    put(ws, "M1", "Raw Data sheet ID  →", f_h2(9.5), align=A_LI)
    put(ws, "N1", "", f_input(9), F_INPUT, align=A_LI, border=B_INPUT)
    put(ws, "M2", "Paste it here if you want to pull straight from the n8n pipeline "
                  "(see 'Start Here'). Otherwise ignore this cell.", f_tiny(8), align=A_LW)
    ws.merge_cells("M2:N3")
    ws["M2"].alignment = A_LW

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:K{last}"
    return ws


# =================================================================== AD DATA
def sheet_ad_data(wb):
    ws = wb.create_sheet(AD)
    std_widths(ws, {"A": 12, "B": 10, "C": 34, "D": 26, "E": 26, "F": 24,
                    "G": 12, "H": 13, "I": 11, "J": 11, "K": 14})

    hdr = ["Date", "Platform", "Ad Name", "Campaign", "Ad Group / Ad Set",
           "Creative Key", "Spend", "Impressions", "Clicks", "Purchases", "Revenue"]
    fmts = [F_DATE, None, None, None, None, None, M, F_INT, F_INT, F_INT, M]
    for i, (h, f) in enumerate(zip(hdr, fmts)):
        put(ws, f"{L(1+i)}1", h, Font(name="Inter", size=9.5, bold=True, color=WHITE), F_SECTION,
            fmt=f, align=A_C)
    ws.row_dimensions[1].height = 26

    rows = SD.ad_rows(SD.fundamentals_rows())
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = ws.cell(row=2 + i, column=1 + j)
            c.value = v
            if j == 0: c.number_format = F_DATE
            elif j == 6 or j == 10: c.number_format = M
            elif j in (7, 8, 9): c.number_format = F_INT
    last = 1 + len(rows)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:K{last}"
    return ws


# =================================================================== KPI CALC
def sheet_kpi_calc(wb):
    ws = wb.create_sheet(KC)
    gridlines_off(ws)
    std_widths(ws, {"A": 38, "B": 16, "C": 16, "D": 14, "E": 12, "F": 12, "G": 54,
                    "H": 3, "I": 32, "J": 14})

    title_block(ws, "KPI Calculator  —  live", "Every number recalculates from Fundamentals. Change the four date cells and the whole kit follows.", CUR, last_col=7)

    # period controls
    put(ws, "A4", "Current period", f_h2(10), align=A_LI)
    put(ws, "B4", SD.CUR_START, f_input(10), F_INPUT, fmt=F_DATE, align=A_C, border=B_INPUT)
    put(ws, "C4", SD.CUR_END,   f_input(10), F_INPUT, fmt=F_DATE, align=A_C, border=B_INPUT)
    put(ws, "A5", "Compare against", f_h2(10), align=A_LI)
    put(ws, "B5", SD.CMP_START, f_input(10), F_INPUT, fmt=F_DATE, align=A_C, border=B_INPUT)
    put(ws, "C5", SD.CMP_END,   f_input(10), F_INPUT, fmt=F_DATE, align=A_C, border=B_INPUT)

    # business inputs
    section_bar(ws, 4, 9, 10, "  BUSINESS INPUTS")
    ws.merge_cells("I4:J4")
    inputs = [("COGS % of revenue", SD.COGS_PCT, F_PCT),
              ("Other variable cost % of revenue", SD.OTHER_VAR_PCT, F_PCT),
              ("Shipping & fulfilment per order", SD.SHIP_PER_ORDER, M)]
    for i, (lab, v, fmt) in enumerate(inputs):
        r = 5 + i
        put(ws, f"I{r}", lab, f_body(9.5), align=A_LI)
        put(ws, f"J{r}", v, f_input(10), F_INPUT, fmt=fmt, align=A_C, border=B_INPUT)
    put(ws, "I8", "Ask the client for these three. Everything about profit depends on them.", f_tiny(8), align=A_LW)
    ws.merge_cells("I8:J9")
    ws["I8"].alignment = A_LW

    section_bar(ws, 7, 1, 7, "  PERIOD RESULTS  —  current versus comparison")
    for i, h in enumerate(["Metric", "Current", "Compare", "Change", "Δ %", "Status", "How to read it"]):
        put(ws, f"{L(1+i)}8", h, f_h2(9.5), F_HEAD, align=A_LI if i in (0, 6) else A_C)

    cur, cmp_ = "$B$4", "$B$5"
    endc, endp = "$C$4", "$C$5"

    # (row, label, col, fmt, note, better)  better: 'up' | 'down' | None
    metrics = [
        (9,  "Ad spend",                     "C", M,        "Media only — exclude your fee", "down"),
        (10, "Impressions",                  "D", F_INT,    "Volume of attention bought", "up"),
        (11, "Reach (sum of daily)",         "E", F_INT,    "Indicative — daily reach does not deduplicate across days", "up"),
        (12, "Clicks",                       "F", F_INT,    "Use link / outbound clicks only", "up"),
        (13, "Landing page views",           "G", F_INT,    "Meta only — TikTok does not report LPV", "up"),
        (14, "Add to cart",                  "H", F_INT,    "Cheap early intent", "up"),
        (15, "Initiate checkout",            "I", F_INT,    "Last step before money moves", "up"),
        (16, "Purchases",                    "J", F_INT,    "Platform-attributed orders", "up"),
        (17, "Revenue",                      "K", M,        "Platform purchase value, not bank revenue", "up"),
    ]
    for r, lab, col, fmt, note, better in metrics:
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        put(ws, f"B{r}", f"={S(col, cur, endc)}", f_calc(10), fmt=fmt, align=A_R)
        put(ws, f"C{r}", f"={S(col, cmp_, endp)}", f_calc(10), fmt=fmt, align=A_R)
        put(ws, f"D{r}", f"=B{r}-C{r}", f_calc(9.5), fmt=fmt, align=A_R)
        put(ws, f"E{r}", f"=IFERROR(B{r}/C{r}-1,0)", f_calc(9.5), fmt=F_PCT, align=A_R)
        put(ws, f"F{r}", None, f_calc(9), align=A_C)
        put(ws, f"G{r}", note, f_small(8.5), align=A_LI)

    derived = [
        (19, "CPM",                           f"=IFERROR(B9/B10*1000,0)",  M,        "Cost of 1,000 impressions", "down"),
        (20, "CPC",                           f"=IFERROR(B9/B12,0)",      M,        "Cost of a link click", "down"),
        (21, "CTR",                           f"=IFERROR(B12/B10,0)",     F_PCT,    "Creative hook strength", "up"),
        (22, "Frequency",                     f"=IFERROR(B10/B11,0)",     F_2D,     "Impressions per person. Above 3.5, refresh creative", "down"),
        (23, "Click → Add to cart %",         f"=IFERROR(B14/B12,0)",     F_PCT,    "Across both platforms", "up"),
        (24, "Add to cart → Checkout %",      f"=IFERROR(B15/B14,0)",     F_PCT,    "Shipping cost and fees show up here", "up"),
        (25, "Checkout → Purchase %",         f"=IFERROR(B16/B15,0)",     F_PCT,    "Payment options and trust", "up"),
        (26, "Click → Purchase CVR %",        f"=IFERROR(B16/B12,0)",     F_PCT,    "End-to-end site conversion on paid clicks", "up"),
        (27, "Click → Landing page % (Meta)", f"=IFERROR({S('G')}/{S('F', plat='Meta')},0)", F_PCT, "Page-speed diagnostic. Below 60% is a technical problem", "up"),
        (28, "Cost per purchase",             f"=IFERROR(B9/B16,0)",      M,        "Always read beside AOV", "down"),
        (29, "AOV",                           f"=IFERROR(B17/B16,0)",     M,        "Average order value", "up"),
        (30, "ROAS",                          f"=IFERROR(B17/B9,0)",      F_RATIO4, "Meaningless without breakeven ROAS", "up"),
        (31, "Revenue per 1,000 impressions", f"=IFERROR(B17/B10*1000,0)",M,        "Cleanest single measure of media efficiency", "up"),
        (33, "Contribution margin %",         "=IFERROR(1-$J$5-$J$6-$J$7/B29,0)", F_PCT, "What's left from revenue to pay for ads", None),
        (34, "Contribution",                  "=IFERROR(B17*B33,0)",      M,        "Revenue minus all variable costs", None),
        (35, "BREAKEVEN ROAS",                "=IFERROR(1/B33,0)",        F_RATIO4, "Below this, every sale loses money", None),
        (36, "Profit after ad spend",         "=IFERROR(B34-B9,0)",       M,        "Contribution minus media", "up"),
        (37, "POAS (profit on ad spend)",     "=IFERROR(B36/B9,0)",       F_RATIO4, "Profit per unit of spend", "up"),
        (38, "Spend as % of revenue",         "=IFERROR(B9/B17,0)",       F_PCT,    "Share of revenue going back into ads", "down"),
    ]
    for r, lab, form, fmt, note, better in derived:
        strong = lab in ("ROAS", "BREAKEVEN ROAS", "Profit after ad spend")
        put(ws, f"A{r}", lab, f_h2(10) if strong else f_body(10),
            F_PANEL if strong else None, align=A_LI)
        put(ws, f"B{r}", form, f_input(10) if strong else f_calc(10),
            F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"C{r}", f"=IFERROR({form[1:].replace('B','C')},0)" if form.startswith("=") else None,
            f_calc(9.5), F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"D{r}", f"=B{r}-C{r}", f_calc(9.5), F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"E{r}", f"=IFERROR(B{r}/C{r}-1,0)", f_calc(9.5), F_PANEL if strong else None, fmt=F_PCT, align=A_R)
        put(ws, f"F{r}", None, f_calc(9), F_PANEL if strong else None, align=A_C)
        put(ws, f"G{r}", note, f_small(8.5), F_PANEL if strong else None, align=A_LI)

    # comparison column for derived metrics must recompute against the *compare* period
    import re as _re
    row_ref = _re.compile(r"(?<![\w$!])B(\d{1,2})(?!\d)")
    for r, lab, form, fmt, note, better in derived:
        if not form.startswith("="):
            continue
        inner = form[1:]
        if "SUMIFS" in inner:
            # swap the platform-qualified SUMIFS first: the plain one is a prefix of it
            inner = inner.replace(S('F', cur, endc, plat='Meta'), S('F', cmp_, endp, plat='Meta'))
            inner = inner.replace(S('G', cur, endc), S('G', cmp_, endp))
            inner = inner.replace(S('C', cur, endc), S('C', cmp_, endp))
            inner = inner.replace(S('D', cur, endc), S('D', cmp_, endp))
            inner = inner.replace(S('F', cur, endc), S('F', cmp_, endp))
        # then point the cross-row references at the Compare column
        inner = row_ref.sub(lambda m: "C" + m.group(1), inner)
        ws[f"C{r}"] = "=" + inner

    # status column reads straight out of Benchmarks (range G7:G21 -> index = row - 6)
    bmap = {19: 7, 20: 8, 21: 9, 22: 15, 23: 11, 24: 12, 25: 13, 26: 14,
            27: 10, 29: 16, 30: 18, 31: 17, 33: 21, 35: 19, 37: 20}
    for r, brow in bmap.items():
        ws[f"F{r}"] = f'=IFERROR(INDEX(Benchmarks!$G$7:$G$21,{brow - 6}),"—")'
    ws["F28"] = '="—"'   # cost per purchase has no fixed threshold; it depends on AOV

    # conditional colours on the % change column
    ws.conditional_formatting.add("E9:E38", CellIsRule(operator="lessThan", formula=["0"],
                                  font=Font(name="Inter", size=9.5, color=BAD)))
    ws.conditional_formatting.add("E9:E38", CellIsRule(operator="greaterThan", formula=["0"],
                                  font=Font(name="Inter", size=9.5, color=GOOD)))
    ws.conditional_formatting.add("F9:F38", FormulaRule(formula=['$F9="Weak"'],
                                  font=Font(name="Inter", size=9, bold=True, color=BAD), fill=F_BADBG))
    ws.conditional_formatting.add("F9:F38", FormulaRule(formula=['$F9="Strong"'],
                                  font=Font(name="Inter", size=9, bold=True, color=GOOD), fill=F_GOODBG))
    ws.conditional_formatting.add("F9:F38", FormulaRule(formula=['$F9="Watch"'],
                                  font=Font(name="Inter", size=9, bold=True, color=WARN), fill=F_WARNBG))

    r = 40
    ws.merge_cells(f"A{r}:G{r}")
    verdict_cell(ws, f"A{r}",
        '=IF(B16=0,"No purchases in this period — check the date cells and the platform attribution window.",'
        '"Spend "&TEXT(ROUND(B9,0),"#,##0")&" → revenue "&TEXT(ROUND(B17,0),"#,##0")&" ("&ROUND(B30,2)&"x ROAS) '
        'against a breakeven of "&ROUND(B35,2)&"x. "&IF(B30>=B35,"Profitable","Below breakeven — the account is losing money at this margin")&'
        '" · profit after ad spend "&TEXT(ROUND(B36,0),"#,##0")&" · POAS "&ROUND(B37,2)&"x.")',
        font=Font(name="Inter", size=10, bold=True, color=INK), fill_=F_ACCENTBG)
    for c in range(1, 8):
        ws.cell(row=r, column=c).fill = F_ACCENTBG
    ws.row_dimensions[r].height = 30
    ws.freeze_panes = "A9"
    return ws


# ================================================================= DASHBOARD
def sheet_dashboard(wb):
    ws = wb.create_sheet("Dashboard")
    gridlines_off(ws)
    std_widths(ws, {"A": 30, "B": 15, "C": 15, "D": 15, "E": 15, "F": 15, "G": 15, "H": 15})

    ws.merge_cells("A1:H1")
    put(ws, "A1", "='Start Here'!C6", f_title(20))
    ws.row_dimensions[1].height = 28
    ws.merge_cells("A2:H2")
    _pl_a = period_label("'KPI Calc'!$B$4", "'KPI Calc'!$C$4")
    _pl_b = period_label("'KPI Calc'!$B$5", "'KPI Calc'!$C$5")
    put(ws, "A2", "=" + _pl_a + '&"      vs      "&' + _pl_b, f_italic(10), align=A_L)
    ws.merge_cells("A3:H3")
    _cur = CUR
    put(ws, "A3", '="Prepared by "&\'Start Here\'!C7&"   ·   all amounts in ' + _cur + '"',
        f_small(9), align=A_L)

    # ---- KPI cards
    kpi_card(ws, 5, 1, "AD SPEND",   "='KPI Calc'!B9",  M, sub='="vs "&TEXT(\'KPI Calc\'!C9,"#,##0")&" last period"', span=2)
    kpi_card(ws, 5, 3, "REVENUE",    "='KPI Calc'!B17", M, sub='="vs "&TEXT(\'KPI Calc\'!C17,"#,##0")&" last period"', span=2)
    kpi_card(ws, 5, 5, "ROAS",       "='KPI Calc'!B30", F_RATIO4, sub='="breakeven "&ROUND(\'KPI Calc\'!B35,2)&"x"', span=2)
    kpi_card(ws, 5, 7, "PROFIT AFTER AD SPEND", "='KPI Calc'!B36", M,
             sub='="POAS "&ROUND(\'KPI Calc\'!B37,2)&"x"', span=2)

    kpi_card(ws, 9, 1, "PURCHASES",  "='KPI Calc'!B16", F_INT, sub='="vs "&TEXT(\'KPI Calc\'!C16,"#,##0")&" last period"', span=2)
    kpi_card(ws, 9, 3, "AOV",        "='KPI Calc'!B29", M,     sub='="vs "&TEXT(\'KPI Calc\'!C29,"#,##0")&" last period"', span=2)
    kpi_card(ws, 9, 5, "COST PER PURCHASE", "='KPI Calc'!B28", M, sub='="contribution/order "&TEXT(\'KPI Calc\'!B34/MAX(1,\'KPI Calc\'!B16),"#,##0")', span=2)
    kpi_card(ws, 9, 7, "REVENUE / 1,000 IMPRESSIONS", "='KPI Calc'!B31", M, sub='="CPM "&TEXT(\'KPI Calc\'!B19,"#,##0")', span=2)

    # ---- platform split
    section_bar(ws, 13, 1, 8, "  WHERE THE BUDGET WENT")
    for i, h in enumerate(["Platform", "Spend", "Revenue", "ROAS", "Purchases",
                           "Cost / purchase", "Share of spend", ""]):
        put(ws, f"{L(1+i)}14", h, f_h2(9), F_HEAD, align=A_C if i else A_LI)
    ws.merge_cells("G14:H14")

    for i, plat in enumerate(["Meta", "TikTok"]):
        r = 15 + i
        put(ws, f"A{r}", plat, f_h2(10), align=A_LI)
        put(ws, f"B{r}", f"={S('C', plat=plat)}", f_calc(10), fmt=M, align=A_C)
        put(ws, f"C{r}", f"={S('K', plat=plat)}", f_calc(10), fmt=M, align=A_C)
        put(ws, f"D{r}", f"=IFERROR(C{r}/B{r},0)", f_calc(10), fmt=F_RATIO4, align=A_C)
        put(ws, f"E{r}", f"={S('J', plat=plat)}", f_calc(10), fmt=F_INT, align=A_C)
        put(ws, f"F{r}", f"=IFERROR(B{r}/E{r},0)", f_calc(10), fmt=M, align=A_C)
        put(ws, f"G{r}", f"=IFERROR(B{r}/$B$17,0)", f_calc(10), fmt=F_PCT, align=A_C)
        put(ws, f"H{r}", f'=REPT("█",ROUND(14*IFERROR(B{r}/$B$17,0),0))',
            Font(name="Inter", size=9, color=ACCENT_DK), align=A_LI)

    put(ws, "A17", "Total", f_h2(10), F_PANEL, align=A_LI)
    put(ws, "B17", "=SUM(B15:B16)", f_calc(10), F_PANEL, fmt=M, align=A_C)
    put(ws, "C17", "=SUM(C15:C16)", f_calc(10), F_PANEL, fmt=M, align=A_C)
    put(ws, "D17", "=IFERROR(C17/B17,0)", f_calc(10), F_PANEL, fmt=F_RATIO4, align=A_C)
    put(ws, "E17", "=SUM(E15:E16)", f_calc(10), F_PANEL, fmt=F_INT, align=A_C)
    put(ws, "F17", "=IFERROR(B17/E17,0)", f_calc(10), F_PANEL, fmt=M, align=A_C)
    put(ws, "G17", "=IFERROR(B17/B17,0)", f_calc(10), F_PANEL, fmt=F_PCT, align=A_C)
    put(ws, "H17", "", f_calc(10), F_PANEL)

    # ---- funnel
    section_bar(ws, 19, 1, 8, "  THE FUNNEL  —  combined Meta + TikTok")
    for i, h in enumerate(["Step", "Count", "Step rate", "Target", "Status", "Bar", "", ""]):
        put(ws, f"{L(1+i)}20", h, f_h2(9), F_HEAD, align=A_C if i else A_LI)

    funnel = [
        ("Impressions",       "='KPI Calc'!B10", None,               None),
        ("Clicks",            "='KPI Calc'!B12", "='KPI Calc'!B21",  9),
        ("Add to cart",       "='KPI Calc'!B14", "='KPI Calc'!B23",  11),
        ("Initiate checkout", "='KPI Calc'!B15", "='KPI Calc'!B24",  12),
        ("Purchases",         "='KPI Calc'!B16", "='KPI Calc'!B25",  13),
    ]
    for i, (lab, cnt, rate, brow) in enumerate(funnel):
        r = 21 + i
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        put(ws, f"B{r}", cnt, f_calc(10), fmt=F_INT, align=A_C)
        if rate:
            put(ws, f"C{r}", rate, f_calc(10), fmt=F_PCT, align=A_C)
            put(ws, f"D{r}", f"=Benchmarks!$E${brow}", f_small(9), fmt=F_PCT, align=A_C)
            put(ws, f"E{r}", f'=IFERROR(INDEX(Benchmarks!$G$7:$G$21,{brow-6}),"")', f_calc(9), align=A_C)
            put(ws, f"F{r}", f'=REPT("█",ROUND(20*IFERROR(C{r},0),0))',
                Font(name="Inter", size=9, color=ACCENT_DK), align=A_LI)
        else:
            for col in "CDEF":
                put(ws, f"{col}{r}", None, f_small(9), align=A_C)

    # meta-only note
    r = 26
    put(ws, f"A{r}", "Meta click → landing page", f_body(9.5), align=A_LI)
    put(ws, f"B{r}", f"={S('G')}", f_calc(9.5), fmt=F_INT, align=A_C)
    put(ws, f"C{r}", "='KPI Calc'!B27", f_calc(9.5), fmt=F_PCT, align=A_C)
    put(ws, f"D{r}", "=Benchmarks!$E$10", f_small(9), fmt=F_PCT, align=A_C)
    put(ws, f"E{r}", '=IFERROR(INDEX(Benchmarks!$G$7:$G$21,4),"")', f_calc(9), align=A_C)
    put(ws, f"F{r}", '=REPT("█",ROUND(20*IFERROR(C26,0),0))',
        Font(name="Inter", size=9, color=ACCENT_DK), align=A_LI)
    put(ws, f"G{r}", "Meta only — TikTok doesn't report landing page views",
        f_tiny(8), align=A_LI)
    ws.merge_cells(f"G{r}:H{r}")

    # ---- auto commentary
    section_bar(ws, 28, 1, 8, "  WHAT TO SAY  —  generated from this period's numbers. Edit before you send.")
    notes = [
        '="Headline: we spent "&TEXT(ROUND(\'KPI Calc\'!B9,0),"#,##0")&" and returned "&TEXT(ROUND(\'KPI Calc\'!B17,0),"#,##0")&" '
        '("&ROUND(\'KPI Calc\'!B30,2)&"x). "&IF(\'KPI Calc\'!B30>=\'KPI Calc\'!B35,"That is above the "&ROUND(\'KPI Calc\'!B35,2)&"x breakeven, so media paid for itself this period.",'
        '"That is below the "&ROUND(\'KPI Calc\'!B35,2)&"x breakeven — media did not pay for itself this period and we need to talk about that directly.")',

        '="Movement: spend "&IF(\'KPI Calc\'!E9>=0,"up","down")&" "&TEXT(ABS(\'KPI Calc\'!E9),"0%")&" while revenue "&IF(\'KPI Calc\'!E17>=0,"rose","fell")&" "&TEXT(ABS(\'KPI Calc\'!E17),"0%")&", so ROAS "&IF(\'KPI Calc\'!B30>=\'KPI Calc\'!C30,"improved","slipped")&" from "&ROUND(\'KPI Calc\'!C30,2)&"x to "&ROUND(\'KPI Calc\'!B30,2)&"x. Costs per thousand impressions went from "&TEXT(ROUND(\'KPI Calc\'!C19,0),"#,##0")&" to "&TEXT(ROUND(\'KPI Calc\'!B19,0),"#,##0")&".",',

        '="Where the money went: "&TEXT(\'Dashboard\'!G15,"0%")&" of budget on Meta returning "&ROUND(\'Dashboard\'!D15,2)&"x, and "&TEXT(\'Dashboard\'!G16,"0%")&" on TikTok returning "&ROUND(\'Dashboard\'!D16,2)&"x. "&IF(\'Dashboard\'!D15>\'Dashboard\'!D16,"Meta is the more efficient channel this period.","TikTok is the more efficient channel this period.")',

        '="Efficiency read: CPM "&TEXT(ROUND(\'KPI Calc\'!B19,0),"#,##0")&", CTR "&TEXT(\'KPI Calc\'!B21,"0.00%")&", click-to-purchase "&TEXT(\'KPI Calc\'!B26,"0.00%")&", AOV "&TEXT(ROUND(\'KPI Calc\'!B29,0),"#,##0")&". '
        'Frequency is "&ROUND(\'KPI Calc\'!B22,2)&", "&IF(\'KPI Calc\'!B22>3.5,"which is high enough that creative fatigue is now a budget risk — fresh assets before we scale.","which leaves room to add budget without hitting fatigue.")',

        '="Cost per purchase is "&TEXT(ROUND(\'KPI Calc\'!B28,0),"#,##0")&" against an AOV of "&TEXT(ROUND(\'KPI Calc\'!B29,0),"#,##0")&". '
        'At a "&TEXT(\'KPI Calc\'!B33,"0.0%")&" contribution margin, breakeven ROAS is "&ROUND(\'KPI Calc\'!B35,2)&"x, and headroom before we hit it is roughly "&TEXT(ROUND(MAX(0,\'KPI Calc\'!B17*\'KPI Calc\'!B33-\'KPI Calc\'!B9),0),"#,##0")&" more in spend at today\'s efficiency.",',
    ]
    for i, t in enumerate(notes):
        r = 29 + i
        ws.merge_cells(f"A{r}:H{r}")
        verdict_cell(ws, f"A{r}", t, font=Font(name="Inter", size=9.5, color=INK_SOFT), fill_=F_ACCENTBG)
        for c in range(1, 9):
            ws.cell(row=r, column=c).fill = F_ACCENTBG
        ws.row_dimensions[r].height = 32

    ws.freeze_panes = "A5"
    return ws


# =========================================================== AD PERFORMANCE
def sheet_ad_performance(wb):
    ws = wb.create_sheet("Ad Performance")
    gridlines_off(ws)
    ws.sheet_view.showGridLines = False
    std_widths(ws, {"A": 34, "B": 10, "C": 26, "D": 22, "E": 13, "F": 12, "G": 11,
                    "H": 10, "I": 11, "J": 13, "K": 10, "L": 12, "M": 12, "N": 40})

    title_block(ws, "Ad Performance", "Ranked by spend. One row per ad name — edit column A when you paste your own data.", CUR, last_col=14)

    hdrs = ["Ad Name", "Platform", "Campaign", "Creative Key", "Spend", "Impressions",
            "Clicks", "CTR", "Purchases", "Revenue", "ROAS", "Cost / purchase", "AOV", "Verdict"]
    for i, h in enumerate(hdrs):
        put(ws, f"{L(1+i)}5", h, f_h2(9), F_HEAD, align=A_LI if i in (0, 2, 3, 13) else A_C)

    seen = set()
    roster = []
    for plat, name, camp, creative, _w, _e in SD.AD_ROSTER:
        if name in seen:
            continue
        seen.add(name)
        roster.append((plat, name, camp, creative))
    roster.append(("Meta", "", "", ""))          # one blank row for pasting

    for i, (plat, name, camp, creative) in enumerate(roster):
        r = 6 + i
        put(ws, f"A{r}", name, Font(name="Inter", size=9.5, bold=True, color=INK), align=A_LI)
        put(ws, f"B{r}", plat if name else None, f_small(9.5), align=A_C)
        put(ws, f"C{r}", camp, f_small(9), align=A_LI)
        put(ws, f"D{r}", creative, f_small(9), align=A_LI)
        if not name:
            continue
        put(ws, f"E{r}",  f"={SA('G', f'$A{r}')}", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"F{r}",  f"={SA('H', f'$A{r}')}", f_calc(9.5), fmt=F_INT, align=A_C)
        put(ws, f"G{r}",  f"={SA('I', f'$A{r}')}", f_calc(9.5), fmt=F_INT, align=A_C)
        put(ws, f"H{r}",  f"=IFERROR(G{r}/F{r},0)", f_calc(9.5), fmt=F_PCT, align=A_C)
        put(ws, f"I{r}",  f"={SA('J', f'$A{r}')}", f_calc(9.5), fmt=F_INT, align=A_C)
        put(ws, f"J{r}",  f"={SA('K', f'$A{r}')}", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"K{r}",  f"=IFERROR(J{r}/E{r},0)", Font(name="Inter", size=10, bold=True, color=INK), fmt=F_RATIO4, align=A_C)
        put(ws, f"L{r}",  f"=IFERROR(E{r}/I{r},0)", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"M{r}",  f"=IFERROR(J{r}/I{r},0)", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"N{r}",  f'=IF(E{r}=0,"No spend in period",'
                          f'IF(K{r}>=MAX(\'KPI Calc\'!$B$35*1.3,0.01),"Scale — put more budget here",'
                          f'IF(K{r}>=\'KPI Calc\'!$B$35,"Working — maintain and refresh creative",'
                          f'"Below breakeven — fix the page or cut it")))',
            f_small(9), align=A_LI)

    last = 5 + len(roster)
    ws.conditional_formatting.add(f"N6:N{last}", FormulaRule(formula=['ISNUMBER(SEARCH("Scale",$N6))'],
                                  font=Font(name="Inter", size=9, bold=True, color=GOOD), fill=F_GOODBG))
    ws.conditional_formatting.add(f"N6:N{last}", FormulaRule(formula=['ISNUMBER(SEARCH("Working",$N6))'],
                                  font=Font(name="Inter", size=9, bold=True, color=INFO), fill=F_INFOBG))
    ws.conditional_formatting.add(f"N6:N{last}", FormulaRule(formula=['ISNUMBER(SEARCH("Below breakeven",$N6))'],
                                  font=Font(name="Inter", size=9, bold=True, color=BAD), fill=F_BADBG))
    ws.conditional_formatting.add(f"K6:K{last}", ColorScaleRule(
        start_type="num", start_value=0, start_color="FEE2E2",
        mid_type="num", mid_value=2, mid_color="FEF3C7",
        end_type="num", end_value=5, end_color="DCFCE7"))
    ws.freeze_panes = "A6"
    return ws


# ================================================================ BENCHMARKS
def sheet_benchmarks(wb):
    ws = wb.create_sheet("Benchmarks")
    gridlines_off(ws)
    std_widths(ws, {"A": 30, "B": 13, "C": 11, "D": 11, "E": 11, "F": 11, "G": 12, "H": 62})

    title_block(ws, "Benchmarks", "These thresholds decide every Status column in the kit. Retune them per account.", CUR, last_col=8)
    put(ws, "A4", "⚠ The starting numbers below are placeholders so the status columns work on day one — they are not "
                  "industry truth. Replace them with this client's own trailing 90-day range by month three. "
                  "A benchmark you didn't measure is a guess, and clients can smell a guess.   •   Once you have "
                  "replaced them, type TUNED in cell B28 below so Health Check stops flagging this tab.",
        Font(name="Inter", size=9, bold=True, color=BAD), align=A_LW)
    ws.merge_cells("A4:H5")
    ws.row_dimensions[4].height = 20
    ws.row_dimensions[5].height = 18

    for i, h in enumerate(["Metric", "Your value", "Weak", "Watch", "Target", "Strong", "Status", "If it's below target, look here first"]):
        put(ws, f"{L(1+i)}6", h, f_h2(9), F_HEAD, align=A_LI if i in (0, 7) else A_C)

    rows = [
        ("CPM",                       "='KPI Calc'!B19", M,       "down", 140, 95, 72, 55,
         "Auction pressure, audience saturation, or broad targeting diluting the mix."),
        ("CPC",                       "='KPI Calc'!B20", M,       "down", 9, 6.5, 5, 3.5,
         "Mostly CPM plus CTR. If CPC is high but CTR is fine, look at placement and audience."),
        ("CTR",                       "='KPI Calc'!B21", F_PCT,   "up",   0.008, 0.012, 0.018, 0.028,
         "The creative hook — first 3 seconds of video, first line of primary text."),
        ("Meta click to landing page", "='KPI Calc'!B27", F_PCT,  "up",   0.45, 0.6, 0.72, 0.85,
         "Page speed and mobile load. A technical problem wearing a media costume."),
        ("Click to add to cart",      "='KPI Calc'!B23", F_PCT,   "up",   0.03, 0.055, 0.08, 0.13,
         "Product page: price positioning, imagery, reviews, delivery promise."),
        ("Add to cart to checkout",   "='KPI Calc'!B24", F_PCT,   "up",   0.18, 0.3, 0.45, 0.6,
         "Shipping cost, surprise fees, forced account creation."),
        ("Checkout to purchase",      "='KPI Calc'!B25", F_PCT,   "up",   0.35, 0.5, 0.65, 0.78,
         "Payment methods, cash on delivery, trust badges, retargeting coverage."),
        ("Click to purchase CVR",     "='KPI Calc'!B26", F_PCT,   "up",   0.008, 0.015, 0.025, 0.04,
         "End-to-end site conversion on paid clicks. Compare to this account's own history."),
        ("Frequency",                 "='KPI Calc'!B22", F_2D,    "down", 5.0, 3.5, 2.4, 1.5,
         "Creative fatigue. Above target, refresh assets before adding budget."),
        ("AOV",                       "='KPI Calc'!B29", M,       "up",   450, 550, 650, 800,
         "Placeholder ladder — replace with this account's own trailing range."),
        ("Revenue per 1,000 impressions", "='KPI Calc'!B31", M,   "up",   80, 120, 170, 250,
         "The cleanest single measure of end-to-end media efficiency."),
        ("ROAS",                      "='KPI Calc'!B30", F_RATIO4,"up",   1.5, 2.0, 2.6, 3.5,
         "Never set a target below breakeven ROAS. Weak here sits below breakeven on purpose."),
        ("Breakeven ROAS",            "='KPI Calc'!B35", F_RATIO4,"down", 3.0, 2.4, 2.0, 1.6,
         "Calculated from the client's own margin inputs. Do not overwrite this row."),
        ("POAS (profit on ad spend)", "='KPI Calc'!B37", F_RATIO4,"up",   0, 0.15, 0.35, 0.6,
         "Profit per unit of spend. The number to move once ROAS is acceptable."),
        ("Contribution margin %",     "='KPI Calc'!B33", F_PCT,   "up",   0.25, 0.35, 0.45, 0.55,
         "Driven by the client's cost inputs on KPI Calc, cells J5:J7."),
    ]
    for i, row in enumerate(rows):
        r = 7 + i
        lab, val, fmt, direction = row[0], row[1], row[2], row[3]
        weak, watch, target, strong, action = row[4], row[5], row[6], row[7], row[8]
        put(ws, f"A{r}", lab, f_body(9.5), align=A_LI)
        put(ws, f"B{r}", val, Font(name="Inter", size=10, bold=True, color=INK), fmt=fmt, align=A_C)
        for j, v in enumerate([weak, watch, target, strong]):
            put(ws, f"{L(3+j)}{r}", v, f_small(9), fmt=fmt, align=A_C)
        if direction == "up":
            f = (f'=IF($B{r}=0,"—",IF($B{r}>=F{r},"Strong",IF($B{r}>=E{r},"Target",'
                 f'IF($B{r}>=D{r},"Watch","Weak"))))')
        else:
            f = (f'=IF($B{r}=0,"—",IF($B{r}<=F{r},"Strong",IF($B{r}<=E{r},"Target",'
                 f'IF($B{r}<=D{r},"Watch","Weak"))))')
        put(ws, f"G{r}", f, f_calc(9), align=A_C)
        put(ws, f"H{r}", action, f_small(8.5), align=A_LI)

    rng = f"G7:G{6+len(rows)}"
    for tag, fnt, fl in [("Strong", Font(name="Inter", size=9, bold=True, color=GOOD), F_GOODBG),
                         ("Target", Font(name="Inter", size=9, bold=True, color=GOOD), F_GOODBG),
                         ("Watch",  Font(name="Inter", size=9, bold=True, color=WARN), F_WARNBG),
                         ("Weak",   Font(name="Inter", size=9, bold=True, color=BAD),  F_BADBG)]:
        ws.conditional_formatting.add(rng, FormulaRule(formula=[f'$G7="{tag}"'], font=fnt, fill=fl))

    r = 7 + len(rows) + 1
    put(ws, f"A{r}", "How status is decided", f_h1(10))
    put(ws, f"A{r+1}", "Higher is better (CTR, rates, AOV, ROAS, POAS): Strong ≥ F, Target ≥ E, Watch ≥ D, otherwise Weak.", f_small(9))
    put(ws, f"A{r+2}", "Lower is better (CPM, CPC, Frequency, Breakeven ROAS): the same ladder, mirrored.", f_small(9))

    # Machine-readable tuning flag. Health Check row 28 reads THIS cell, so the
    # nag disappears exactly when the user says the benchmarks are the client's own.
    put(ws, "A28", "Benchmarks tuning status", f_h2(10), align=A_LI)
    put(ws, "B28", "PLACEHOLDER", Font(name="Inter", size=10, bold=True, color=BAD), F_WARNBG, align=A_C)
    put(ws, "C28", "Type TUNED here once the thresholds above are this client's own 90-day numbers.", f_small(9), align=A_LI)
    return ws


# ============================================================== HEALTH CHECK
def sheet_health(wb):
    ws = wb.create_sheet("Health Check")
    gridlines_off(ws)
    std_widths(ws, {"A": 46, "B": 14, "C": 74, "D": 3, "E": 34, "F": 16})

    title_block(ws, "Health Check", "Run this before anything goes to a client. Data errors look exactly like performance problems.", None, last_col=6)

    # --- coverage
    section_bar(ws, 5, 1, 3, "  DATA COVERAGE")
    cov = [
        ("Rows in the current period",  f'=COUNTIFS({FUND}!$A$2:$A${LROWS},">="&\'KPI Calc\'!$B$4,{FUND}!$A$2:$A${LROWS},"<="&\'KPI Calc\'!$C$4)', F_INT,
         "Zero here means your date cells and your data don't overlap. Start here."),
        ("Distinct days present",       f'=SUMPRODUCT((COUNTIFS({FUND}!$A$2:$A${LROWS},{FUND}!$A$2:$A${LROWS},{FUND}!$A$2:$A${LROWS},">="&\'KPI Calc\'!$B$4,{FUND}!$A$2:$A${LROWS},"<="&\'KPI Calc\'!$C$4)>0)/COUNTIF({FUND}!$A$2:$A${LROWS},{FUND}!$A$2:$A${LROWS}&""))', F_INT,
         "Should roughly equal the days in your period, per platform."),
        ("Days in the period (calendar)", "='KPI Calc'!$C$4-'KPI Calc'!$B$4+1", F_INT,
         "Compare with the row above. A big gap means missing sync days."),
        ("First date in the data",      f"=IFERROR(MIN({FUND}!$A$2:$A${LROWS}),0)", F_DATE, "Sanity-check the year."),
        ("Last date in the data",       f"=IFERROR(MAX({FUND}!$A$2:$A${LROWS}),0)", F_DATE, "Should be yesterday or today if the pipeline is healthy."),
        ("Meta rows in period",         f'=COUNTIFS({FUND}!$A$2:$A${LROWS},">="&\'KPI Calc\'!$B$4,{FUND}!$A$2:$A${LROWS},"<="&\'KPI Calc\'!$C$4,{FUND}!$B$2:$B${LROWS},"Meta")', F_INT, ""),
        ("TikTok rows in period",       f'=COUNTIFS({FUND}!$A$2:$A${LROWS},">="&\'KPI Calc\'!$B$4,{FUND}!$A$2:$A${LROWS},"<="&\'KPI Calc\'!$C$4,{FUND}!$B$2:$B${LROWS},"TikTok")', F_INT, ""),
    ]
    for i, (lab, form, fmt, note) in enumerate(cov):
        r = 6 + i
        put(ws, f"A{r}", lab, f_body(9.5), align=A_LI)
        put(ws, f"B{r}", form, f_calc(10), fmt=fmt, align=A_C)
        put(ws, f"C{r}", note, f_small(8.5), align=A_LI)

    # --- checks
    section_bar(ws, 15, 1, 3, "  CHECKS  —  red means fix the DATA, not the campaign")
    put(ws, "A16", "Check", f_h2(9.5), F_HEAD, align=A_LI)
    put(ws, "B16", "Status", f_h2(9.5), F_HEAD, align=A_C)
    put(ws, "C16", "Why it matters", f_h2(9.5), F_HEAD, align=A_LI)

    KCc = "'KPI Calc'!"
    checks = [
        ("Data exists for the selected period",      f'=IF({KCc}$B$10>0,"OK","FIX")',
         "No impressions in the period means the date cells are wrong."),
        ("Clicks never exceed impressions",          f'=IF({KCc}$B$12>{KCc}$B$10,"FIX","OK")',
         "A clicks > impressions read almost always means the wrong click column was pulled."),
        ("Purchases never exceed clicks",            f'=IF({KCc}$B$16>{KCc}$B$12,"FIX","OK")',
         "Either a view-through-heavy attribution window or mismatched date ranges."),
        ("Add to cart never exceeds clicks",         f'=IF({KCc}$B$14>{KCc}$B$12,"CHECK","OK")',
         "Cross-platform ATC can exceed clicks if windows differ between platforms."),
        ("Reach never exceeds impressions",          f'=IF({KCc}$B$11>{KCc}$B$10,"FIX","OK")',
         "Reach is deduplicated, so this is a hard rule."),
        ("Revenue is present",                       f'=IF({KCc}$B$17<=0,"FIX","OK")',
         "Without purchase value there is no ROAS, no AOV and no story to tell."),
        ("Ad spend reconciles to ad-level spend",    f'=IF(ABS(SUMIFS(\'{AD}\'!$G$2:$G${LROWS},\'{AD}\'!$A$2:$A${LROWS},">="&{KCc}$B$4,\'{AD}\'!$A$2:$A${LROWS},"<="&{KCc}$C$4)-{KCc}$B$9)/MAX(1,{KCc}$B$9)>0.05,"CHECK","OK")',
         "Sums ad-level spend for the SAME dates as the period, then compares it with account-level spend. More than 5% apart means the ad-level export is incomplete."),
        ("Ad-level purchases reconcile",             f'=IF(ABS(SUMIFS(\'{AD}\'!$J$2:$J${LROWS},\'{AD}\'!$A$2:$A${LROWS},">="&{KCc}$B$4,\'{AD}\'!$A$2:$A${LROWS},"<="&{KCc}$C$4)-{KCc}$B$16)/MAX(1,{KCc}$B$16)>0.08,"CHECK","OK")',
         "Ad-level and account-level purchase counts should be close over the same dates."),
        ("Business inputs are filled in",            f'=IF(OR({KCc}$J$5<=0,{KCc}$J$7<=0),"FIX","OK")',
         "COGS % and shipping per order drive every profit number in the kit."),
        ("Contribution margin is plausible",         f'=IF(OR({KCc}$B$33<=0,{KCc}$B$33>=1),"CHECK","OK")',
         "A margin outside 0–100% means a cost input is wrong."),
        ("No blank platforms in Fundamentals",       f'=IF(SUMPRODUCT(({FUND}!$A$2:$A${LROWS}<>"")*({FUND}!$B$2:$B${LROWS}=""))>0,"CHECK","OK")',
         "Counts only rows that carry a date -- the empty rows below your data are normal and are ignored."),
        ("Benchmarks retuned for this account",      f'=IF(Benchmarks!$B$28="TUNED","OK","CHECK")',
         "The Benchmarks tab still holds the shipped placeholders. Replace them with this client's own range, then set Benchmarks!B28 to TUNED."),
    ]
    for i, (lab, form, why) in enumerate(checks):
        r = 17 + i
        put(ws, f"A{r}", lab, f_body(9.5), align=A_LI)
        put(ws, f"B{r}", form, Font(name="Inter", size=9.5, bold=True, color=INK), align=A_C)
        put(ws, f"C{r}", why, f_small(8.5), align=A_LI)

    rng = f"B17:B{16+len(checks)}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=["B17=\"FIX\""], font=Font(name="Inter", size=9.5, bold=True, color=BAD), fill=F_BADBG))
    ws.conditional_formatting.add(rng, FormulaRule(formula=["B17=\"CHECK\""], font=Font(name="Inter", size=9.5, bold=True, color=WARN), fill=F_WARNBG))
    ws.conditional_formatting.add(rng, FormulaRule(formula=["B17=\"OK\""], font=Font(name="Inter", size=9.5, bold=True, color=GOOD), fill=F_GOODBG))

    r = 17 + len(checks) + 1
    ws.merge_cells(f"A{r}:C{r}")
    verdict_cell(ws, f"A{r}",
        f'=IF(COUNTIF({rng},"FIX")>0,"⛔ "&COUNTIF({rng},"FIX")&" check(s) need fixing before you report these numbers.",'
        f'IF(COUNTIF({rng},"CHECK")>0,"⚠ "&COUNTIF({rng},"CHECK")&" thing(s) to verify. They are usually benign — but verify them.",'
        f'"✅ All "&COUNTA({rng})&" checks passed. This data is safe to report."))',
        font=Font(name="Inter", size=11, bold=True, color=INK), fill_=F_PANEL)
    for c in range(1, 4):
        ws.cell(row=r, column=c).fill = F_PANEL
    ws.row_dimensions[r].height = 28

    # --- glossary side panel
    section_bar(ws, 5, 5, 6, "  WHAT COUNTS AS 'GOOD'")
    put(ws, "E6", "There is no universal good CPM.", f_h2(9.5), align=A_LW)
    put(ws, "E7", "A CPM of 180 EGP is excellent for one category and fatal for another. The status column in this "
                  "file compares this account against thresholds you control — start with the placeholders, then "
                  "replace them with this client's own 90-day trailing range. That is the only benchmark that "
                  "survives a client asking \"compared to what?\"", f_small(9), align=A_LW)
    ws.merge_cells("E7:F20")
    ws["E7"].alignment = A_LW
    return ws


# =================================================================== BUILD
def build():
    wb = Workbook()
    wb.remove(wb.active)
    sheet_start(wb)
    sheet_fundamentals(wb)
    sheet_ad_data(wb)
    sheet_kpi_calc(wb)
    sheet_dashboard(wb)
    sheet_ad_performance(wb)
    sheet_benchmarks(wb)
    sheet_health(wb)
    wb.active = 0
    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
