"""
Builds 03_KPI_Calculator.xlsx  —  the math engine of the kit.

Tabs: Start Here · Calculator · Profit Bridge · Period Compare · Benchmarks · Metric Dictionary

Run:  python3 "_build/build_kpi_calculator.py"
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openpyxl import Workbook
from openpyxl.utils import get_column_letter as L
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Font, Alignment

from kitstyle import *
from kitstyle import CURRENCY_CODE as CUR
import sample_data as SD

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "03_KPI_Calculator.xlsx")
M  = money()
M0 = money0()


# =============================================================== START HERE
def sheet_start(wb):
    ws = wb.create_sheet("Start Here")
    gridlines_off(ws)
    std_widths(ws, {"A": 3, "B": 30, "C": 96, "D": 3})

    put(ws, "B2", KIT_NAME, f_title(18))
    put(ws, "B3", "KPI Calculator  ·  the math engine", f_h2(11))
    ws.row_dimensions[2].height = 26
    ws.row_dimensions[3].height = 18

    put(ws, "B5", "What this file does", f_h1(11))
    put(ws, "B6", "It turns platform numbers (spend, impressions, clicks, purchases, revenue) into the two "
                  "things a client actually asks about: what each order really costs you, and whether the "
                  "ad spend made money. It also tells you your breakeven ROAS, which is the number most "
                  "media buyers quote wrong.", f_body(10), align=A_LW)
    ws.row_dimensions[6].height = 46

    steps = [
        ("1", "Open the Calculator tab.", "Fill in the nine amber boxes under MEDIA INPUTS. That's your platform data."),
        ("2", "Fill the nine amber boxes under BUSINESS INPUTS.", "These are the client's real costs: margin, shipping, fees, returns. If you don't have them, ask. This is the difference between a report and a guess."),
        ("3", "Leave every grey cell alone.", "Grey = calculated. Nothing there needs typing."),
        ("4", "Read THE VERDICT.", "Five plain-English sentences you can paste into a client email. They update live."),
        ("5", "Check the sanity checks.", "Red rows mean the input data is wrong — fix the data before you trust the output."),
        ("6", "Use Profit Bridge and Period Compare.", "Profit Bridge shows where every unit of revenue goes. Period Compare explains WHY ROAS moved, split into CPM / CTR / CVR / AOV."),
    ]
    r = 8
    for n, t, d in steps:
        put(ws, f"B{r}", n, Font(name="Inter", size=13, bold=True, color=ACCENT))
        put(ws, f"C{r}", t, f_h2(10))
        put(ws, f"C{r+1}", d, f_small(9), align=A_LW)
        ws.row_dimensions[r].height = 16
        ws.row_dimensions[r + 1].height = 30
        r += 2

    r += 1
    section_bar(ws, r, 2, 3, "  ONE SETTING")
    r += 1
    put(ws, f"B{r}", "Currency code", f_h2(10), align=A_LI)
    put(ws, f"C{r}", CUR, f_input(11), F_INPUT, align=A_LI, border=B_INPUT)
    r += 1
    put(ws, f"B{r}", "Change it by:", f_small(9), align=A_LI)
    put(ws, f"C{r}", "Find-and-replace \"" + CUR + "\" with your currency code on the Calculator, Profit Bridge "
                     "and Benchmarks tabs, then update the cell formats (Format ▸ Number ▸ Custom) where you "
                     "want the symbol shown.", f_small(9), align=A_LW)
    ws.row_dimensions[r].height = 28

    r += 2
    put(ws, f"B{r}", "The one rule", f_h1(11))
    put(ws, f"B{r+1}", "Never report ROAS without breakeven ROAS next to it.", Font(name="Inter", size=10, bold=True, color=BAD), align=A_LW)
    put(ws, f"C{r+1}", "A 2.4x ROAS sounds fine until you learn the client's breakeven is 2.8x. Every number in "
                       "this kit is built to be read against breakeven, not against a vague idea of \"good\".", f_body(10), align=A_LW)
    ws.row_dimensions[r + 1].height = 32
    return ws


# ============================================================== CALCULATOR
def sheet_calculator(wb):
    ws = wb.create_sheet("Calculator")
    gridlines_off(ws)
    std_widths(ws, {"A": 36, "B": 17, "C": 52, "D": 3, "E": 34, "F": 17, "G": 52})

    title_block(ws, "KPI Calculator", "Nine numbers in. Everything a client will ask you, out. A worked example (Meta, September 2026) is already loaded — overwrite the amber cells.", CUR, last_col=7)
    ws["A3"].font = f_small(9)

    # ---- section bars
    section_bar(ws, 5, 1, 3, "  1 · MEDIA INPUTS  —  type in the amber cells")
    section_bar(ws, 5, 5, 7, "  2 · BUSINESS INPUTS  —  the client's real costs")

    label_value_hdr(ws, 6, 1, "Metric", "Value", "Where you get it")
    label_value_hdr(ws, 6, 5, "Input", "Value", "Where you get it")

    # A worked example ships prefilled so the file is understandable on open.
    # Overwrite every amber cell with your own numbers.
    _m = SD.derive(SD.totals(SD.fundamentals_rows(), SD.CUR_START, SD.CUR_END, "Meta"))
    _v = [round(_m["spend"], 2), round(_m["imp"]), round(_m["reach"]), round(_m["clicks"]),
          round(_m["lpv"]), round(_m["atc"]), round(_m["ic"]), round(_m["pur"]),
          round(_m["rev"], 2)]
    media = [
        ("Ad spend",                              M,   "Platform total, same period as everything below"),
        ("Impressions",                           F_INT, "Platform"),
        ("Reach",                                 F_INT, "Platform — needed for frequency"),
        ("Clicks (link clicks)",                  F_INT, "Outbound / link clicks, NOT all clicks"),
        ("Landing page views",                    F_INT, "Same platform as the clicks above. TikTok does not report LPV"),
        ("Adds to cart",                          F_INT, "Platform, same attribution window"),
        ("Initiate checkout",                     F_INT, "Platform"),
        ("Purchases",                             F_INT, "Platform. Keep the window consistent month to month"),
        ("Revenue (purchase value)",               M,   "Platform purchase value, not Shopify gross sales"),
    ]
    for i, (lab, fmt, note) in enumerate(media):
        metric_row(ws, 7 + i, 1, lab, _v[i], note, fmt=fmt, is_input=True)

    _rows = SD.fundamentals_rows()
    _all = SD.derive(SD.totals(_rows, SD.CUR_START, SD.CUR_END))
    _biz = [SD.COGS_PCT, SD.SHIP_PER_ORDER, 0.03, 0.03, 0.0,
            25000, 18000, 0.15, round(_all["rev"] * 1.35, 2)]
    biz = [
        ("COGS (% of revenue)",          F_PCT, "Product cost ÷ selling price. Ask the client — don't assume 30%"),
        ("Shipping & fulfilment per order", M,  "What it costs to get an order out, including packaging"),
        ("Payment processing fee (%)",   F_PCT, "Card / gateway fees. Usually 2–4%"),
        ("Returns & refunds (% of revenue)", F_PCT, "Real refund rate, not the aspirational one"),
        ("Other variable cost per order", M,    "Anything that scales with an order"),
        ("Fixed monthly costs",          M,     "Excluding ads and agency fee"),
        ("Agency / retainer fee (monthly)", M,  "What you charge this client"),
        ("Target net margin (%)",        F_PCT, "The profit the client wants to keep AFTER ads"),
        ("Blended revenue incl. organic", M,    "All revenue, not just ads — for MER. Leave blank if unknown"),
    ]
    for i, (lab, fmt, note) in enumerate(biz):
        metric_row(ws, 7 + i, 5, lab, _biz[i], note, fmt=fmt, is_input=True)

    # ---- section 3 + 4
    section_bar(ws, 17, 1, 3, "  3 · FUNNEL EFFICIENCY  —  calculated, do not type")
    section_bar(ws, 17, 5, 7, "  4 · UNIT ECONOMICS & PROFIT  —  calculated, do not type")

    put(ws, "A18", "Metric", f_h2(9.5), F_HEAD, align=A_LI)
    put(ws, "B18", "Value",  f_h2(9.5), F_HEAD, align=A_C)
    put(ws, "C18", "What it tells you", f_h2(9.5), F_HEAD, align=A_LI)
    put(ws, "E18", "Metric", f_h2(9.5), F_HEAD, align=A_LI)
    put(ws, "F18", "Value",  f_h2(9.5), F_HEAD, align=A_C)
    put(ws, "G18", "What it tells you", f_h2(9.5), F_HEAD, align=A_LI)
    ws.row_dimensions[18].height = 17

    funnel = [
        ("CPM (cost per 1,000 impressions)", "=IFERROR(B7/B8*1000,0)", M, "What you paid for attention. Rising CPM is usually auction pressure, not your fault"),
        ("CPC (cost per link click)",        "=IFERROR(B7/B10,0)",    M, "Cost of a visit. Moves with CPM and CTR"),
        ("CTR %",                            "=IFERROR(B10/B8,0)",    F_PCT, "Creative hook strength. The only lever you can change fast"),
        ("Frequency",                        "=IFERROR(B8/B9,0)",     F_RATIO, "Average times each person saw you. Above ~3.5, fatigue starts"),
        ("Click → Landing page %",           "=IFERROR(B11/B10,0)",   F_PCT, "Site speed and load quality. Below 60% is a technical problem"),
        ("Landing page → Add to cart %",     "=IFERROR(B12/B11,0)",   F_PCT, "Product page: offer, price, imagery"),
        ("Add to cart → Checkout %",         "=IFERROR(B13/B12,0)",   F_PCT, "Shipping cost and surprise fees show up here"),
        ("Checkout → Purchase %",            "=IFERROR(B14/B13,0)",   F_PCT, "Payment options and trust signals"),
        ("Click → Purchase CVR %",           "=IFERROR(B14/B10,0)",   F_PCT, "End-to-end site conversion on paid traffic"),
        ("Cost per add to cart",             "=IFERROR(B7/B12,0)",    M, "Cheap intent. Good for judging creative before purchase data settles"),
        ("Cost per checkout",                "=IFERROR(B7/B13,0)",    M, "Mid-funnel cost"),
        ("Cost per purchase (CPA)",          "=IFERROR(B7/B14,0)",    M, "The number clients fixate on. Always show AOV beside it"),
        ("AOV (average order value)",        "=IFERROR(B15/B14,0)",   M, "Revenue ÷ orders. Rising AOV can rescue a falling CVR"),
        ("ROAS",                             "=IFERROR(B15/B7,0)",    F_RATIO4, "Revenue ÷ ad spend. Meaningless without breakeven ROAS"),
        ("Revenue per 1,000 impressions",    "=IFERROR(B15/B8*1000,0)", M, "Media efficiency end to end — the cleanest single measure"),
        ("Spend as % of revenue",            "=IFERROR(B7/B15,0)",    F_PCT, "Share of revenue going back into ads"),
    ]
    for i, (lab, form, fmt, note) in enumerate(funnel):
        metric_row(ws, 19 + i, 1, lab, form, note, fmt=fmt, strong=(lab == "ROAS"))

    units = [
        ("Revenue",                            "=B15",                     M,     "Everything below starts here"),
        ("Less: COGS",                         "=-IFERROR(B15*F7,0)",      M,     "Product cost"),
        ("Less: shipping & fulfilment",        "=-IFERROR(B14*F8,0)",      M,     "Scales with orders, not revenue"),
        ("Less: payment processing",           "=-IFERROR(B15*F9,0)",      M,     "Gateway fees"),
        ("Less: returns & refunds",            "=-IFERROR(B15*F10,0)",     M,     "Money you sent back"),
        ("Less: other variable costs",         "=-IFERROR(B14*F11,0)",     M,     "Anything order-linked"),
        ("= Contribution margin",              "=SUM(F19:F24)",            M,     "What's left to pay for ads, overhead and profit", True),
        ("Contribution margin %",              "=IFERROR(F25/F19,0)",      F_PCT, "The single most important input in this whole file"),
        ("Contribution per order",             "=IFERROR(F25/B14,0)",      M,     "Profit per order before ad spend"),
        ("BREAKEVEN ROAS",                     "=IFERROR(1/F26,0)",        F_RATIO4, "Below this, every sale loses money. Report this next to ROAS, always", True),
        ("Target ROAS for your margin goal",   "=IFERROR(1/(F26-F14),0)",  F_RATIO4, "The ROAS you must hit to deliver the client's target profit"),
        ("ROAS achieved",                      "=IFERROR(B15/B7,0)",       F_RATIO4, "What you actually delivered"),
        ("= Profit after ad spend",            "=F25-B7",                  M,     "Contribution minus media. The line that matters", True),
        ("POAS (profit on ad spend)",          "=IFERROR(F31/B7,0)",       F_RATIO4, "Profit per 1 unit of ad spend. The margin-aware sibling of ROAS"),
        ("Profit after fixed costs",           "=F31-F12",                 M,     "Ad-funded contribution minus overhead"),
        ("Net profit after agency fee",        "=F33-F13",                 M,     "The bottom line the client sees"),
        ("MER (blended ROAS)",                 "=IFERROR(F15/B7,0)",       F_RATIO4, "All revenue ÷ ad spend. Blank if you didn't enter blended revenue"),
    ]
    for i, item in enumerate(units):
        lab, form, fmt, note = item[0], item[1], item[2], item[3]
        strong = len(item) > 4 and item[4]
        metric_row(ws, 19 + i, 5, lab, form, note, fmt=fmt, strong=strong)

    # ---- Section 5 · verdict
    section_bar(ws, 37, 1, 7, "  5 · THE VERDICT  —  plain English, updates live. Paste straight into a client email.")
    n = lambda expr, dp=0: f'ROUND({expr},{dp})'
    verdicts = [
        '=IF(F19<=0,"⚠ Add your business inputs first (section 2) — the verdict needs them.",'
        '"Profitability: after ad spend the account kept "&' + n("F31") + '&" ' + CUR + '. Breakeven ROAS is "&'
        + n("F28", 2) + '&"x and you delivered "&' + n("F30", 2) + '&"x — "&'
        'IF(F30>=F28,"you are trading above breakeven, so the account is making money on media.","you are trading BELOW breakeven: at this margin, this spend is not paying for itself."))',

        '="Headroom: at a "&' + n("F26*100", 1) + '&"% contribution margin you can carry up to "&' + n("B15*F26") +
        '&" ' + CUR + ' of ad spend before ads stop paying for themselves. You spent "&' + n("B7") +
        '&" ' + CUR + ', so there is "&' + n("B15*F26-B7") + '&" ' + CUR + ' of room at today\'s efficiency."',

        '="Efficiency: every 1,000 impressions cost "&' + n("B19", 2) + '&" ' + CUR + ' and returned "&' + n("B33", 2) +
        '&" ' + CUR + ' of revenue ("&' + n("IFERROR(B33/B19,0)", 2) + '&"x). You paid "&' + n("B20", 2) +
        '&" ' + CUR + ' per link click and that click converted to a purchase "&' + n("B27*100", 2) + '&"% of the time."',

        '="Tightest bottleneck: "&IF(AND(B23<=B24,B23<=B25,B23<=B26),"click → landing page ("&' + n("B23*100", 1) +
        '&"%) — this is usually a page-speed or tracking problem, not a media problem.",'
        'IF(AND(B24<=B25,B24<=B26),"landing page → add to cart ("&' + n("B24*100", 1) +
        '&"%) — the product page is not persuading. Offer, price, imagery, reviews.",'
        'IF(B25<=B26,"add to cart → checkout ("&' + n("B25*100", 1) +
        '&"%) — something is being added at checkout: shipping cost, fees, or forced account creation.",'
        '"checkout → purchase ("&' + n("B26*100", 1) +
        '&"%) — payment options or trust signals are costing you completed orders.")))&" Every other step is above it, so fix this one first."',

        '="Volume: you bought "&' + n("B8") + '&" impressions and reached "&' + n("B9") + '&" people, so the average person saw you "&'
        + n("B22", 2) + '&" times. "&IF(B22>3.5,"That is high — refresh creative before you add budget, or you will keep paying more for the same eyeballs.",'
        'IF(B22<1.6,"That is very low — you are under-spending into a proven audience. There is budget headroom here.","That is a healthy range, so there is room to add budget before creative fatigue bites."))',
    ]
    for i, v in enumerate(verdicts):
        r = 38 + i
        ws.merge_cells(f"A{r}:G{r}")
        verdict_cell(ws, f"A{r}", v,
                     font=Font(name="Inter", size=10, color=INK_SOFT), fill_=F_ACCENTBG)
        for c in range(1, 8):
            ws.cell(row=r, column=c).fill = F_ACCENTBG
        ws.row_dimensions[r].height = 34

    # ---- Section 6 · sanity checks
    section_bar(ws, 44, 1, 7, "  6 · SANITY CHECKS  —  run these before you send anything to a client")
    put(ws, "A45", "Check", f_h2(9.5), F_HEAD, align=A_LI)
    put(ws, "B45", "Status", f_h2(9.5), F_HEAD, align=A_C)
    put(ws, "C45", "Meaning", f_h2(9.5), F_HEAD, align=A_LI)

    checks = [
        ("Clicks must not exceed impressions",              '=IF(B10>B8,"FIX","OK")',        "A clicks > impressions read means you pulled the wrong click column."),
        ("Add to cart should not exceed landing page views",'=IF(B12>B11,"CHECK","OK")',     "Usually means LPV and ATC came from different sources or windows."),
        ("Purchases must not exceed clicks",                '=IF(B14>B10,"FIX","OK")',       "Either a lookalike-justified view-through number, or mixed date ranges."),
        ("Reach must not exceed impressions",               '=IF(B9>B8,"FIX","OK")',         "Reach is deduplicated, so it is always ≤ impressions."),
        ("Revenue must be present",                         '=IF(B15<=0,"FIX","OK")',        "Without purchase value there is no ROAS, no AOV and no story."),
        ("Contribution margin should be between 0% and 100%",'=IF(OR(F26<=0,F26>=1),"CHECK","OK")', "A negative margin means you lose money on the product before ads."),
        ("Breakeven ROAS should land between 1.1x and 10x", '=IF(OR(F28<1.1,F28>10),"CHECK","OK")', "Outside that range the cost inputs are almost certainly wrong."),
    ]
    for i, (lab, form, mean) in enumerate(checks):
        r = 46 + i
        put(ws, f"A{r}", lab, f_body(9.5), align=A_LI)
        c = put(ws, f"B{r}", form, Font(name="Inter", size=9.5, bold=True, color=INK), align=A_C)
        put(ws, f"C{r}", mean, f_small(8.5), align=A_LI)

    rng = f"B46:B{45+len(checks)}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'B46="FIX"'],   font=Font(name="Inter", size=9.5, bold=True, color=BAD),  fill=F_BADBG))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'B46="CHECK"'], font=Font(name="Inter", size=9.5, bold=True, color=WARN), fill=F_WARNBG))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'B46="OK"'],    font=Font(name="Inter", size=9.5, bold=True, color=GOOD), fill=F_GOODBG))

    r = 46 + len(checks) + 1
    ws.merge_cells(f"A{r}:G{r}")
    verdict_cell(ws, f"A{r}",
                 f'=IF(COUNTIF({rng},"FIX")>0,"⛔ Something is wrong with the INPUT data. Fix the red rows before you send these numbers to anyone.",'
                 f'IF(COUNTIF({rng},"CHECK")>0,"⚠ Possible data problem on the amber rows — verify against the platform before reporting.",'
                 f'"✅ All checks passed. These numbers are safe to put in front of a client."))',
                 font=Font(name="Inter", size=10, bold=True, color=INK), fill_=F_PANEL)
    for c in range(1, 8):
        ws.cell(row=r, column=c).fill = F_PANEL
    ws.row_dimensions[r].height = 26

    ws.freeze_panes = "A5"
    return ws


# ============================================================ PROFIT BRIDGE
def sheet_profit_bridge(wb):
    ws = wb.create_sheet("Profit Bridge")
    gridlines_off(ws)
    std_widths(ws, {"A": 32, "B": 16, "C": 18, "D": 14, "E": 26, "F": 3,
                    "G": 10, "H": 20, "I": 20, "J": 22, "K": 30})

    title_block(ws, "Profit Bridge", "Where every unit of revenue actually goes — and what ROAS you need to make money.", CUR, last_col=5)

    section_bar(ws, 5, 1, 5, "  REVENUE → PROFIT, WATERFALL")
    for i, h in enumerate(["Step", "Per order", "This period", "% of revenue", "Share of revenue"]):
        put(ws, f"{L(1+i)}6", h, f_h2(9.5), F_HEAD, align=A_LI if i == 0 else A_R)

    rows = [
        ("Revenue",                       "=Calculator!F19",  M,   False),
        ("Less: COGS",                    "=Calculator!F20",  M,   False),
        ("Less: shipping & fulfilment",   "=Calculator!F21",  M,   False),
        ("Less: payment processing",      "=Calculator!F22",  M,   False),
        ("Less: returns & refunds",       "=Calculator!F23",  M,   False),
        ("Less: other variable costs",    "=Calculator!F24",  M,   False),
        ("= Contribution margin",         "=Calculator!F25",  M,   True),
        ("Less: ad spend",                "=-Calculator!B7",  M,   False),
        ("= Profit after ad spend",       "=Calculator!F31",  M,   True),
        ("Less: fixed costs",             "=-Calculator!F12", M,   False),
        ("Less: agency fee",              "=-Calculator!F13", M,   False),
        ("= NET PROFIT",                  "=Calculator!F34",  M,   True),
    ]
    for i, (lab, form, fmt, strong) in enumerate(rows):
        r = 7 + i
        put(ws, f"A{r}", lab, f_h2(10) if strong else f_body(10), F_PANEL if strong else None, align=A_LI)
        put(ws, f"B{r}", f"=IFERROR({form}/Calculator!$B$14,0)", f_input(10) if strong else f_calc(9.5),
            F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"C{r}", form, f_input(10) if strong else f_calc(9.5), F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"D{r}", f"=IFERROR({form}/Calculator!$F$19,0)", f_small(9), F_PANEL if strong else None, fmt=F_PCT, align=A_R)
        put(ws, f"E{r}", f'=REPT("█",MAX(0,ROUND(18*IFERROR({form}/Calculator!$F$19,0),0)))',
            Font(name="Inter", size=9, color=ACCENT_DK), align=A_LI)

    rng = f"C7:C{6+len(rows)}"
    ws.conditional_formatting.add(rng, CellIsRule(operator="lessThan", formula=["0"],
                                  font=Font(name="Inter", size=9.5, bold=True, color=BAD)))

    # ---- sensitivity table
    section_bar(ws, 21, 1, 5, "  WHAT ROAS DO YOU ACTUALLY NEED?  —  sensitivity at your current spend and costs")
    put(ws, "A22", "Same spend, same costs, different ROAS. This is the table that ends the \"is 2x good?\" argument.",
        f_italic(9.5))
    ws.merge_cells("A22:E22")

    hdrs = ["ROAS", "Revenue", "Contribution margin", "Profit after ads", "Verdict"]
    for i, h in enumerate(hdrs):
        put(ws, f"{L(1+i)}23", h, f_h2(9.5), F_HEAD, align=A_C if i == 0 else A_R)

    # 13 rows from 1.0x to 4.0x in 0.25 steps, then 4.5, 5, 6
    levels = [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5, 4.0, 5.0, 6.0]
    for i, lv in enumerate(levels):
        r = 24 + i
        rev  = f"(Calculator!$B$7*{lv})"
        orders = f"({rev}/IFERROR(Calculator!$B$31,1))"
        cm = (f"({rev}*(1-Calculator!$F$7-Calculator!$F$9-Calculator!$F$10)"
              f"-{orders}*(Calculator!$F$8+Calculator!$F$11))")
        put(ws, f"A{r}", lv, f_body(9.5), fmt=F_RATIO, align=A_C)
        put(ws, f"B{r}", f"={rev}", f_body(9.5), fmt=M, align=A_R)
        put(ws, f"C{r}", f"={cm}", f_body(9.5), fmt=M, align=A_R)
        put(ws, f"D{r}", f"={cm}-Calculator!$B$7", Font(name="Inter", size=9.5, bold=True, color=INK), fmt=M, align=A_R)
        put(ws, f"E{r}", f'=IF(D{r}<0,"Losing money — below cost",IF(D{r}<Calculator!$F$12+Calculator!$F$13,"Covers media only","Profitable after all costs"))',
            f_small(9), align=A_LI)
    ws.conditional_formatting.add(f"D24:D{23+len(levels)}", CellIsRule(operator="lessThan", formula=["0"],
                                  font=Font(name="Inter", size=9.5, bold=True, color=BAD), fill=F_BADBG))
    ws.conditional_formatting.add(f"D24:D{23+len(levels)}", CellIsRule(operator="greaterThanOrEqual", formula=["0"],
                                  font=Font(name="Inter", size=9.5, bold=True, color=GOOD), fill=F_GOODBG))

    r = 24 + len(levels) + 2
    ws.merge_cells(f"A{r}:E{r}")
    verdict_cell(ws, f"A{r}", '=Calculator!A38', font=Font(name="Inter", size=10, color=INK_SOFT), fill_=F_PANEL)
    for c in range(1, 6):
        ws.cell(row=r, column=c).fill = F_PANEL
    ws.row_dimensions[r].height = 30
    return ws


# =========================================================== PERIOD COMPARE
def sheet_period_compare(wb):
    ws = wb.create_sheet("Period Compare")
    gridlines_off(ws)
    std_widths(ws, {"A": 30, "B": 16, "C": 16, "D": 16, "E": 16, "F": 52,
                    "G": 3, "H": 30, "I": 18, "J": 18})

    title_block(ws, "Period Compare — why did ROAS move?",
                "ROAS = 1,000 × CTR × CVR × AOV ÷ CPM. This tab splits the change in ROAS into those four drivers, so you can name the cause instead of guessing.",
                CUR, last_col=6)

    section_bar(ws, 5, 1, 6, "  STEP 1 · ENTER TWO PERIODS")
    for i, h in enumerate(["Metric", "Period A (before)", "Period B (after)", "Change", "Change %", "Note"]):
        put(ws, f"{L(1+i)}6", h, f_h2(9.5), F_HEAD, align=A_LI if i in (0, 5) else A_C)

    inputs = [
        ("Period label",        "text", "e.g. Sep 2025",              "e.g. Oct 2025"),
        ("Ad spend",            M,      None, None),
        ("Impressions",         F_INT,  None, None),
        ("Clicks",              F_INT,  None, None),
        ("Purchases",           F_INT,  None, None),
        ("Revenue",             M,      None, None),
    ]
    for i, (lab, fmt, ta, tb) in enumerate(inputs):
        r = 7 + i
        put(ws, f"A{r}", lab, f_body(10), align=A_LI)
        put(ws, f"B{r}", ta, Font(name="Inter", size=10, bold=True, color=ACCENT_DK), F_INPUT, fmt=None if fmt == "text" else fmt, align=A_C, border=B_INPUT)
        put(ws, f"C{r}", tb, Font(name="Inter", size=10, bold=True, color=ACCENT_DK), F_INPUT, fmt=None if fmt == "text" else fmt, align=A_C, border=B_INPUT)

    # derived
    section_bar(ws, 14, 1, 6, "  STEP 2 · DERIVED DRIVERS")
    for i, h in enumerate(["Driver", "Period A", "Period B", "Change", "Change %", "What it means"]):
        put(ws, f"{L(1+i)}15", h, f_h2(9.5), F_HEAD, align=A_LI if i in (0, 5) else A_C)

    drivers = [
        ("CPM",       "=IFERROR(B8/B9*1000,0)",  "=IFERROR(C8/C9*1000,0)",  M,        "Cost of attention. Rising = auction pressure or audience saturation"),
        ("CTR",       "=IFERROR(B10/B9,0)",      "=IFERROR(C10/C9,0)",      F_PCT,    "Creative hook. Falling = fatigue or the wrong audience"),
        ("CVR",       "=IFERROR(B11/B10,0)",     "=IFERROR(C11/C10,0)",     F_PCT,    "Site conversion on paid clicks. Falling = landing page, offer, price or stock"),
        ("AOV",       "=IFERROR(B12/B11,0)",     "=IFERROR(C12/C11,0)",     M,        "Basket size. Falling = discounting, cheaper SKUs, or a bundle ending"),
        ("ROAS",      "=IFERROR(B12/B8,0)",      "=IFERROR(C12/C8,0)",      F_RATIO4, "The output these four drivers produce"),
    ]
    for i, (lab, fa, fb, fmt, note) in enumerate(drivers):
        r = 16 + i
        strong = lab == "ROAS"
        put(ws, f"A{r}", lab, f_h2(10) if strong else f_body(10), F_PANEL if strong else None, align=A_LI)
        put(ws, f"B{r}", fa, f_calc(9.5), F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"C{r}", fb, f_calc(9.5), F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"D{r}", f"=C{r}-B{r}", f_calc(9.5), F_PANEL if strong else None, fmt=fmt, align=A_R)
        put(ws, f"E{r}", f"=IFERROR(C{r}/B{r}-1,0)", f_calc(9.5), F_PANEL if strong else None, fmt=F_PCT, align=A_R)
        put(ws, f"F{r}", note, f_small(8.5), F_PANEL if strong else None, align=A_LI)

    # decomposition
    section_bar(ws, 23, 1, 6, "  STEP 3 · ATTRIBUTION  —  each driver's share of the total ROAS move")
    put(ws, "A24", "Sequential substitution: drivers are changed one at a time, in the order below, so the four "
                   "contributions add up exactly to the total change in ROAS. Order affects the split between "
                   "correlated drivers, so read the ranking, not the third decimal.", f_italic(8.5))
    ws.merge_cells("A24:F24")
    ws.row_dimensions[24].height = 24

    for i, h in enumerate(["Driver", "Effect on ROAS (points)", "% of total move", "Direction", "Verdict"]):
        put(ws, f"{L(1+i)}25", h, f_h2(9.5), F_HEAD, align=A_LI if i in (0, 3, 4) else A_C)
    ws.merge_cells("A25:B25"); ws["A25"].value = "Driver"; ws["A25"].alignment = A_LI

    # sequential substitution: ROAS = k*CTR*CVR*AOV/CPM
    # r0 = CB*DB*EB/AB ; r1 = CC*DB*EB/AB ; r2 = CC*DC*EB/AB ; r3 = CC*DC*EC/AB ; r4 = CC*DC*EC/AC
    decomp = [
        ("CTR (creative hook)",      "=1000*C16*B17*B18/1000/B19*1000", "=1000*B16*B17*B18/1000/B19*1000",
         "Creative response changed"),
        ("CVR (site conversion)",    None, None, "Site conversion changed"),
        ("AOV (basket size)",        None, None, "Order value changed"),
        ("CPM (cost of attention)",  None, None, "Media got cheaper or more expensive"),
    ]
    # explicit, readable sequential formulas
    # ROAS = 1000 * CTR * CVR * AOV / CPM   (all rates held as fractions)
    # Sequential substitution: CTR -> CVR -> AOV -> CPM.
    # Contribution = (value with that driver updated) - (value before it).
    seq = [
        ("CTR (creative hook)",
         "=IFERROR(1000*B17*B18*B19/B16,0)",      # before: all Period A
         "=IFERROR(1000*C17*B18*B19/B16,0)",      # after : CTR now Period B
         "Your creative pulled a different rate of clicks from the same impressions."),
        ("CVR (site conversion)",
         "=IFERROR(1000*C17*B18*B19/B16,0)",
         "=IFERROR(1000*C17*C18*B19/B16,0)",
         "The same clicks converted to orders at a different rate."),
        ("AOV (basket size)",
         "=IFERROR(1000*C17*C18*B19/B16,0)",
         "=IFERROR(1000*C17*C18*C19/B16,0)",
         "The average order value moved."),
        ("CPM (cost of attention)",
         "=IFERROR(1000*C17*C18*C19/B16,0)",
         "=IFERROR(C20,0)",                       # after : fully Period B
         "What you paid for impressions changed."),
    ]

    total_move_ref = "$C$20-$B$20"
    for i, (lab, fa, fb, note) in enumerate(seq):
        r = 26 + i
        put(ws, f"A{r}", lab, f_body(9.5), align=A_LI)
        # contribution = step_after - step_before   (hidden refs in H/I)
        put(ws, f"H{r}", fa, f_tiny(8), align=A_R)
        put(ws, f"I{r}", fb, f_tiny(8), align=A_R)
        ws.column_dimensions["H"].hidden = True
        ws.column_dimensions["I"].hidden = True
        put(ws, f"B{r}", f"=I{r}-H{r}", Font(name="Inter", size=10, bold=True, color=INK), fmt=F_2D, align=A_R)
        put(ws, f"C{r}", f"=IFERROR(B{r}/{total_move_ref},0)", f_calc(9.5), fmt=F_PCT, align=A_R)
        put(ws, f"D{r}", f'=IF(B{r}>0,"Helped","Hurt")', f_small(9), align=A_LI)
        put(ws, f"E{r}", note, f_small(8.5), align=A_LI)
    ws.merge_cells("D25:E25")
    ws["D25"].value = "Direction / what it means"
    ws["D25"].font = f_h2(9.5); ws["D25"].fill = F_HEAD; ws["D25"].alignment = A_LI
    ws.cell(row=25, column=4).fill = F_HEAD
    ws.cell(row=25, column=5).fill = F_HEAD
    # widen E since it now carries the note and D the direction
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 50

    r = 31
    put(ws, f"A{r}", "Total change in ROAS", f_h2(10), F_PANEL, align=A_LI)
    put(ws, f"B{r}", f"=SUM(B26:B29)", f_input(10), F_PANEL, fmt=F_2D, align=A_R)
    put(ws, f"C{r}", "=IFERROR(SUM(C26:C29),0)", f_small(9), F_PANEL, fmt=F_PCT, align=A_R)
    put(ws, f"D{r}", '=IF(B31>0,"ROAS improved","ROAS declined")', f_small(9), F_PANEL, align=A_LI)
    ws.merge_cells(f"E{r}:F{r}")
    put(ws, f"E{r}", "These four add up to the total change — nothing is left unexplained.", f_small(8.5), F_PANEL, align=A_LI)
    ws.cell(row=r, column=6).fill = F_PANEL
    ws.conditional_formatting.add("B26:B29", CellIsRule(operator="lessThan", formula=["0"],
                                  font=Font(name="Inter", size=10, bold=True, color=BAD), fill=F_BADBG))
    ws.conditional_formatting.add("B26:B29", CellIsRule(operator="greaterThan", formula=["0"],
                                  font=Font(name="Inter", size=10, bold=True, color=GOOD), fill=F_GOODBG))

    r = 33
    ws.merge_cells(f"A{r}:F{r}")
    verdict_cell(ws, f"A{r}",
        '="ROAS moved from "&ROUND(B20,2)&"x to "&ROUND(C20,2)&"x. The single biggest driver was "'
        '&IF(AND(ABS(B26)>=ABS(B27),ABS(B26)>=ABS(B28),ABS(B26)>=ABS(B29)),"CTR — creative response",'
        'IF(AND(ABS(B27)>=ABS(B28),ABS(B27)>=ABS(B29)),"CVR — how the site converted paid clicks",'
        'IF(ABS(B28)>=ABS(B29),"AOV — basket size","CPM — the cost of attention")))'
        '&" (worth "&ROUND(MAX(ABS(B26),ABS(B27),ABS(B28),ABS(B29))*IF(OR(B26<0,B27<0,B28<0,B29<0),-1,1),2)&" ROAS points). Lead your client update with that, not with the headline number."',
        font=Font(name="Inter", size=10, color=INK_SOFT), fill_=F_ACCENTBG)
    for c in range(1, 7):
        ws.cell(row=r, column=c).fill = F_ACCENTBG
    ws.row_dimensions[r].height = 32

    # worked example note
    r = 36
    put(ws, f"A{r}", "How to read this", f_h1(10.5))
    put(ws, f"A{r+1}",
        "If CPM rose and it was the only driver, that is a market conversation: you are paying more for the same "
        "attention, and the fix is creative, audience or offer — not 'turning things off'. If CVR or AOV moved, "
        "that is a business conversation: the site, the price, the stock. Naming which of the two you are in is "
        "what separates a report from an excuse.", f_body(9.5), align=A_LW)
    ws.merge_cells(f"A{r+1}:F{r+1}")
    ws.row_dimensions[r + 1].height = 46
    return ws


# ================================================================ BENCHMARKS
def sheet_benchmarks(wb):
    ws = wb.create_sheet("Benchmarks")
    gridlines_off(ws)
    std_widths(ws, {"A": 26, "B": 12, "C": 14, "D": 14, "E": 14, "F": 14, "G": 12, "H": 58})

    title_block(ws, "Benchmarks", "Editable thresholds. The status column on every report reads from here.", CUR, last_col=8)

    put(ws, "A4", "⚠ Read this first:", Font(name="Inter", size=10, bold=True, color=BAD))
    put(ws, "B4", "The numbers below are starting points so the status column works on day one — they are not "
                  "industry truth. Replace them with your own trailing 90-day average per account as soon as you "
                  "have it. Your own history is the only benchmark that pays rent.", f_body(9.5), align=A_LW)
    ws.merge_cells("B4:H4")
    ws.row_dimensions[4].height = 30

    for i, h in enumerate(["Metric", "Your value", "Weak", "Watch", "Target", "Strong", "Status", "If you're below target, look here first"]):
        put(ws, f"{L(1+i)}6", h, f_h2(9.5), F_HEAD, align=A_LI if i in (0, 7) else A_C)

    # direction: Up = higher is better, Down = lower is better
    rows = [
        ("CPM",                    "=Calculator!$B$19", M,     "Down", 190, 140, 110, 80,
         "Auction pressure, audience saturation, or a broad-targeting test diluting the mix."),
        ("CPC",                    "=Calculator!$B$20", M,     "Down", 14, 9, 6, 3.5,
         "Mostly CPM plus CTR. If CPC is high but CTR is fine, look at placement and audience."),
        ("CTR",                    "=Calculator!$B$21", F_PCT, "Up",   0.008, 0.012, 0.018, 0.028,
         "Creative hook. First 3 seconds of video, first line of primary text."),
        ("Click → Landing page %", "=Calculator!$B$23", F_PCT, "Up",   0.45, 0.6, 0.72, 0.85,
         "Page speed and mobile load. This is a technical problem, not a media one."),
        ("Landing page → ATC %",   "=Calculator!$B$24", F_PCT, "Up",   0.03, 0.055, 0.08, 0.13,
         "Product page: price positioning, imagery, reviews, delivery promise."),
        ("ATC → Checkout %",       "=Calculator!$B$25", F_PCT, "Up",   0.18, 0.3, 0.45, 0.6,
         "Shipping cost, surprise fees, forced account creation."),
        ("Checkout → Purchase %",  "=Calculator!$B$26", F_PCT, "Up",   0.35, 0.5, 0.65, 0.78,
         "Payment methods, COD availability, trust badges, retargeting coverage."),
        ("Click → Purchase CVR %", "=Calculator!$B$27", F_PCT, "Up",   0.008, 0.015, 0.025, 0.04,
         "The end-to-end site rate on paid clicks. Compare month to month, not to strangers."),
        ("Frequency",              "=Calculator!$B$22", F_2D,  "Down", 5.0, 3.5, 2.4, 1.5,
         "Creative fatigue. Above target, refresh before you scale."),
        ("AOV",                    "=Calculator!$B$31", M,     "Up",   0, 0, 0, 0,
         "REPLACE these four cells with this client's real AOV range — it is account-specific."),
        ("Revenue per 1,000 impressions", "=Calculator!$B$33", M, "Up", 0, 0, 0, 0,
         "REPLACE. The cleanest single end-to-end measure of media efficiency."),
        ("ROAS",                   "=Calculator!$B$32", F_RATIO4, "Up", 0, 0, 0, 0,
         "REPLACE with realistic tiers for this account. Never set a target below breakeven ROAS."),
        ("Breakeven ROAS",         "=Calculator!$F$28", F_RATIO4,"Down", 0, 0, 0, 0,
         "This one is calculated from the client's own margin — do not overwrite it."),
        ("POAS (profit on ad spend)","=Calculator!$F$32", F_RATIO4,"Up", 0, 0, 0, 0,
         "Profit per unit of spend. The number to move when ROAS is already acceptable."),
    ]

    for i, (lab, val, fmt, direction, weak, watch, target, strong, action) in enumerate(rows):
        r = 7 + i
        put(ws, f"A{r}", lab, f_body(9.5), align=A_LI)
        put(ws, f"B{r}", val, Font(name="Inter", size=10, bold=True, color=INK), fmt=fmt, align=A_C)
        for j, v in enumerate([weak, watch, target, strong]):
            put(ws, f"{L(3+j)}{r}", v, f_small(9), fmt=fmt, align=A_C)
        put(ws, f"G{r}", None, f_calc(9), align=A_C)
        put(ws, f"H{r}", action, f_small(8.5), align=A_LI)

    # simpler, correct status formula per row (avoid clever tricks)
    for i, (lab, val, fmt, direction, weak, watch, target, strong, action) in enumerate(rows):
        r = 7 + i
        if direction == "Up":
            f = (f'=IF($B{r}=0,"—",IF($B{r}>={L(6)}{r},"Strong",IF($B{r}>={L(5)}{r},"Target",'
                 f'IF($B{r}>={L(4)}{r},"Watch","Weak"))))')
        else:
            f = (f'=IF($B{r}=0,"—",IF($B{r}<={L(6)}{r},"Strong",IF($B{r}<={L(5)}{r},"Target",'
                 f'IF($B{r}<={L(4)}{r},"Watch","Weak"))))')
        ws[f"G{r}"] = f

    rng = f"G7:G{6+len(rows)}"
    for tag, fnt, fl in [("Strong", Font(name="Inter", size=9, bold=True, color=GOOD), F_GOODBG),
                         ("Target", Font(name="Inter", size=9, bold=True, color=GOOD), F_GOODBG),
                         ("Watch",  Font(name="Inter", size=9, bold=True, color=WARN), F_WARNBG),
                         ("Weak",   Font(name="Inter", size=9, bold=True, color=BAD),  F_BADBG)]:
        ws.conditional_formatting.add(rng, FormulaRule(formula=[f'$G7="{tag}"'], font=fnt, fill=fl))

    # direction legend
    r = 7 + len(rows) + 1
    put(ws, f"A{r}", "How status is decided", f_h1(10))
    put(ws, f"A{r+1}", "Higher is better (CTR, CVR, AOV, ROAS, POAS): Strong ≥ column F, Target ≥ E, Watch ≥ D, below D = Weak.",
        f_small(9))
    put(ws, f"A{r+2}", "Lower is better (CPM, CPC, Frequency, Breakeven ROAS): the same logic mirrored.",
        f_small(9))
    return ws


# ========================================================= METRIC DICTIONARY
def sheet_dictionary(wb):
    ws = wb.create_sheet("Metric Dictionary")
    gridlines_off(ws)
    std_widths(ws, {"A": 26, "B": 40, "C": 52, "D": 52})

    title_block(ws, "Metric Dictionary", "One shared definition per metric — for you, the client, and the AI prompts. If a number isn't defined here, don't report it.", None, last_col=4)

    for i, h in enumerate(["Metric", "How it is calculated", "What it actually tells you", "How it is most often misused"]):
        put(ws, f"{L(1+i)}5", h, f_h2(9.5), F_HEAD, align=A_LI)

    rows = [
        ("Spend", "Sum of ad spend for the period", "Money out the door on media only — exclude agency fees and tooling.",
         "Bundling management fees into spend, which makes every efficiency metric worse than reality."),
        ("Impressions", "Counted each time the ad renders", "Volume of attention bought.",
         "Using impressions as a success metric on its own. Cheap impressions nobody acts on are not a win."),
        ("Reach", "Unique people who saw the ad", "How many actual humans, deduplicated.",
         "Adding reach across months or platforms. Reach does not sum — deduplicated people overlap."),
        ("Frequency", "Impressions ÷ Reach", "Average number of times each person saw you.",
         "Averaging the daily frequency column. Average the ratio, or use total impressions ÷ total reach."),
        ("CPM", "Spend ÷ Impressions × 1,000", "What you paid for 1,000 impressions — the price of attention.",
         "Calling a rising CPM your fault. It is often auction-wide. Check CTR and CVR before you blame the account."),
        ("CTR", "Clicks ÷ Impressions", "How well the creative earns a click.",
         "Mixing 'all clicks' with 'link clicks'. Outbound/link clicks only, every time, or the number drifts."),
        ("CPC", "Spend ÷ Clicks", "Cost of a visit to the site.",
         "Optimising CPC in isolation — cheaper clicks from a worse audience convert worse."),
        ("Landing page view (LPV)", "Page loaded after a click", "How many clicks actually arrived on the site.",
         "Ignoring the gap between clicks and LPVs. A large gap is a page-speed problem masquerading as a media problem."),
        ("Add to cart (ATC)", "Product added to cart", "Cheap, early intent signal.",
         "Treating ATC as a proxy for revenue. High ATC with low checkout = shipping cost shock."),
        ("Initiate checkout (IC)", "Checkout started", "The last step before money changes hands.",
         "Assuming IC → Purchase is a media metric. It is almost always a payment or trust issue."),
        ("Purchases", "Attributed orders in the platform window", "Orders the platform takes credit for.",
         "Comparing platforms without matching attribution windows. 7-day-click on Meta vs 7-day on TikTok is fine; 1-day vs 7-day is not."),
        ("Purchases Value / Revenue", "Sum of order value in the window", "The revenue side of ROAS.",
         "Using the platform's purchase value as the client's bank statement. Platform value is claim, not cash. Reconcile monthly."),
        ("ROAS", "Revenue ÷ Spend", "Revenue returned per unit of ad spend.",
         "Reporting it with no breakeven context. A 3x ROAS on a 35% margin business loses money."),
        ("Breakeven ROAS", "1 ÷ Contribution margin %", "The ROAS at which you make exactly zero profit on ads.",
         "Using a generic 2x or 3x rule of thumb. Breakeven is a property of the client's cost structure, not the industry."),
        ("Contribution margin", "Revenue − COGS − shipping − fees − returns − other variable costs", "The money left from a sale to pay for ads and overhead.",
         "Confusing it with gross margin. Contribution margin is what ad spend is actually competing against."),
        ("AOV", "Revenue ÷ Purchases", "Average basket size.",
         "Reporting AOV without saying whether it moved because of price, mix, or discounting."),
        ("CPA / Cost per purchase", "Spend ÷ Purchases", "Cost to acquire one order.",
         "Judging it without AOV and margin. CPA only means something relative to contribution per order."),
        ("CVR (purchase)", "Purchases ÷ Clicks", "How well paid traffic converts on site.",
         "Benchmarking against another store's CVR. Compare to this account's own history."),
        ("POAS", "(Contribution margin − Spend) ÷ Spend", "Profit returned per unit of ad spend.",
         "Ignoring it. When a client says 'make me more money', POAS is the metric, not ROAS."),
        ("MER (blended ROAS)", "Total revenue (incl. organic) ÷ ad spend", "Whether the business as a whole is efficient at buying growth.",
         "Using MER when organic revenue is unstable — it swings on things media doesn't control."),
        ("Attribution window", "The lookback period credited to an ad", "How generous the platform is being with its own credit.",
         "Changing the window between months, then presenting the change as performance. Fix the window and note it on the report."),
    ]
    for i, (a, b, c, d) in enumerate(rows):
        r = 6 + i
        put(ws, f"A{r}", a, Font(name="Inter", size=9.5, bold=True, color=INK), align=A_LW)
        put(ws, f"B{r}", b, f_body(9), align=A_LW)
        put(ws, f"C{r}", c, f_body(9), align=A_LW)
        put(ws, f"D{r}", d, Font(name="Inter", size=9, color=BAD), align=A_LW)
        ws.row_dimensions[r].height = 40
    ws.freeze_panes = "A6"
    return ws


# ==================================================================== BUILD
def build():
    wb = Workbook()
    wb.remove(wb.active)
    sheet_start(wb)
    sheet_calculator(wb)
    sheet_profit_bridge(wb)
    sheet_period_compare(wb)
    sheet_benchmarks(wb)
    sheet_dictionary(wb)
    wb.active = 0
    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
