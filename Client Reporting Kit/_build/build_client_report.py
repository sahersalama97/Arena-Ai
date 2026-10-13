"""
Builds 02_Client_Report_Template.xlsx  —  the client-facing monthly report.

Tab names and metric rows mirror the n8n Ads Reporting System output, so you can
copy a block straight out of the automation's report sheet into `_Inputs` and the
whole report fills in.

Run:  python3 "_build/build_client_report.py"
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
                   "02_Client_Report_Template.xlsx")
M, M0 = money(), money0()
IN = "_Inputs"                     # internal tab holding every number


# ------------------------------------------------------------ sample figures
# All sample numbers come from _build/sample_data.py, which is also what builds the
# Dashboard and the KPI Calculator — so the three files never disagree.
ROWS     = SD.fundamentals_rows()
ADROWS   = SD.ad_rows(ROWS)
cur_all  = SD.derive(SD.totals(ROWS, SD.CUR_START, SD.CUR_END))
cur_meta = SD.derive(SD.totals(ROWS, SD.CUR_START, SD.CUR_END, "Meta"))
cur_tt   = SD.derive(SD.totals(ROWS, SD.CUR_START, SD.CUR_END, "TikTok"))
prv_meta = SD.derive(SD.totals(ROWS, SD.CMP_START, SD.CMP_END, "Meta"))
prv_tt   = SD.derive(SD.totals(ROWS, SD.CMP_START, SD.CMP_END, "TikTok"))
prv_all  = SD.derive(SD.totals(ROWS, SD.CMP_START, SD.CMP_END))
BREAKEVEN = SD.breakeven_roas(cur_all["aov"])

PERIOD_LABEL = "September 2026"
COMPARE_LABEL = "August 2026"


# ================================================================ _INPUTS
def sheet_inputs(wb):
    ws = wb.create_sheet(IN)
    gridlines_off(ws)
    std_widths(ws, {"A": 40, "B": 18, "C": 18, "D": 18, "E": 3, "F": 76})

    put(ws, "A1", "INTERNAL — this tab holds every number in the report. Do not send it to the client.",
        Font(name="Inter", size=11, bold=True, color=BAD))
    ws.merge_cells("A1:F1")

    put(ws, "A2", "Paste from the automation's report sheet, or type your platform numbers. Every other tab reads from here.",
        f_small(9))
    ws.merge_cells("A2:F2")

    # ---- cover block
    section_bar(ws, 4, 1, 4, "  COVER DETAILS")
    cover = [
        ("Client / brand name", SD.BRAND, None),          # B5
        ("Reporting period", PERIOD_LABEL, None),         # B6
        ("Compared against", COMPARE_LABEL, None),        # B7
        ("Prepared by", SD.PREPARED_BY, None),            # B8
        ("Report date", SD.DATA_END, F_DATE),             # B9
        ("Currency", CUR, None),                          # B10
    ]
    for i, (lab, v, fmt) in enumerate(cover):
        r = 5 + i
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        put(ws, f"B{r}", v, f_input(10), F_INPUT, fmt=fmt, align=A_LI, border=B_INPUT)
        ws.merge_cells(f"B{r}:D{r}")

    # ---- combined (mirrors the pipeline 'Combined' tab row for row)
    section_bar(ws, 11, 1, 4, "  COMBINED  —  mirrors the automation's 'Combined' tab")
    for i, h in enumerate(["Metric", "Meta", "TikTok", "Combined"]):
        put(ws, f"{L(1+i)}12", h, f_h2(9.5), F_HEAD, align=A_LI if i == 0 else A_C)
    combined = [
        ("Spend",                 cur_meta["spend"], cur_tt["spend"], cur_all["spend"], M),
        ("Purchases",             cur_meta["pur"],   cur_tt["pur"],   cur_all["pur"],   F_INT),
        ("Cost Per Purchase",     cur_meta["cpp"],   cur_tt["cpp"],   cur_all["cpp"],   M),
        ("Purchases Value",       cur_meta["rev"],   cur_tt["rev"],   cur_all["rev"],   M),
        ("ROAS",                  cur_meta["roas"],  cur_tt["roas"],  cur_all["roas"],  F_RATIO4),
        ("AOV",                   cur_meta["aov"],   cur_tt["aov"],   cur_all["aov"],   M),
    ]
    for i, (lab, a, b, c, fmt) in enumerate(combined):
        r = 13 + i
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        for j, v in enumerate([a, b, c]):
            put(ws, f"{L(2+j)}{r}", round(v, 4), f_input(10), F_INPUT, fmt=fmt, align=A_C, border=B_INPUT)

    # ---- per-platform overviews
    meta_rows = [
        ("Spend",          cur_meta["spend"],  prv_meta["spend"],  M),
        ("Outbound CTR",   cur_meta["ctr"],    prv_meta["ctr"],    F_PCT),
        ("Impressions",    cur_meta["imp"],    prv_meta["imp"],    F_INT),
        ("Reach",          cur_meta["reach"],  prv_meta["reach"],  F_INT),
        ("Frequency",      cur_meta["freq"],   prv_meta["freq"],   F_2D),
        ("Adds to cart",   cur_meta["atc"],    prv_meta["atc"],    F_INT),
        ("Initiate Checkout", cur_meta["ic"],  prv_meta["ic"],     F_INT),
        ("Purchases",      cur_meta["pur"],    prv_meta["pur"],    F_INT),
        ("Cost Per Purchase", cur_meta["cpp"], prv_meta["cpp"],    M),
        ("Purchases Value", cur_meta["rev"],   prv_meta["rev"],    M),
        ("ROAS",           cur_meta["roas"],   prv_meta["roas"],   F_RATIO4),
        ("AOV",            cur_meta["aov"],    prv_meta["aov"],    M),
    ]
    section_bar(ws, 20, 1, 4, "  META OVERVIEW  —  mirrors the automation's 'Meta Overview' tab")
    for i, h in enumerate(["Metric", "This period", COMPARE_LABEL, ""]):
        put(ws, f"{L(1+i)}21", h, f_h2(9.5), F_HEAD, align=A_C if i else A_LI)
    for i, (lab, a, b, fmt) in enumerate(meta_rows):
        r = 22 + i
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        put(ws, f"B{r}", round(a, 4), f_input(10), F_INPUT, fmt=fmt, align=A_C, border=B_INPUT)
        put(ws, f"C{r}", round(b, 4), f_input(10), F_INPUT, fmt=fmt, align=A_C, border=B_INPUT)

    tt_rows = [
        ("Spend",          cur_tt["spend"],   prv_tt["spend"],   M),
        ("CPM",            cur_tt["cpm"],     prv_tt["cpm"],     M),
        ("CTR",            cur_tt["ctr"],     prv_tt["ctr"],     F_PCT),
        ("Impressions",    cur_tt["imp"],     prv_tt["imp"],     F_INT),
        ("Reach",          cur_tt["reach"],   prv_tt["reach"],   F_INT),
        ("Frequency",      cur_tt["freq"],    prv_tt["freq"],    F_2D),
        ("Adds to cart",   cur_tt["atc"],     prv_tt["atc"],     F_INT),
        ("Initiate Checkout", cur_tt["ic"],   prv_tt["ic"],      F_INT),
        ("Purchases",      cur_tt["pur"],     prv_tt["pur"],     F_INT),
        ("Cost Per Purchase", cur_tt["cpp"],  prv_tt["cpp"],     M),
        ("Purchases Value", cur_tt["rev"],    prv_tt["rev"],     M),
        ("ROAS",           cur_tt["roas"],    prv_tt["roas"],    F_RATIO4),
        ("AOV",            cur_tt["aov"],     prv_tt["aov"],     M),
    ]
    section_bar(ws, 36, 1, 4, "  TIKTOK OVERVIEW  —  mirrors the automation's 'TikTok Overview' tab")
    for i, h in enumerate(["Metric", "This period", COMPARE_LABEL, ""]):
        put(ws, f"{L(1+i)}37", h, f_h2(9.5), F_HEAD, align=A_C if i else A_LI)
    for i, (lab, a, b, fmt) in enumerate(tt_rows):
        r = 38 + i
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        put(ws, f"B{r}", round(a, 4), f_input(10), F_INPUT, fmt=fmt, align=A_C, border=B_INPUT)
        put(ws, f"C{r}", round(b, 4), f_input(10), F_INPUT, fmt=fmt, align=A_C, border=B_INPUT)

    # ---- the context only the media buyer can supply
    section_bar(ws, 53, 1, 4, "  CONTEXT  —  the numbers don't know these. You do.")
    ctx = [
        ("Breakeven ROAS",               round(BREAKEVEN, 2), F_RATIO4, "From the KPI Calculator. Say it out loud on every report."),
        ("Target ROAS",                   3.0, F_RATIO4, "What you and the client agreed."),
        ("What we changed this month",    "", None,     "e.g. Launched 4 new UGC concepts, cut the two weakest ad sets."),
        ("What we learned",               "", None,     "e.g. Founder-story creative beats product-only by 1.9x on ROAS."),
        ("What we're doing next month",   "", None,     "e.g. Scale the top creative to 40% of budget, test a bundle offer."),
        ("Anything the numbers don't show", "", None,   "e.g. Two shipping delays cut checkout completion in week 3. Stockout on the best SKU."),
        ("What we need from you",         "", None,     "e.g. New hero imagery for the bundle. Price decision on the 3-pack."),
    ]
    for i, (lab, v, fmt, hint) in enumerate(ctx):
        r = 54 + i
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        put(ws, f"B{r}", v, f_input(10), F_INPUT, fmt=fmt, align=A_LI, border=B_INPUT)
        ws.merge_cells(f"B{r}:D{r}")
        put(ws, f"F{r}", hint, f_tiny(8), align=A_LW)
    ws.row_dimensions[60].height = 30
    ws.row_dimensions[61].height = 30

    # ---- how to use
    section_bar(ws, 62, 1, 4, "  HOW TO BUILD THIS REPORT IN 10 MINUTES")
    steps = [
        "1 · Fill the COVER DETAILS block, then paste your spend, purchases and revenue into the COMBINED block — it mirrors the automation's Combined tab row for row.",
        "2 · Paste the platform overviews into the META and TIKTOK blocks. Copy the whole table from the automation's tabs; the metric names already match.",
        "3 · Fill CONTEXT. This is the part that makes the report yours. Six short lines.",
        "4 · Fill the Top Ads, Creatives and Weekly Trend blocks on those tabs, then open the AI prompts file and run the monthly narrative prompt on the whole thing.",
        "5 · Paste the AI output into 'What We Did / What's Next', edit for tone, then export to PDF (File ▸ Download ▸ PDF) and delete this tab's contents before you send anything.",
    ]
    for i, s in enumerate(steps):
        r = 63 + i
        put(ws, f"A{r}", s, f_small(9), align=A_LW)
        ws.merge_cells(f"A{r}:F{r}")
        ws.row_dimensions[r].height = 26
    return ws


# =================================================================== COVER
def sheet_cover(wb):
    ws = wb.create_sheet("Cover")
    gridlines_off(ws)
    std_widths(ws, {"A": 3, "B": 26, "C": 22, "D": 22, "E": 22, "F": 22, "G": 3})

    for r in range(1, 40):
        for c in "ABCDEFG":
            ws[f"{c}{r}"].fill = F_WHITE

    ws.merge_cells("B6:E6")
    put(ws, "B6", "MONTHLY PERFORMANCE REPORT", Font(name="Inter", size=10, bold=True, color=ACCENT))
    ws.merge_cells("B8:E8")
    put(ws, "B8", f"={IN}!$B$5", Font(name="Inter", size=30, bold=True, color=INK))
    ws.row_dimensions[8].height = 40
    ws.merge_cells("B10:E10")
    put(ws, "B10", f'={IN}!$B$6&"   ·   compared with "&{IN}!$B$7', Font(name="Inter", size=12, color=MUTED))
    ws.row_dimensions[10].height = 20

    ws.merge_cells("B13:E14")
    put(ws, "B13", f'="Prepared by "&{IN}!$B$8&"    ·    "&TEXT({IN}!$B$9,"yyyy-mm-dd")',
        f_body(10), align=A_LW)

    # headline strip
    tiles = [
        ("Spend",   f"={IN}!$D$13", M),
        ("Revenue", f"={IN}!$D$16", M),
        ("ROAS",    f"={IN}!$D$17", F_RATIO4),
        ("Purchases", f"={IN}!$D$14", F_INT),
    ]
    for i, (lab, form, fmt) in enumerate(tiles):
        col = L(2 + i)
        r = 18
        put(ws, f"{col}{r}", lab, Font(name="Inter", size=9, color=MUTED), F_PANEL,
            align=Alignment(horizontal="left", vertical="bottom", indent=1))
        put(ws, f"{col}{r+1}", form, Font(name="Inter", size=15, bold=True, color=INK), F_PANEL,
            fmt=fmt, align=Alignment(horizontal="left", vertical="center", indent=1))
        ws.row_dimensions[r].height = 16
        ws.row_dimensions[r+1].height = 24

    # cover commitment line
    ws.merge_cells("B22:E23")
    put(ws, "B22",
        f'="Every number in this report traces back to a daily row pulled directly from Meta\'s and TikTok\'s own '
        f'reporting APIs. Nothing here is typed in by hand, and nothing is estimated."',
        Font(name="Inter", size=9.5, italic=True, color=MUTED), align=A_LW)
    ws.merge_cells("B27:E27")
    put(ws, "B27", f'="Amounts in "&{IN}!$B$10&".   Reporting window "&{IN}!$B$6&"."',
        f_tiny(8.5), align=A_L)
    return ws


# ======================================================= EXECUTIVE SUMMARY
def sheet_exec(wb):
    ws = wb.create_sheet("Executive Summary")
    gridlines_off(ws)
    std_widths(ws, {"A": 34, "B": 16, "C": 16, "D": 16, "E": 16, "F": 16, "G": 16, "H": 16})

    put(ws, "A1", f"={IN}!$B$5", Font(name="Inter", size=17, bold=True, color=INK))
    put(ws, "A2", f'="Executive summary   ·   "&{IN}!$B$6&" compared with "&{IN}!$B$7',
        f_italic(9.5))

    section_bar(ws, 4, 1, 8, "  AT A GLANCE")
    tiles = [
        ("SPEND",             f"={IN}!$D$13", M,        f"=SUM({IN}!$C$22,{IN}!$C$38)",  True),
        ("REVENUE",           f"={IN}!$D$16", M,        f"=SUM({IN}!$C$31,{IN}!$C$48)",  True),
        ("ROAS",              f"={IN}!$D$17", F_RATIO4, f"=IFERROR(SUM({IN}!$C$31,{IN}!$C$48)/SUM({IN}!$C$22,{IN}!$C$38),0)", True),
        ("PURCHASES",         f"={IN}!$D$14", F_INT,    f"=SUM({IN}!$C$29,{IN}!$C$46)",  True),
        ("COST PER PURCHASE", f"={IN}!$D$15", M,        f"=IFERROR(SUM({IN}!$C$22,{IN}!$C$38)/SUM({IN}!$C$29,{IN}!$C$46),0)", True),
        ("AOV",               f"={IN}!$D$18", M,        f"=IFERROR(SUM({IN}!$C$31,{IN}!$C$48)/SUM({IN}!$C$29,{IN}!$C$46),0)", True),
    ]
    for i, (lab, form, fmt, prev, better_up) in enumerate(tiles):
        left = 1 + i
        ws.merge_cells(f"{L(left)}5:{L(left)}5")
        put(ws, f"{L(left)}5", lab, Font(name="Inter", size=8.5, bold=True, color=MUTED),
            F_PANEL, align=Alignment(horizontal="left", vertical="bottom", indent=1))
        put(ws, f"{L(left)}6", form, Font(name="Inter", size=14, bold=True, color=INK),
            F_PANEL, fmt=fmt, align=Alignment(horizontal="left", vertical="center", indent=1))
        put(ws, f"{L(left)}7", prev, f_tiny(8), F_PANEL, fmt=fmt,
            align=Alignment(horizontal="left", vertical="top", indent=1))
    ws.row_dimensions[5].height = 14
    ws.row_dimensions[6].height = 22
    ws.row_dimensions[7].height = 12

    # deltas
    put(ws, "A9", "Change vs " + COMPARE_LABEL, f_h2(10), F_HEAD, align=A_LI)
    for i in range(6):
        put(ws, f"{L(1+i)}9", "Change vs " + COMPARE_LABEL if i == 0 else None, f_h2(9), F_HEAD, align=A_LI)

    delta_rows = [
        ("Spend",             f"={IN}!$D$13", f"=SUM({IN}!$C$22,{IN}!$C$38)", M,        "down"),
        ("Revenue",           f"={IN}!$D$16", f"=SUM({IN}!$C$31,{IN}!$C$48)", M,        "up"),
        ("ROAS",              f"={IN}!$D$17", f"=IFERROR(SUM({IN}!$C$31,{IN}!$C$48)/SUM({IN}!$C$22,{IN}!$C$38),0)", F_RATIO4, "up"),
        ("Purchases",         f"={IN}!$D$14", f"=SUM({IN}!$C$29,{IN}!$C$46)", F_INT,    "up"),
        ("Cost per purchase", f"={IN}!$D$15", f"=IFERROR(SUM({IN}!$C$22,{IN}!$C$38)/SUM({IN}!$C$29,{IN}!$C$46),0)", M, "down"),
        ("AOV",               f"={IN}!$D$18", f"=IFERROR(SUM({IN}!$C$31,{IN}!$C$48)/SUM({IN}!$C$29,{IN}!$C$46),0)", M, "up"),
    ]
    for i, (lab, nowv, prevv, fmt, better) in enumerate(delta_rows):
        c = L(1 + i)
        put(ws, f"{c}9", lab if i == 0 else None, None)
        ws.merge_cells(f"{L(1)}{9}:{L(1)}{9}")
        put(ws, f"{c}10", f"=IFERROR({nowv}/{prevv}-1,0)", f_calc(11), fmt=F_PCT,
            align=Alignment(horizontal="left", vertical="center", indent=1))
        put(ws, f"{c}11",
            f'=IF({c}10=0,"",IF({c}10>{0 if better == "up" else 0},"▲ ","▼ ")&TEXT(ABS({c}10),"0.0%"))',
            f_small(9), align=Alignment(horizontal="left", vertical="center", indent=1))
        put(ws, f"{c}9", lab, Font(name="Inter", size=8.5, bold=True, color=MUTED), align=A_LI)
    ws.row_dimensions[10].height = 22
    ws.row_dimensions[11].height = 14
    ws.conditional_formatting.add("A10:F10", FormulaRule(formula=['A10>0'],
                                  font=Font(name="Inter", size=11, bold=True, color=GOOD)))
    ws.conditional_formatting.add("A10:F10", FormulaRule(formula=['A10<0'],
                                  font=Font(name="Inter", size=11, bold=True, color=BAD)))

    # narrative
    section_bar(ws, 13, 1, 8, "  WHAT HAPPENED  —  written from the numbers, then edited by a human")
    nar = [
        ("The headline",
         f'="We invested "&TEXT(ROUND(A6,0),"#,##0")&" and generated "&TEXT(ROUND(B6,0),"#,##0")&'
         f'" in tracked revenue — a return of "&ROUND(C6,2)&"x against a breakeven of "&ROUND({IN}!$B$54,2)&'
         f'"x. "&IF(C6>={IN}!$B$54,"Advertising paid for itself this month.","Advertising did not cover its own '
         f'cost this month, and we are treating that as the primary issue to solve.")'),
        ("Where it came from",
         f'="Meta carried "&TEXT(IFERROR({IN}!$B$22/{IN}!$D$13,0),"0%")&" of spend at "&ROUND({IN}!$B$32,2)&'
         f'"x, and TikTok carried "&TEXT(IFERROR({IN}!$B$38/{IN}!$D$13,0),"0%")&" at "&ROUND({IN}!$B$49,2)&'
         f'"x. "&IF({IN}!$B$32>{IN}!$B$49,"Meta was the more efficient channel this month.",'
         f'"TikTok was the more efficient channel this month.")'),
        ("What changed",
         f'="Return moved from "&ROUND(C7,2)&"x to "&ROUND(C6,2)&"x, and cost per purchase from "&'
         f'TEXT(ROUND(E7,0),"#,##0")&" to "&TEXT(ROUND(E6,0),"#,##0")&". "&'
         f'IF(C6>=C7,"Efficiency improved month on month.","Efficiency slipped month on month, and we know why.")'),
        ("What we are doing about it",
         f'=IF({IN}!$B$58="","Fill this in on the _Inputs tab — what we are doing next month. Talk to the AI prompts file, prompt 1.",{IN}!$B$58)'),
        ("What we need from you",
         f'=IF({IN}!$B$60="","Fill this in on the _Inputs tab — one clear ask.",{IN}!$B$60)'),
    ]
    for i, (lab, form) in enumerate(nar):
        r = 14 + i * 2
        put(ws, f"A{r}", lab, Font(name="Inter", size=10, bold=True, color=ACCENT), align=A_LI)
        ws.merge_cells(f"A{r+1}:H{r+1}")
        put(ws, f"A{r+1}", form, f_body(10), align=A_LW)
        ws.row_dimensions[r].height = 16
        ws.row_dimensions[r + 1].height = 34
    return ws


# ============================================================= PERFORMANCE
def sheet_performance(wb):
    ws = wb.create_sheet("Performance")
    gridlines_off(ws)
    std_widths(ws, {"A": 30, "B": 15, "C": 15, "D": 15, "E": 15, "F": 15, "G": 15, "H": 15})

    put(ws, "A1", "Performance", f_title(17))
    put(ws, "A2", f'={IN}!$B$5&"   ·   Meta, TikTok and combined   ·   all amounts in "&{IN}!$B$10', f_italic(9.5))

    # mirrors the automation's Combined tab
    section_bar(ws, 4, 1, 8, "  COMBINED  —  the three numbers that matter")
    for i, h in enumerate(["Metric", "Meta", "TikTok", "Combined", "Compare (Combined)", "Change", "Read", ""]):
        put(ws, f"{L(1+i)}5", h, f_h2(9), F_HEAD, align=A_LI if i in (0, 6) else A_C)
    ws.merge_cells("G5:H5")

    rows = [
        ("Spend",             "$B$13", "$C$13", "$D$13", "=SUM({IN}!$C$22,{IN}!$C$38)", M, "down"),
        ("Purchases",         "$B$14", "$C$14", "$D$14", "=SUM({IN}!$C$29,{IN}!$C$46)", F_INT, "up"),
        ("Cost Per Purchase", "$B$15", "$C$15", "$D$15", "=IFERROR(SUM({IN}!$C$22,{IN}!$C$38)/SUM({IN}!$C$29,{IN}!$C$46),0)", M, "down"),
        ("Purchases Value",   "$B$16", "$C$16", "$D$16", "=SUM({IN}!$C$31,{IN}!$C$48)", M, "up"),
        ("ROAS",              "$B$17", "$C$17", "$D$17", "=IFERROR(SUM({IN}!$C$31,{IN}!$C$48)/SUM({IN}!$C$22,{IN}!$C$38),0)", F_RATIO4, "up"),
        ("AOV",               "$B$18", "$C$18", "$D$18", "=IFERROR(SUM({IN}!$C$31,{IN}!$C$48)/SUM({IN}!$C$29,{IN}!$C$46),0)", M, "up"),
    ]
    READS = [
        f'=IF(F6>0,"More budget deployed than last period.","Less budget deployed than last period.")',
        f'=IF(F7>0,"More orders than last period.","Fewer orders than last period.")',
        f'=IF(F8<0,"Orders got cheaper — efficiency improved.","Orders got more expensive — watch this closely.")',
        f'=IF(F9>0,"Revenue grew month on month.","Revenue fell month on month.")',
        f'=IF(D10>={IN}!$B$54,"Above breakeven — advertising paid for itself.","Below breakeven — advertising did not pay for itself.")',
        f'=IF(F11>0,"Basket size grew, which absorbs rising media costs.","Basket size shrank, which makes rising media costs harder to absorb.")',
    ]
    for i, (lab, b, c, d, prev, fmt, better) in enumerate(rows):
        r = 6 + i
        put(ws, f"A{r}", lab, f_h2(10) if lab in ("ROAS", "Purchases Value") else f_body(10),
            F_PANEL if lab in ("ROAS", "Purchases Value") else None, align=A_LI)
        for j, ref in enumerate([b, c, d]):
            put(ws, f"{L(2+j)}{r}", f"={IN}!{ref}", f_calc(10),
                F_PANEL if lab in ("ROAS", "Purchases Value") else None, fmt=fmt, align=A_C)
        put(ws, f"E{r}", prev.replace("{IN}", IN), f_small(9.5), fmt=fmt, align=A_C)
        put(ws, f"F{r}", f"=IFERROR(D{r}/E{r}-1,0)", f_calc(9.5), fmt=F_PCT, align=A_C)
        put(ws, f"G{r}", READS[i], f_small(9), align=A_LI)
        ws.merge_cells(f"G{r}:H{r}")

    ws.conditional_formatting.add("F6:F11", CellIsRule(operator="lessThan", formula=["0"],
                                  font=Font(name="Inter", size=9.5, bold=True, color=BAD)))
    ws.conditional_formatting.add("F6:F11", CellIsRule(operator="greaterThan", formula=["0"],
                                  font=Font(name="Inter", size=9.5, bold=True, color=GOOD)))

    # spend mix
    section_bar(ws, 13, 1, 8, "  SPEND MIX")
    for i, h in enumerate(["Channel", "Spend", "Share of spend", "Revenue", "ROAS", "Verdict", "", ""]):
        put(ws, f"{L(1+i)}14", h, f_h2(9), F_HEAD, align=A_LI if i == 0 else A_C)
    for i, (plat, sp, rv, ro) in enumerate([
            ("Meta",   f"={IN}!$B$13", f"={IN}!$B$16", f"={IN}!$B$17"),
            ("TikTok", f"={IN}!$C$13", f"={IN}!$C$16", f"={IN}!$C$17")]):
        r = 15 + i
        put(ws, f"A{r}", plat, f_h2(10), align=A_LI)
        put(ws, f"B{r}", sp, f_calc(10), fmt=M, align=A_C)
        put(ws, f"C{r}", f"=IFERROR(B{r}/$D$13,0)", f_calc(10), fmt=F_PCT, align=A_C)
        put(ws, f"D{r}", rv, f_calc(10), fmt=M, align=A_C)
        put(ws, f"E{r}", ro, f_calc(10), fmt=F_RATIO4, align=A_C)
        put(ws, f"F{r}", f'=IF(E{r}>={IN}!$B$54,"Above breakeven","Below breakeven — under review")', f_small(9.5), align=A_LI)
        ws.merge_cells(f"F{r}:H{r}")
    put(ws, "A17", "Total", f_h2(10), F_PANEL, align=A_LI)
    for col, form, fmt in [("B", "=SUM(B15:B16)", M), ("C", "=IFERROR(B17/$D$13,0)", F_PCT),
                           ("D", "=SUM(D15:D16)", M), ("E", f"=IFERROR(D17/B17,0)", F_RATIO4)]:
        put(ws, f"{col}17", form, f_calc(10), F_PANEL, fmt=fmt, align=A_C)
    put(ws, "F17", f'=IF(E17>={IN}!$B$54,"Above breakeven","Below breakeven")', f_small(9.5), F_PANEL, align=A_LI)
    ws.merge_cells("F17:H17")

    # breakeven context
    section_bar(ws, 19, 1, 8, "  READ THIS AGAINST BREAKEVEN")
    notes = [
        f'="Breakeven ROAS for this business is "&ROUND({IN}!$B$54,2)&"x. That is calculated from your own cost '
        f'structure — product cost, shipping, payment fees and returns — not from an industry rule of thumb."',
        f'="You delivered "&ROUND({IN}!$D$17,2)&"x. "&IF({IN}!$D$17>={IN}!$B$54,'
        f'"That means every unit spent on advertising returned a profit above its own cost.",'
        f'"That means advertising did not cover its own cost this month.")',
        f'="Target for next month is "&ROUND({IN}!$B$55,2)&"x. Anything at or above breakeven keeps the account '
        f'compounding; anything below it needs a structural fix, not a bigger budget."',
    ]
    for i, t in enumerate(notes):
        r = 20 + i
        ws.merge_cells(f"A{r}:H{r}")
        verdict_cell(ws, f"A{r}", t, Font(name="Inter", size=9.5, color=INK_SOFT), fill_=F_ACCENTBG)
        for c in range(1, 9):
            ws.cell(row=r, column=c).fill = F_ACCENTBG
        ws.row_dimensions[r].height = 26
    return ws


# ========================================================== PLATFORM DETAIL
def sheet_platform(wb):
    ws = wb.create_sheet("Platform Detail")
    gridlines_off(ws)
    std_widths(ws, {"A": 28, "B": 15, "C": 15, "D": 15, "E": 3, "F": 28, "G": 15, "H": 15, "I": 15})

    put(ws, "A1", "Platform detail", f_title(17))
    put(ws, "A2", f'={IN}!$B$5&"   ·   this period against last period"', f_italic(9.5))

    def block(start_col, title, row_keys):
        c0 = start_col
        section_bar(ws, 4, c0, c0 + 2, f"  {title}")
        for i, h in enumerate(["Metric", "This period", COMPARE_LABEL]):
            put(ws, f"{L(c0+i)}5", h, f_h2(9), F_HEAD, align=A_LI if i == 0 else A_C)
        for i, (lab, cur_ref, prv_ref, fmt) in enumerate(row_keys):
            r = 6 + i
            put(ws, f"{L(c0)}{r}", lab, f_body(9.5), align=A_LI)
            put(ws, f"{L(c0+1)}{r}", f"={IN}!{cur_ref}", f_calc(9.5), fmt=fmt, align=A_C)
            put(ws, f"{L(c0+2)}{r}", f"={IN}!{prv_ref}", f_small(9.5), fmt=fmt, align=A_C)
        return 6 + len(row_keys)

    meta_keys = [
        ("Spend",             "$B$22", "$C$22", M),
        ("Outbound CTR",      "$B$23", "$C$23", F_PCT),
        ("Impressions",       "$B$24", "$C$24", F_INT),
        ("Reach",             "$B$25", "$C$25", F_INT),
        ("Frequency",         "$B$26", "$C$26", F_2D),
        ("Adds to cart",      "$B$27", "$C$27", F_INT),
        ("Initiate Checkout", "$B$28", "$C$28", F_INT),
        ("Purchases",         "$B$29", "$C$29", F_INT),
        ("Cost Per Purchase", "$B$30", "$C$30", M),
        ("Purchases Value",   "$B$31", "$C$31", M),
        ("ROAS",              "$B$32", "$C$32", F_RATIO4),
        ("AOV",               "$B$33", "$C$33", M),
    ]
    tt_keys = [
        ("Spend",             "$B$38", "$C$38", M),
        ("CPM",               "$B$39", "$C$39", M),
        ("CTR",               "$B$40", "$C$40", F_PCT),
        ("Impressions",       "$B$41", "$C$41", F_INT),
        ("Reach",             "$B$42", "$C$42", F_INT),
        ("Frequency",         "$B$43", "$C$43", F_2D),
        ("Adds to cart",      "$B$44", "$C$44", F_INT),
        ("Initiate Checkout", "$B$45", "$C$46", F_INT),
        ("Purchases",         "$B$46", "$C$46", F_INT),
        ("Cost Per Purchase", "$B$47", "$C$48", M),
        ("Purchases Value",   "$B$48", "$C$48", M),
        ("ROAS",              "$B$49", "$C$49", F_RATIO4),
        ("AOV",               "$B$50", "$C$50", M),
    ]
    end_a = block(1, "META", meta_keys)
    end_b = block(6, "TIKTOK", tt_keys)

    r = max(end_a, end_b) + 1
    ws.merge_cells(f"A{r}:I{r}")
    verdict_cell(ws, f"A{r}",
        '="A note on reach: the numbers above sum daily reach across the month, so they overstate the number of '
        'distinct people. Platform reach is deduplicated within a day, not across a month. Treat it as a trend, '
        'not a headcount."',
        Font(name="Inter", size=9, italic=True, color=MUTED), fill_=F_PANEL)
    for c in range(1, 10):
        ws.cell(row=r, column=c).fill = F_PANEL
    ws.row_dimensions[r].height = 26
    return ws


# ================================================================ TOP ADS
def sheet_top_ads(wb, *, creative=False):
    name = "Creatives" if creative else "Top Ads"
    ws = wb.create_sheet(name)
    gridlines_off(ws)
    std_widths(ws, {"A": 6, "B": 38, "C": 15, "D": 13, "E": 15, "F": 11, "G": 12,
                    "H": 12, "I": 44})

    put(ws, "A1", name, f_title(17))
    sub = ("Grouped by creative key — the same asset across campaigns and ad sets."
           if creative else "Ranked by spend. Paste straight from the automation's Ad Performance tab.")
    put(ws, "A2", f'={IN}!$B$5&"   ·   "&"{sub}"', f_italic(9.5))

    hdrs = ["#", "Ad name" if not creative else "Creative", "Spend", "Purchases",
            "Revenue", "ROAS", "Cost/Purch.", "AOV", "Read"]
    for i, h in enumerate(hdrs):
        put(ws, f"{L(1+i)}5", h, f_h2(9), F_HEAD, align=A_LI if i in (1, 8) else A_C)

    roster = SD.aggregate_ads(ADROWS, by=("creative" if creative else "ad"), top=10)

    for i, (label, spend, pur, rev, _r, _c, _a) in enumerate(roster):
        r = 6 + i
        put(ws, f"A{r}", i + 1, f_small(9), align=A_C)
        put(ws, f"B{r}", label, Font(name="Inter", size=9.5, bold=True, color=INK), align=A_LI)
        put(ws, f"C{r}", spend, f_input(9.5), F_INPUT, fmt=M, align=A_C, border=B_INPUT)
        put(ws, f"D{r}", pur, f_input(9.5), F_INPUT, fmt=F_INT, align=A_C, border=B_INPUT)
        put(ws, f"E{r}", rev, f_input(9.5), F_INPUT, fmt=M, align=A_C, border=B_INPUT)
        put(ws, f"F{r}", f"=IFERROR(E{r}/C{r},0)", f_calc(9.5), fmt=F_RATIO4, align=A_C)
        put(ws, f"G{r}", f"=IFERROR(C{r}/D{r},0)", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"H{r}", f"=IFERROR(E{r}/D{r},0)", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"I{r}", f'=IF(C{r}=0,"",IF(F{r}>={IN}!$B$54*1.3,"Scale — strongest return in the set",'
                         f'IF(F{r}>={IN}!$B$54,"Keep and refresh the asset","Below breakeven — cut or rebuild")))',
            f_small(9), align=A_LI)
    last = 5 + len(roster)

    ws.conditional_formatting.add(f"F6:F{last}", ColorScaleRule(
        start_type="num", start_value=0, start_color="FEE2E2",
        mid_type="num", mid_value=2, mid_color="FEF3C7",
        end_type="num", end_value=6, end_color="DCFCE7"))
    ws.conditional_formatting.add(f"I6:I{last}", FormulaRule(formula=['ISNUMBER(SEARCH("Scale",$I6))'],
                                  font=Font(name="Inter", size=9, bold=True, color=GOOD), fill=F_GOODBG))
    ws.conditional_formatting.add(f"I6:I{last}", FormulaRule(formula=['ISNUMBER(SEARCH("Below",$I6))'],
                                  font=Font(name="Inter", size=9, bold=True, color=BAD), fill=F_BADBG))

    r = last + 2
    ws.merge_cells(f"A{r}:I{r}")
    verdict_cell(ws, f"A{r}",
        f'="Spend above is "&TEXT(ROUND(SUM(C6:C{last}),0),"#,##0")&" against "&'
        f'TEXT(ROUND({IN}!$D$13,0),"#,##0")&" total ad spend — a gap means some spend sits in ads not listed here."',
        Font(name="Inter", size=9.5, color=INK_SOFT), fill_=F_PANEL)
    for c in range(1, 10):
        ws.cell(row=r, column=c).fill = F_PANEL
    ws.row_dimensions[r].height = 24

    r += 2
    put(ws, f"A{r}", "What to do with this table", f_h1(10.5))
    ws.merge_cells(f"A{r}:I{r}")
    guidance = [
        "Anything above 1.3× breakeven gets more budget — but raise it in steps and watch frequency, not in one jump.",
        "Anything between breakeven and 1.3× is working. Keep it, and refresh the creative before it fatigues.",
        "Anything below breakeven is losing money on every order. Fix the landing page or stop it. Do not 'optimise' it forever.",
        "Look at cost per purchase against AOV, not against last month alone. A rising CPA with a rising AOV can still be progress.",
    ]
    for i, g in enumerate(guidance):
        rr = r + 1 + i
        put(ws, f"A{rr}", "·", f_small(9), align=A_C)
        put(ws, f"B{rr}", g, f_small(9), align=A_LW)
        ws.merge_cells(f"B{rr}:I{rr}")
        ws.row_dimensions[rr].height = 15
    return ws


# ============================================================= WEEKLY TREND
def sheet_weekly(wb):
    ws = wb.create_sheet("Weekly Trend")
    gridlines_off(ws)
    std_widths(ws, {"A": 4, "B": 20, "C": 15, "D": 13, "E": 15, "F": 12, "G": 13,
                    "H": 13, "I": 34})

    put(ws, "A1", "Weekly trend", f_title(17))
    put(ws, "A2", f'={IN}!$B$5&"   ·   week by week, ranked best ROAS first (matching the automation\'s Weekly tabs)"', f_italic(9.5))

    for i, h in enumerate(["#", "Week", "Spend", "Purchases", "Revenue", "ROAS", "Cost/Purch.", "AOV", "Read"]):
        put(ws, f"{L(1+i)}5", h, f_h2(9), F_HEAD, align=A_LI if i in (1, 8) else A_C)

    weeks = SD.weekly_rows(ROWS)
    for i, (lab, spend, pur, rev, _roas, _cpp, _aov) in enumerate(weeks):
        r = 6 + i
        put(ws, f"A{r}", i + 1, f_small(9), align=A_C)
        put(ws, f"B{r}", lab, Font(name="Inter", size=9.5, bold=True, color=INK), align=A_LI)
        put(ws, f"C{r}", spend, f_input(9.5), F_INPUT, fmt=M, align=A_C, border=B_INPUT)
        put(ws, f"D{r}", pur, f_input(9.5), F_INPUT, fmt=F_INT, align=A_C, border=B_INPUT)
        put(ws, f"E{r}", rev, f_input(9.5), F_INPUT, fmt=M, align=A_C, border=B_INPUT)
        put(ws, f"F{r}", f"=IFERROR(E{r}/C{r},0)", f_calc(9.5), fmt=F_RATIO4, align=A_C)
        put(ws, f"G{r}", f"=IFERROR(C{r}/D{r},0)", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"H{r}", f"=IFERROR(E{r}/D{r},0)", f_calc(9.5), fmt=M, align=A_C)
        put(ws, f"I{r}", f'=IF(F{r}="","",IF(F{r}>={IN}!$B$54*1.25,"Strongest week of the month",'
                         f'IF(F{r}>={IN}!$B$54,"Above breakeven","The soft week — this is the one to explain")))',
            f_small(9), align=A_LI)
    last = 5 + len(weeks)
    ws.conditional_formatting.add(f"F6:F{last}", ColorScaleRule(
        start_type="min", start_color="FEE2E2", mid_type="percentile", mid_value=50,
        mid_color="FEF3C7", end_type="max", end_color="DCFCE7"))
    ws.conditional_formatting.add(f"I6:I{last}", FormulaRule(formula=['ISNUMBER(SEARCH("soft",$I6))'],
                                  font=Font(name="Inter", size=9, bold=True, color=WARN), fill=F_WARNBG))

    r = last + 2
    ws.merge_cells(f"A{r}:I{r}")
    verdict_cell(ws, f"A{r}",
        f'="Spread between the best and worst week: "&ROUND(MAX(F6:F{last})-MIN(F6:F{last}),2)&" ROAS points. "&'
        f'"Weeks are ranked by return, exactly as the automation\'s Weekly tabs rank them. If the soft week is also '
        f'the week you spent the most, that is the whole story of the month."',
        Font(name="Inter", size=9.5, color=INK_SOFT), fill_=F_ACCENTBG)
    for c in range(1, 10):
        ws.cell(row=r, column=c).fill = F_ACCENTBG
    ws.row_dimensions[r].height = 30
    return ws


# ================================================================== NARRATIVE
def sheet_narrative(wb):
    ws = wb.create_sheet("What We Did & Next")
    gridlines_off(ws)
    std_widths(ws, {"A": 26, "B": 78, "C": 60})

    put(ws, "A1", "What we did, and what happens next", f_title(17))
    put(ws, "A2", f'={IN}!$B$5&"   ·   the part of the report the client actually reads"', f_italic(9.5))

    blocks = [
        ("What we changed this month", "$B$56",
         "Name three things you actually did. Specifics beat adjectives: \"launched four UGC concepts\" not \"optimised creative\"."),
        ("What we learned", "$B$57",
         "One insight the data proved. This is what you are paid for."),
        ("What we are doing next month", "$B$58",
         "Two or three concrete moves, each tied to a number above."),
        ("What the numbers don't show", "$B$59",
         "Stockouts, shipping delays, a price change, a competitor entering. Say it before the client finds it."),
        ("What we need from you", "$B$60",
         "One clear ask. New imagery, a price decision, a stock fix. Give them a job and they become a partner."),
    ]
    r = 4
    for lab, ref, hint in blocks:
        section_bar(ws, r, 1, 2, f"  {lab.upper()}")
        r += 1
        put(ws, f"A{r}", lab, f_h2(10), align=A_LW)
        ws.merge_cells(f"B{r}:B{r+3}")
        put(ws, f"B{r}", f"={IN}!{ref}", f_body(10), align=A_LW, border=b_all())
        put(ws, f"C{r}", hint, f_tiny(8), align=A_LW)
        ws.merge_cells(f"C{r}:C{r+3}")
        for k in range(4):
            ws.row_dimensions[r + k].height = 20
        r += 5

    section_bar(ws, r, 1, 2, "  HOW TO FILL THESE IN")
    r += 1
    put(ws, f"A{r}", "Don't write these from scratch.", f_h2(10), align=A_LI)
    put(ws, f"B{r}", "Open 05_AI_Prompts_Campaign_Performance.md and run Prompt 1 (the monthly narrative) on your "
                     "_Inputs tab. It will draft all five blocks. Then edit for tone — delete anything that sounds "
                     "like a machine, and cut it to half the length. The client reads the first sentence of each block.",
        f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 46
    r += 2
    put(ws, f"A{r}", "The tone rule", f_h2(10), align=A_LI)
    put(ws, f"B{r}", "Never explain a metric the client didn't ask about. Never hide a bad month. Lead with what "
                     "changed and what you're doing about it — the numbers are evidence, not the message.",
        f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 32
    return ws


# =============================================================== DICTIONARY
def sheet_dict(wb):
    ws = wb.create_sheet("Dictionary")
    gridlines_off(ws)
    std_widths(ws, {"A": 26, "B": 52, "C": 62})

    put(ws, "A1", "What each number means", f_title(17))
    put(ws, "A2", "Send this page with the report. It answers 80% of the follow-up questions before they're asked.", f_italic(9.5))

    for i, h in enumerate(["Term", "In plain English", "Why it matters to you"]):
        put(ws, f"{L(1+i)}4", h, f_h2(9.5), F_HEAD, align=A_LI)

    rows = [
        ("Ad spend", "What we put into Meta and TikTok this month.", "This is the investment. Everything else is the result of it."),
        ("Impressions", "How many times our ads were shown.", "Volume of attention — not a result on its own."),
        ("Reach", "How many people saw the ads (counted once per person per day).", "How many humans, roughly. It can't be added up across a month, so treat it as a trend."),
        ("Frequency", "How many times, on average, each person saw us.", "Too low and you're under-spending; too high and people stop noticing us."),
        ("CPM", "What it cost to show our ads a thousand times.", "The price of attention. It rises and falls with auction competition, not just our choices."),
        ("CTR", "The share of people who clicked after seeing an ad.", "How well the creative earns attention."),
        ("Clicks", "Visits to your site from our ads.", "The top of your sales funnel."),
        ("Add to cart", "People who put something in their basket.", "Intent. This is where we see if the product page is doing its job."),
        ("Initiate checkout", "People who started checking out.", "The last step before money moves."),
        ("Purchases", "Orders attributed to our ads.", "The result we're judged on — reported inside the platform's attribution window, which is stated on every report."),
        ("Purchases value / Revenue", "The value of those orders.", "This is what ROAS is built from."),
        ("ROAS", "Revenue divided by ad spend. A 3.0x return means each unit spent brought back 3.", "The headline efficiency number."),
        ("Breakeven ROAS", "The ROAS at which you make exactly zero profit after product cost, shipping, fees and returns.", "The only number that tells you whether a ROAS is good. A 3x ROAS is a loss for one business and a win for another."),
        ("AOV", "Average order value.", "A rising AOV can rescue a rising cost per order."),
        ("Cost per purchase", "Ad spend divided by orders.", "Meaningful only next to AOV and breakeven. Cheaper orders from a lower-value basket aren't progress."),
        ("Conversion rate", "The share of clicks that became orders.", "How well the site converts the traffic we buy."),
        ("Attribution window", "How long after clicking a platform still credits itself with a sale.", "We keep this fixed month to month so comparisons stay honest. It's stated on the report."),
    ]
    for i, (a, b, c) in enumerate(rows):
        r = 5 + i
        put(ws, f"A{r}", a, Font(name="Inter", size=9.5, bold=True, color=INK), align=A_LW)
        put(ws, f"B{r}", b, f_body(9), align=A_LW)
        put(ws, f"C{r}", c, f_body(9), align=A_LW)
        ws.row_dimensions[r].height = 34

    r = 5 + len(rows) + 1
    ws.merge_cells(f"A{r}:C{r}")
    verdict_cell(ws, f"A{r}",
        '="All figures are pulled directly from Meta\'s and TikTok\'s own reporting APIs. There is no manual entry '
        'step between the platform and this report."',
        Font(name="Inter", size=9.5, bold=True, color=INK), fill_=F_PANEL)
    for c in range(1, 4):
        ws.cell(row=r, column=c).fill = F_PANEL
    ws.row_dimensions[r].height = 24
    return ws


# ==================================================================== BUILD
def build():
    wb = Workbook()
    wb.remove(wb.active)
    sheet_inputs(wb)
    sheet_cover(wb)
    sheet_exec(wb)
    sheet_performance(wb)
    sheet_platform(wb)
    sheet_top_ads(wb, creative=False)
    sheet_top_ads(wb, creative=True)
    sheet_weekly(wb)
    sheet_narrative(wb)
    sheet_dict(wb)
    wb.active = 1
    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
