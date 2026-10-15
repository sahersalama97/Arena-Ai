"""
Builds the monthly report PDF.

  python3 "_build/build_pdf.py"            -> both files
  python3 "_build/build_pdf.py" sample     -> samples/Sample_Monthly_Report.pdf
  python3 "_build/build_pdf.py" template   -> 04_Monthly_Report_PDF_Template.pdf

The two files share one layout. `sample` is filled with the kit's worked example;
`template` replaces every number with a labelled blank you can fill by hand.

To use it with your own numbers, edit the DATA dict in monthly_data() (or point it
at a JSON file) and re-run.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fpdf import FPDF
from fpdf.enums import XPos, YPos

import sample_data as SD

HERE  = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(HERE)
FONTS = os.path.join(HERE, "fonts")

# ------------------------------------------------------------------ palette
INK      = (17, 24, 39)
INK_SOFT = (55, 65, 81)
MUTED    = (107, 114, 128)
HAIR     = (229, 231, 235)
PANEL    = (243, 244, 246)
WHITE    = (255, 255, 255)
ACCENT   = (249, 115, 22)
ACCENT_D = (194, 65, 12)
ACCENT_BG= (255, 247, 237)
GOOD     = (21, 128, 61)
GOOD_BG  = (220, 252, 231)
WARN     = (180, 83, 9)
BAD      = (185, 28, 28)

PW, PH = 210, 297
ML, MR = 18, 18
CW = PW - ML - MR


# ==================================================================== data
def monthly_data():
    rows = SD.fundamentals_rows()
    adr  = SD.ad_rows(rows)
    c  = SD.derive(SD.totals(rows, SD.CUR_START, SD.CUR_END))
    p  = SD.derive(SD.totals(rows, SD.CMP_START, SD.CMP_END))
    cm = SD.derive(SD.totals(rows, SD.CUR_START, SD.CUR_END, "Meta"))
    pm = SD.derive(SD.totals(rows, SD.CMP_START, SD.CMP_END, "Meta"))
    ct = SD.derive(SD.totals(rows, SD.CUR_START, SD.CUR_END, "TikTok"))
    pt = SD.derive(SD.totals(rows, SD.CMP_START, SD.CMP_END, "TikTok"))
    be = SD.breakeven_roas(c["aov"])
    cm_pct = 1 - SD.COGS_PCT - SD.OTHER_VAR_PCT - SD.SHIP_PER_ORDER / c["aov"]
    return dict(
        brand=SD.BRAND, period="September 2026", compare="August 2026",
        prepared_by=SD.PREPARED_BY, currency="EGP",
        breakeven=be, cm_pct=cm_pct,
        profit=c["rev"] * cm_pct - c["spend"],
        poas=(c["rev"] * cm_pct - c["spend"]) / c["spend"],
        combined=dict(spend=c["spend"], pur=c["pur"], cpp=c["cpp"], rev=c["rev"],
                      roas=c["roas"], aov=c["aov"], imp=c["imp"], clicks=c["clicks"],
                      ctr=c["ctr"], cpm=c["cpm"], freq=c["freq"],
                      atc=c["atc"], ic=c["ic"]),
        prev=dict(spend=p["spend"], pur=p["pur"], cpp=p["cpp"], rev=p["rev"],
                  roas=p["roas"], aov=p["aov"]),
        meta=dict(spend=cm["spend"], pur=cm["pur"], cpp=cm["cpp"], rev=cm["rev"],
                  roas=cm["roas"], aov=cm["aov"], ctr=cm["ctr"], imp=cm["imp"],
                  freq=cm["freq"], cpm=cm["cpm"], lpv_rate=cm["lpv_rate"],
                  roas_prev=pm["roas"], cpp_prev=pm["cpp"]),
        tiktok=dict(spend=ct["spend"], pur=ct["pur"], cpp=ct["cpp"], rev=ct["rev"],
                    roas=ct["roas"], aov=ct["aov"], ctr=ct["ctr"], imp=ct["imp"],
                    freq=ct["freq"], cpm=ct["cpm"], roas_prev=pt["roas"]),
        funnel=[("Impressions", c["imp"], None, None),
                ("Link clicks", c["clicks"], c["ctr"], "of impressions"),
                ("Add to cart", c["atc"], c["atc"] / c["clicks"], "of clicks"),
                ("Checkout started", c["ic"], c["ic"] / c["atc"], "of carts"),
                ("Purchases", c["pur"], c["pur"] / c["ic"], "of checkouts")],
        weekly=SD.weekly_rows(rows),
        top_ads=SD.aggregate_ads(adr, by="ad", top=5),
        top_creatives=SD.aggregate_ads(adr, by="creative", top=5),
    )


def blank_data():
    """Same shape, but every value replaced by a blank so nothing is pre-filled."""
    d = monthly_data()
    d["brand"] = "[ CLIENT NAME ]"
    d["period"] = "[ REPORTING MONTH ]"
    d["compare"] = "[ COMPARISON MONTH ]"
    d["prepared_by"] = "[ YOUR AGENCY ]"
    d["breakeven"] = ""
    d["cm_pct"] = ""
    d["profit"] = ""
    d["poas"] = ""
    blanks = {}
    for k in ("spend", "pur", "cpp", "rev", "roas", "aov", "imp", "clicks", "ctr",
              "cpm", "freq", "atc", "ic"):
        blanks[k] = ""
    for key in ("combined", "prev", "meta", "tiktok"):
        d[key] = {k: "" for k in d[key]}
    # funnel keeps its labels and ordering, loses its numbers
    d["funnel"] = [(lab, "", None, None) for lab, _v, _r, _rl in d["funnel"]]
    # weekly keeps its rhythm but loses the figures
    d["weekly"] = [(lab, "", "", "", "", "", "") for lab, *_ in d["weekly"]]
    d["top_ads"] = [("", "", "", "", "", "", "") for _ in range(5)]
    d["top_creatives"] = [("", "", "", "", "", "", "") for _ in range(5)]
    return d


# ==================================================================== pdf
class Report(FPDF):
    def __init__(self, data, mode):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.data, self.mode = data, mode
        self.set_margins(ML, 16, MR)
        self.set_auto_page_break(False)
        self.add_font("Inter",   "",  os.path.join(FONTS, "Inter-Regular.ttf"))
        self.add_font("Inter",   "B", os.path.join(FONTS, "Inter-Bold.ttf"))
        self.add_font("Inter",   "I", os.path.join(FONTS, "Inter-Italic.ttf"))
        self.add_font("InterM",  "",  os.path.join(FONTS, "Inter-Medium.ttf"))
        self.add_font("InterSB", "",  os.path.join(FONTS, "Inter-SemiBold.ttf"))
        self.add_font("InterEB", "",  os.path.join(FONTS, "Inter-ExtraBold.ttf"))

    # ---------------------------------------------------------- primitives
    def txt(self, x, y, s, font="Inter", style="", size=10, color=INK_SOFT, w=None):
        self.set_font(font, style, size)
        self.set_text_color(*color)
        self.set_xy(x, y)
        if w is None:
            self.cell(0, size * 0.42, str(s), new_x=XPos.RIGHT, new_y=YPos.TOP)
        else:
            self.multi_cell(w, size * 0.46, str(s), new_x=XPos.LEFT, new_y=YPos.TOP)

    def band(self, y, h, color):
        self.set_fill_color(*color)
        self.rect(0, y, PW, h, style="F")

    def rule(self, x, y, w, color=HAIR, t=0.25):
        self.set_draw_color(*color)
        self.set_line_width(t)
        self.line(x, y, x + w, y)

    def bar(self, x, y, w, h, pct, color=ACCENT, bg=PANEL):
        pct = max(0.0, min(1.0, pct))
        self.set_fill_color(*bg)
        self.rect(x, y, w, h, style="F")
        self.set_fill_color(*color)
        self.rect(x, y, w * pct, h, style="F")

    def eyebrow(self, x, y, s, color=ACCENT):
        self.txt(x, y, s.upper(), "InterSB", "", 7.5, color)

    def page_title(self, kicker, title):
        self.eyebrow(ML, 16, kicker)
        self.txt(ML, 21, title, "InterEB", "", 21, INK)
        self.rule(ML, 33, CW)

    def stamp(self, n):
        self.rule(ML, PH - 16, CW)
        self.txt(ML, PH - 13, f"{self.data['brand']}  ·  {self.data['period']}",
                 "Inter", "", 7.5, MUTED)
        self.txt(PW - MR - 30, PH - 13, f"Page {n} of 5", "Inter", "", 7.5, MUTED)

    # ------------------------------------------------------------- helpers
    def money(self, v, dec=0):
        if v in (None, ""):
            return "[   ]"
        return f"{v:,.{dec}f}"

    def pct(self, v, dec=2):
        if v in (None, ""):
            return "[  ]"
        return f"{v * 100:.{dec}f}%"

    def ratio(self, v):
        if v in (None, ""):
            return "[  ]"
        return f"{v:.2f}x"

    def is_blank(self):
        return self.mode == "template"


# ============================================================== page: cover
def page_cover(p):
    d = p.data
    p.add_page()
    p.band(0, 118, INK)

    p.eyebrow(ML, 20, "Monthly performance report", ACCENT)
    p.txt(ML, 28, d["brand"], "InterEB", "", 27, WHITE)
    p.txt(ML, 42, f'{d["period"]}   ·   compared with {d["compare"]}', "Inter", "", 11.5, (209, 213, 219))

    # headline ROAS block
    if p.is_blank():
        val = "[  .  x ]"
    else:
        val = f'{d["combined"]["roas"]:.2f}x'
    p.txt(ML, 62, "RETURN ON AD SPEND", "InterSB", "", 8, (156, 163, 175))
    p.txt(ML, 68, val, "InterEB", "", 44, WHITE)
    sub = ("against a breakeven of [  .  x ]" if p.is_blank()
           else f'against a breakeven of {d["breakeven"]:.2f}x')
    p.txt(ML, 89, sub, "InterM", "", 10.5, (209, 213, 219))

    # headline stats inside the band
    stats = [("Ad spend",        p.money(d["combined"]["spend"]) + ("" if p.is_blank() else f' {d["currency"]}')),
             ("Revenue",         p.money(d["combined"]["rev"]) + ("" if p.is_blank() else f' {d["currency"]}')),
             ("Purchases",       p.money(d["combined"]["pur"])),
             ("Average order",   p.money(d["combined"]["aov"]) + ("" if p.is_blank() else f' {d["currency"]}'))]
    x = ML
    for lab, v in stats:
        p.txt(x, 100, lab.upper(), "InterSB", "", 7.5, (156, 163, 175))
        p.txt(x, 105, v, "InterSB", "", 15, WHITE)
        x += CW / 4

    # below the band
    y = 134
    p.txt(ML, y, "Every number in this report traces back to a daily row pulled directly from Meta's and "
                 "TikTok's own reporting APIs. There is no manual entry step, and nothing is estimated.",
          "Inter", "I", 9, MUTED, w=CW)
    y += 16
    p.rule(ML, y, CW)
    y += 6
    p.txt(ML, y, "PREPARED BY", "InterSB", "", 7.5, MUTED)
    p.txt(ML, y + 5, d["prepared_by"], "InterM", "", 11, INK)
    p.txt(PW - MR - 70, y, "REPORTING WINDOW", "InterSB", "", 7.5, MUTED)
    p.txt(PW - MR - 70, y + 5, d["period"], "InterM", "", 11, INK)

    # breakeven explainer
    y += 24
    p.set_fill_color(*ACCENT_BG)
    p.rect(ML, y, CW, 44, style="F")
    p.set_fill_color(*ACCENT)
    p.rect(ML, y, 2.2, 44, style="F")
    p.txt(ML + 8, y + 7, "THE ONLY NUMBER THAT MATTERS", "InterSB", "", 8, ACCENT_D)
    if p.is_blank():
        body = ("Breakeven ROAS for this business is [  .  x ]. Below that line, every sale loses money "
                "before you have paid for ads. Everything in this report is read against that line, not "
                "against an industry average.")
    else:
        body = (f'Breakeven ROAS for this business is {d["breakeven"]:.2f}x — calculated from the client\'s own '
                f'cost structure ({d["cm_pct"]*100:.1f}% contribution margin), not from an industry average. '
                f'This month the account returned {d["combined"]["roas"]:.2f}x, which is '
                f'{((d["combined"]["roas"]/d["breakeven"])-1)*100:.0f}% above breakeven.')
    p.txt(ML + 8, y + 14, body, "Inter", "", 9.5, INK_SOFT, w=CW - 16)

    p.stamp(1)


# ======================================================== page: performance
def page_performance(p):
    d = p.data
    p.add_page()
    p.page_title("page two", "Performance at a glance")

    y = 40
    p.txt(ML, y, "Combined results against last period", "InterM", "", 10.5, INK)

    y += 8
    cols = [ML, ML + 62, ML + 96, ML + 130, ML + 160]
    for c, h in zip(cols, ["", "Meta", "TikTok", "Combined", "Last month"]):
        p.txt(c, y, h.upper(), "InterSB", "", 7.5, MUTED)
    y += 5
    p.rule(ML, y, CW, INK, 0.4)

    m, t, c, pv = d["meta"], d["tiktok"], d["combined"], d["prev"]
    M0 = lambda v: p.money(v)
    rows = [
        ("Ad spend",          m["spend"], t["spend"], c["spend"], pv["spend"], M0,  False),
        ("Purchases",         m["pur"],   t["pur"],   c["pur"],   pv["pur"],   M0,  False),
        ("Cost per purchase", m["cpp"],   t["cpp"],   c["cpp"],   pv["cpp"],   M0,  False),
        ("Revenue",           m["rev"],   t["rev"],   c["rev"],   pv["rev"],   M0,  True),
        ("ROAS",              m["roas"],  t["roas"],  c["roas"],  pv["roas"],  p.ratio, False),
        ("Average order",     m["aov"],   t["aov"],   c["aov"],   pv["aov"],   M0,  False),
    ]
    for lab, a_, b_, c_, d_, fmt, bold in rows:
        y += 9
        p.txt(ML, y + 2.4, lab, "InterSB" if bold else "Inter", "", 9.5, INK if bold else INK_SOFT)
        for cx, v in zip(cols[1:], [a_, b_, c_, d_]):
            p.txt(cx, y + 2.4, fmt(v), "InterM" if bold else "Inter", "", 9.5,
                  INK if bold else INK_SOFT, w=34)
        p.rule(ML, y + 8, CW)
    y += 9
    p.rule(ML, y, CW, INK, 0.4)

    # single, non-overlapping breakeven verdict under the table
    y += 6
    if p.is_blank():
        verdict = "ROAS of [  .  x ] against a breakeven of [  .  x ]  —  [ above / below ] breakeven."
    else:
        delta = ((c["roas"] / d["breakeven"]) - 1) * 100
        verdict = (f'ROAS of {c["roas"]:.2f}x against a breakeven of {d["breakeven"]:.2f}x — '
                   f'{abs(delta):.0f}% {"above" if delta >= 0 else "below"} breakeven.')
    p.set_fill_color(*ACCENT_BG)
    p.rect(ML, y, CW, 11, style="F")
    p.txt(ML + 6, y + 3.4, verdict, "InterSB", "", 9.5, ACCENT_D, w=CW - 12)

    # where the money went
    y += 22
    p.txt(ML, y, "Where the budget went", "InterM", "", 10.5, INK)
    y += 8
    for h, cx in [("Channel", ML), ("Spend", ML + 26), ("ROAS", ML + 76),
                  ("Share of budget", ML + 100)]:
        p.txt(cx, y, h.upper(), "InterSB", "", 7.5, MUTED)
    y += 5
    p.rule(ML, y, CW, INK, 0.4)
    total_spend = (c["spend"] or 1) if not p.is_blank() else 1
    for lab, sp, ro, col in [("Meta", m["spend"], m["roas"], ACCENT),
                             ("TikTok", t["spend"], t["roas"], (59, 130, 246))]:
        y += 8.4
        p.txt(ML, y + 1.6, lab, "InterM", "", 9.5, INK)
        p.txt(ML + 26, y + 1.6, p.money(sp) + ("" if p.is_blank() else f' {d["currency"]}'),
              "Inter", "", 9.5, INK_SOFT, w=48)
        p.txt(ML + 76, y + 1.6, p.ratio(ro), "Inter", "", 9.5, INK_SOFT, w=22)
        share = (sp / total_spend) if not p.is_blank() else 0.0
        p.bar(ML + 100, y + 2.2, 56, 3.4, share, col)
        p.txt(ML + 160, y + 1.6, p.pct(share, 0) if not p.is_blank() else "[  ]",
              "Inter", "", 9, MUTED, w=20)
        p.rule(ML, y + 7.4, CW)

    # efficiency
    y += 18
    p.txt(ML, y, "Efficiency", "InterM", "", 10.5, INK)
    y += 8
    eff = [("CPM", p.money(c["cpm"]) + ("" if p.is_blank() else f' {d["currency"]}'),
            "cost of 1,000 impressions"),
           ("Click-through rate", p.pct(c["ctr"]), "how well the creative earns a click"),
           ("Frequency", f'{c["freq"]:.2f}' if not p.is_blank() else "[  .  ]",
            "average times each person saw you"),
           ("Click-to-purchase",
            p.pct(c["pur"] / c["clicks"]) if not p.is_blank() else "[  ]",
            "how well the site converted paid clicks"),
           ("Revenue per 1,000 impressions",
            (p.money(c["rev"] / c["imp"] * 1000) + f' {d["currency"]}') if not p.is_blank() else "[        ]",
            "end-to-end media efficiency")]
    for lab, val, note in eff:
        p.txt(ML, y, lab, "Inter", "", 9.5, INK_SOFT)
        p.txt(ML + 66, y, val, "InterSB", "", 9.5, INK, w=34)
        p.txt(ML + 104, y, note, "Inter", "", 8.5, MUTED, w=70)
        y += 7.4

    p.stamp(2)


# ============================================================= page: funnel
def page_funnel(p):
    d = p.data
    p.add_page()
    p.page_title("page three", "The funnel, step by step")

    y = 40
    p.txt(ML, y, "Where people drop out between seeing an ad and buying something. The weakest step is the one "
                 "to fix first — everything upstream of it is being wasted.", "Inter", "", 9.5, INK_SOFT, w=CW)
    y += 12
    p.txt(ML, y, "Step", "InterSB", "", 7.5, MUTED)
    p.txt(ML + 46, y, "Volume", "InterSB", "", 7.5, MUTED)
    p.txt(ML + 76, y, "Conversion from the step above", "InterSB", "", 7.5, MUTED)
    y += 4
    p.rule(ML, y, CW, INK, 0.4)

    c = d["combined"]
    for lab, val, rate, rate_lab in d["funnel"]:
        y += 12
        p.txt(ML, y, lab, "InterM", "", 10, INK)
        p.txt(ML + 46, y, p.money(val) if not p.is_blank() else "[          ]",
              "Inter", "", 9.5, INK_SOFT, w=28)
        if rate is None:
            p.txt(ML + 76, y, "seen by " + p.money(val) if not p.is_blank() else "[     ]",
                  "Inter", "", 8.5, MUTED)
        else:
            frac = min(1.0, max(rate, 0.012)) if not p.is_blank() else 0.4
            p.bar(ML + 76, y + 0.8, 52, 3.6, frac, ACCENT, bg=PANEL)
            p.txt(ML + 132, y, p.pct(rate, 1) if not p.is_blank() else "[  ]",
                  "InterSB", "", 9.5, INK, w=20)
            p.txt(ML + 152, y, rate_lab, "Inter", "", 8, MUTED)
        p.rule(ML, y + 7.6, CW)
    y += 10

    # ---- the weakest post-click step, with real arithmetic behind it
    if p.is_blank():
        box = ("Weakest step this month: [                                 ] at [      ]%, against a target of "
               "[      ]%. A 20% relative improvement at that single step, at the same spend, is worth roughly "
               "[          ] " + d["currency"] + " in additional revenue.")
    else:
        steps = [("add to cart", c["atc"], c["clicks"]),
                 ("checkout started", c["ic"], c["atc"]),
                 ("purchases", c["pur"], c["ic"])]
        wname, wnum, wden = min(steps, key=lambda t: (t[1] / t[2]) if t[2] else 1)
        wrate = wnum / wden
        # hold everything above the weak step constant; lift its rate by 20% relative
        extra_units = wden * wrate * 0.20
        downstream = c["pur"] / wnum if wnum else 0     # purchases per unit at the weak step
        extra_pur = extra_units * downstream
        extra_rev = extra_pur * c["aov"]
        box = (f"Weakest step this month: {wname} at {wrate*100:.1f}% ({p.money(wnum)} of {p.money(wden)}). "
               f"A 20% relative lift at that one step, at the same spend, would put roughly {extra_pur:,.0f} more "
               f"orders through the same funnel — about {extra_rev:,.0f} {d['currency']} of additional revenue. "
               f"That is the argument for fixing the page before raising the budget.")
    p.set_fill_color(*PANEL)
    p.rect(ML, y, CW, 30, style="F")
    p.set_fill_color(*ACCENT)
    p.rect(ML, y, 2.2, 30, style="F")
    p.txt(ML + 8, y + 6, box, "Inter", "", 9, INK_SOFT, w=CW - 16)
    y += 40

    # ---- platform detail
    p.txt(ML, y, "Platform detail", "InterM", "", 10.5, INK)
    y += 7
    for h, cx in [("", ML), ("Meta", ML + 62), ("TikTok", ML + 100), ("Combined", ML + 138)]:
        p.txt(cx, y, h.upper(), "InterSB", "", 7.5, MUTED)
    y += 4
    p.rule(ML, y, CW, INK, 0.4)
    m, t = d["meta"], d["tiktok"]
    detail = [
        ("Spend",         m["spend"], t["spend"], c["spend"], lambda v: p.money(v)),
        ("Impressions",   m["imp"],   t["imp"],   c["imp"],   lambda v: p.money(v)),
        ("CTR",           m["ctr"],   t["ctr"],   c["ctr"],   lambda v: p.pct(v)),
        ("CPM",           m["cpm"],   t["cpm"],   c["cpm"],   lambda v: p.money(v)),
        ("Frequency",     m["freq"],  t["freq"],  c["freq"],  lambda v: f"{v:.2f}"),
        ("Purchases",     m["pur"],   t["pur"],   c["pur"],   lambda v: p.money(v)),
        ("Cost/purchase", m["cpp"],   t["cpp"],   c["cpp"],   lambda v: p.money(v)),
        ("Revenue",       m["rev"],   t["rev"],   c["rev"],   lambda v: p.money(v)),
        ("ROAS",          m["roas"],  t["roas"],  c["roas"],  lambda v: p.ratio(v)),
        ("Average order", m["aov"],   t["aov"],   c["aov"],   lambda v: p.money(v)),
    ]
    for lab, a_, b_, c_, fmt in detail:
        bold = lab in ("ROAS", "Revenue")
        y += 8.0
        p.txt(ML, y + 1.8, lab, "InterSB" if bold else "Inter", "", 9, INK if bold else INK_SOFT)
        for cx, v in zip([ML + 62, ML + 100, ML + 138], [a_, b_, c_]):
            p.txt(cx, y + 1.8, fmt(v) if not p.is_blank() else "[     ]",
                  "InterM" if bold else "Inter", "", 9, INK if bold else INK_SOFT)
        p.rule(ML, y + 7.0, CW)

    y += 12
    p.txt(ML, y, "Reach is shown as a sum of daily reach, which overstates unique people — platforms deduplicate "
                 "within a day, not across a month. Read it as a trend, not a headcount.", "Inter", "I", 8, MUTED, w=CW)
    p.stamp(3)


# =========================================================== page: momentum
def page_momentum(p):
    d = p.data
    p.add_page()
    p.page_title("page four", "Where the growth came from")

    y = 42
    p.txt(ML, y, "Week by week", "InterM", "", 10.5, INK)
    y += 9
    weeks = d["weekly"]
    mx = max((w[4] for w in weeks), default=1)
    for lab, spend, pur, rev, roas, cpp, aov in weeks:
        p.txt(ML, y, lab, "Inter", "", 9, INK_SOFT, w=40)
        p.txt(ML + 42, y, p.money(spend) if not p.is_blank() else "[        ]", "Inter", "", 9, INK_SOFT, w=26)
        p.txt(ML + 70, y, p.money(rev) if not p.is_blank() else "[        ]", "Inter", "", 9, INK_SOFT, w=26)
        p.txt(ML + 98, y, p.ratio(roas) if not p.is_blank() else "[  ]", "InterSB", "", 9, INK, w=20)
        _f = 0.0 if p.is_blank() else (roas / mx)
        _col = HAIR if p.is_blank() else (GOOD if roas >= d["breakeven"] else BAD)
        p.bar(ML + 118, y + 0.8, 46, 3.4, _f, _col)
        y += 8.4
    p.txt(ML + 42, y - 3, "spend", "Inter", "", 7.5, MUTED)
    p.txt(ML + 70, y - 3, "revenue", "Inter", "", 7.5, MUTED)
    p.txt(ML + 98, y - 3, "ROAS", "Inter", "", 7.5, MUTED)

    y += 8
    p.rule(ML, y, CW)
    y += 8
    p.txt(ML, y, "Top ads by spend", "InterM", "", 10.5, INK)
    y += 8
    for h, cx in [("Ad", ML), ("Spend", ML + 78), ("Purch.", ML + 106), ("ROAS", ML + 130), ("Read", ML + 152)]:
        p.txt(cx, y, h.upper(), "InterSB", "", 7.5, MUTED)
    y += 5
    p.rule(ML, y, CW, INK, 0.4)
    for name, spend, pur, rev, roas, cpp, aov in d["top_ads"]:
        if p.is_blank():
            read, col = "[      ]", MUTED
        else:
            read = ("scale" if roas >= d["breakeven"] * 1.3 else
                    ("keep" if roas >= d["breakeven"] else "cut"))
            col = {"scale": GOOD, "keep": ACCENT_D, "cut": BAD}[read]
        p.txt(ML, y + 2, name[:34], "Inter", "", 9, INK_SOFT, w=74)
        p.txt(ML + 78, y + 2, p.money(spend) if not p.is_blank() else "[     ]", "Inter", "", 9, INK_SOFT, w=26)
        p.txt(ML + 106, y + 2, p.money(pur) if not p.is_blank() else "[   ]", "Inter", "", 9, INK_SOFT, w=22)
        p.txt(ML + 130, y + 2, p.ratio(roas) if not p.is_blank() else "[  ]", "InterSB", "", 9, INK, w=20)
        p.txt(ML + 152, y + 2, read, "InterSB", "", 9, col)
        p.rule(ML, y + 7.4, CW)
        y += 8.6

    y += 6
    p.txt(ML, y, "Top creatives", "InterM", "", 10.5, INK)
    y += 8
    _cmax = (max((r[4] for r in d["top_creatives"]), default=1) or 1) if not p.is_blank() else 1
    for name, spend, pur, rev, roas, cpp, aov in d["top_creatives"]:
        p.txt(ML, y, name, "Inter", "", 9, INK_SOFT, w=60)
        p.txt(ML + 66, y, p.money(spend) if not p.is_blank() else "[      ]", "Inter", "", 9, INK_SOFT, w=28)
        p.txt(ML + 98, y, p.ratio(roas) if not p.is_blank() else "[  ]", "InterSB", "", 9, INK, w=20)
        p.bar(ML + 120, y + 0.8, 48, 3.2,
              (roas / _cmax) if not p.is_blank() else 0.0, ACCENT, bg=PANEL)
        p.txt(ML + 172, y, "of best" if not p.is_blank() else "", "Inter", "", 7.5, MUTED)
        y += 7.6

    p.stamp(4)


# ============================================================= page: close
def page_close(p):
    d = p.data
    p.add_page()
    p.page_title("page five", "What we did, and what happens next")

    blocks = [
        ("What we changed this month",
         "[ Three specific things you did. \"Launched four UGC concepts and cut the two weakest ad sets\" — "
         "not \"optimised creative\" and not \"tested some things\". ]"),
        ("What we learned",
         "[ One insight the data proved this month. This is the part the client is actually paying for. ]"),
        ("What we are doing next month",
         "[ Two or three concrete moves, each tied to a number in this report. Name the number. ]"),
        ("What the numbers don't show",
         "[ Stockouts, shipping delays, a price change, a competitor entering. Say it before the client finds it. ]"),
        ("What we need from you",
         "[ One clear ask. New imagery, a price decision, a stock fix. Give them a job and they become a partner. ]"),
    ]
    y = 38
    for lab, body in blocks:
        p.txt(ML, y, lab, "InterM", "", 10.5, INK)
        y += 6.5
        p.set_fill_color(*PANEL)
        p.rect(ML, y, CW, 18, style="F")
        p.txt(ML + 6, y + 4, body, "Inter", "", 8.6, INK_SOFT, w=CW - 12)
        y += 25

    y += 2
    p.rule(ML, y, CW)
    y += 8
    p.txt(ML, y, "What the numbers mean", "InterM", "", 10.5, INK)
    y += 8
    defs = [
        ("ROAS", "Revenue divided by ad spend. A 3.0x return means each unit spent brought back 3."),
        ("Breakeven ROAS", "The point where ads pay for themselves exactly, after product cost, shipping, fees and returns. Below it, every sale loses money."),
        ("Cost per purchase", "Ad spend divided by orders. Only meaningful next to average order value and breakeven."),
        ("Attribution window", "How long after a click the platform still credits itself with a sale. Kept fixed month to month so comparisons stay honest."),
        ("Revenue", "Orders the platforms reported, not your bank statement. We reconcile the two each quarter."),
    ]
    for term, body in defs:
        p.txt(ML, y, term, "InterSB", "", 8.8, INK)
        p.txt(ML + 46, y, body, "Inter", "", 8.4, MUTED, w=CW - 46)
        y += 8.4

    y += 1
    p.set_fill_color(*INK)
    p.rect(ML, y, CW, 22, style="F")
    p.txt(ML + 8, y + 5, "Questions on any of this?", "InterSB", "", 10.5, WHITE, w=CW - 16)
    p.txt(ML + 8, y + 12, "[ your email ]  ·  [ your phone ]  ·  we answer the same day",
          "Inter", "", 8.8, (209, 213, 219), w=CW - 16)

    p.stamp(5)


# ==================================================================== build
def build(mode, out):
    data = blank_data() if mode == "template" else monthly_data()
    pdf = Report(data, mode)
    pdf.set_title("Monthly Performance Report — " + str(data["brand"]))
    pdf.set_author(str(data["prepared_by"]))
    page_cover(pdf)
    page_performance(pdf)
    page_funnel(pdf)
    page_momentum(pdf)
    page_close(pdf)
    pdf.output(out)
    print("wrote", out)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("both", "template"):
        build("template", os.path.join(ROOT, "04_Monthly_Report_PDF_Template.pdf"))
    if which in ("both", "sample"):
        os.makedirs(os.path.join(ROOT, "samples"), exist_ok=True)
        build("sample", os.path.join(ROOT, "samples", "Sample_Monthly_Report.pdf"))
