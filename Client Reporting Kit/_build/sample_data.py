"""
Deterministic sample data for the kit — a plausible Egyptian D2C brand running
Meta + TikTok, with weekly seasonality, CPM creep and one bad week.

Everything is seeded, so rebuilding produces identical numbers.
"""
import math, random, datetime as dt

BRAND = "Northwind Supply Co."
PREPARED_BY = "Your Agency Name"
CURRENCY = "EGP"

# The client's cost structure — the three numbers a media buyer must ask for.
# These are the same defaults the KPI Calculator and Dashboard ship with.
COGS_PCT       = 0.30    # product cost as a share of revenue
OTHER_VAR_PCT  = 0.06    # payment fees + other order-linked costs
SHIP_PER_ORDER = 72      # fulfilment cost per order, in the reporting currency

def breakeven_roas(aov):
    """Breakeven ROAS given an average order value and the cost structure above."""
    cm = 1 - COGS_PCT - OTHER_VAR_PCT - (SHIP_PER_ORDER / aov if aov else 0)
    return (1 / cm) if cm > 0 else 0

# The reporting window: previous full month vs the month before it.
DATA_START = dt.date(2026, 7, 15)
DATA_END   = dt.date(2026, 10, 12)
CUR_START, CUR_END = dt.date(2026, 9, 1),  dt.date(2026, 9, 30)
CMP_START, CMP_END = dt.date(2026, 8, 1),  dt.date(2026, 8, 31)


def _day_factor(d: dt.date) -> float:
    """Weekend lift + a soft mid-September dip + payday spike."""
    dow = d.weekday()                       # 0=Mon
    f = 1.0
    f *= [1.0, 0.98, 1.0, 1.04, 1.12, 1.18, 1.10][dow]   # Thu–Sat are strong in EG
    if dt.date(2026, 9, 8) <= d <= dt.date(2026, 9, 15):
        f *= 0.74                            # the bad week
    if d.day <= 3:
        f *= 1.12                            # payday
    return f


def fundamentals_rows():
    """Date, Platform, Spend, Impressions, Reach, Clicks, LPV, ATC, IC, Purchases, Revenue"""
    rng = random.Random(20261013)
    rows = []
    d = DATA_START
    i = 0
    while d <= DATA_END:
        f = _day_factor(d)
        # CPM creeps upward through the window (auction pressure)
        creep = 1 + 0.0035 * i

        # ---------------- Meta ----------------
        base_spend = 3150 * f
        spend = base_spend * rng.uniform(0.93, 1.07)
        cpm = 62 * creep * rng.uniform(0.95, 1.05)
        impressions = spend / cpm * 1000
        reach = impressions / rng.uniform(1.9, 2.7)
        ctr = 0.0163 * rng.uniform(0.87, 1.12)
        clicks = impressions * ctr
        lpv = clicks * rng.uniform(0.68, 0.82)
        atc = lpv * rng.uniform(0.062, 0.084)
        ic = atc * rng.uniform(0.42, 0.52)
        purchases = ic * rng.uniform(0.70, 0.80)
        aov = 690 * rng.uniform(0.95, 1.06)
        revenue = purchases * aov
        rows.append([d, "Meta", round(spend, 2), round(impressions), round(reach),
                     round(clicks), round(lpv), round(atc), round(ic),
                     round(purchases), round(revenue, 2)])

        # ---------------- TikTok ----------------
        tt_spend = 1450 * f * rng.uniform(0.9, 1.1)
        tt_cpm = 41 * creep * rng.uniform(0.94, 1.06)
        tt_imp = tt_spend / tt_cpm * 1000
        tt_reach = tt_imp / rng.uniform(1.6, 2.3)
        tt_ctr = 0.0118 * rng.uniform(0.85, 1.15)
        tt_clicks = tt_imp * tt_ctr
        tt_atc = tt_clicks * rng.uniform(0.055, 0.075)      # no LPV on TikTok
        tt_ic = tt_atc * rng.uniform(0.38, 0.48)
        tt_pur = tt_ic * rng.uniform(0.60, 0.70)
        tt_aov = 615 * rng.uniform(0.94, 1.07)
        tt_rev = tt_pur * tt_aov
        rows.append([d, "TikTok", round(tt_spend, 2), round(tt_imp), round(tt_reach),
                     round(tt_clicks), "", round(tt_atc), round(tt_ic),
                     round(tt_pur), round(tt_rev, 2)])
        d += dt.timedelta(days=1)
        i += 1
    return rows


AD_ROSTER = [
    # platform, ad name, campaign, creative key, spend weight, efficiency
    ("Meta",   "VID | Founder story | v4",       "Prospecting | Broad | EG",    "UGC-Founder",          1.80, 1.25),
    ("Meta",   "STATIC | Bundle offer | v2",     "Prospecting | Broad | EG",    "Static-Bundle",        1.20, 1.00),
    ("Meta",   "VID | Founder story | v3",       "Prospecting | Broad | EG",    "UGC-Founder",          0.90, 0.95),
    ("Meta",   "VID | Review compilation | v1",  "Prospecting | Interest | EG", "UGC-Reviews",          0.90, 1.05),
    ("Meta",   "STATIC | Bundle offer | v1",     "Test | Broad | EG",           "Static-Bundle",        0.60, 0.80),
    ("Meta",   "STATIC | Discount 20% | v1",     "Retargeting | 7d IC",         "Static-Discount",      0.50, 1.90),
    ("Meta",   "CAROUSEL | Best sellers",        "Retargeting | 14d ATC",       "Carousel-Bestsellers", 0.35, 2.20),
    ("Meta",   "VID | Founder story | v1",       "Prospecting | Broad | EG",    "UGC-Founder",          0.28, 0.52),
    ("TikTok", "UGC | Problem-solution | v2",    "Prospecting | Broad | EG",    "TT-UGC-ProbSol",       1.30, 1.15),
    ("TikTok", "UGC | Trend audio | v1",         "Prospecting | Broad | EG",    "TT-UGC-Trend",         0.90, 0.72),
    ("TikTok", "UGC | Trend audio | v2",         "Prospecting | Broad | EG",    "TT-UGC-Trend",         0.70, 1.00),
    ("TikTok", "Spark ad | Creator A",           "Spark | Creator A",           "TT-Spark-CreatorA",    1.00, 1.45),
]


def _split_int(total, weights):
    """Split an integer total across weights, preserving the total exactly
    (largest-remainder method). Keeps tiny ads from rounding to a flat zero."""
    total = int(round(total))
    sw = sum(weights)
    if sw <= 0 or total <= 0:
        return [0] * len(weights)
    exact = [total * w / sw for w in weights]
    base = [int(x) for x in exact]
    rem = total - sum(base)
    order = sorted(range(len(weights)), key=lambda i: -(exact[i] - base[i]))
    for i in order[:max(0, rem)]:
        base[i] += 1
    return base


def ad_rows(fundamentals):
    """
    Date, Platform, Ad Name, Campaign, Creative Key, Spend, Impressions, Clicks,
    Purchases, Revenue

    Spend is split by the ad's spend weight; purchases by weight x efficiency;
    revenue follows the purchases each ad actually won. Integer splits use largest
    remainder, so ad-level rows sum to the account-level totals — which is what lets
    the Health Check tab prove the two reconcile, and it is what gives the ranked
    tables a real scale / maintain / cut story.
    """
    rng = random.Random(7)
    totals_by_day = {(r[0], r[1]): r for r in fundamentals}
    dates = sorted({r[0] for r in fundamentals})
    rows = []
    for plat in ("Meta", "TikTok"):
        ads = [a for a in AD_ROSTER if a[0] == plat]
        for d in dates:
            base = totals_by_day.get((d, plat))
            if not base:
                continue
            _, _, spend, imp, reach, clicks, lpv, atc, ic, pur, rev = base
            jitter = [rng.uniform(0.85, 1.15) for _ in ads]
            w = [a[4] * j for a, j in zip(ads, jitter)]
            e = [a[4] * a[5] * j for a, j in zip(ads, jitter)]
            sw = sum(w)
            pu = _split_int(pur, e)
            aov_j = [rng.uniform(0.90, 1.10) for _ in ads]
            raw = [p * x for p, x in zip(pu, aov_j)]
            sr = sum(raw)
            for k, (a, wi) in enumerate(zip(ads, w)):
                rows.append([
                    d, plat, a[1], a[2], a[3],
                    round(spend * wi / sw, 2),
                    round(imp * wi / sw),
                    round(clicks * wi / sw),
                    pu[k],
                    round(rev * raw[k] / sr, 2) if sr > 0 else 0.0,
                ])
    return rows


def totals(rows, start, end, plat=None):
    t = dict(spend=0, imp=0, reach=0, clicks=0, lpv=0, atc=0, ic=0, pur=0, rev=0)
    for r in rows:
        if not (start <= r[0] <= end):
            continue
        if plat and r[1] != plat:
            continue
        t["spend"] += r[2]; t["imp"] += r[3]; t["reach"] += r[4]; t["clicks"] += r[5]
        t["lpv"] += r[6] or 0; t["atc"] += r[7]; t["ic"] += r[8]
        t["pur"] += r[9]; t["rev"] += r[10]
    return t


def derive(t):
    g = lambda a, b: (t[a] / t[b]) if t[b] else 0
    return dict(
        spend=t["spend"], imp=t["imp"], reach=t["reach"], clicks=t["clicks"],
        lpv=t["lpv"], atc=t["atc"], ic=t["ic"], pur=t["pur"], rev=t["rev"],
        cpm=g("spend", "imp") * 1000, cpc=g("spend", "clicks"),
        ctr=g("clicks", "imp"), freq=g("imp", "reach"),
        lpv_rate=g("lpv", "clicks"),
        atc_rate=g("atc", "clicks"), ic_rate=g("ic", "atc"), pur_rate=g("pur", "ic"),
        cvr=g("pur", "clicks"), cpp=g("spend", "pur"), aov=g("rev", "pur"),
        roas=g("rev", "spend"), rev_per_mille=g("rev", "imp") * 1000,
    )


def bands():
    """The reporting bands used by the kit, in reporting order."""
    return {
        "current":  (CUR_START, CUR_END),
        "previous": (CMP_START, CMP_END),
    }


def weekly_rows(rows=None, start=None, end=None):
    """Weekly account-level totals for the current period, ranked by ROAS."""
    import datetime as _dt
    rows = rows or fundamentals_rows()
    start = start or CUR_START
    end = end or CUR_END
    out = []
    d = start
    while d <= end:
        w_end = min(d + _dt.timedelta(days=6), end)
        t = totals(rows, d, w_end)
        if t["spend"]:
            fmt = lambda x: x.strftime("%b ") + str(x.day)
            lbl = f"{fmt(d)} – {fmt(w_end)}"
            out.append((lbl, round(t["spend"]), round(t["pur"]), round(t["rev"]),
                        t["rev"] / t["spend"], t["spend"] / t["pur"] if t["pur"] else 0,
                        t["rev"] / t["pur"] if t["pur"] else 0))
        d += _dt.timedelta(days=7)
    out.sort(key=lambda r: -r[4])
    return out


def aggregate_ads(rows=None, by="ad", start=None, end=None, top=None):
    """Spend-ranked ad or creative rollup for the current period."""
    rows = rows or ad_rows(fundamentals_rows())
    start = start or CUR_START
    end = end or CUR_END
    agg = {}
    for r in rows:
        if not (start <= r[0] <= end):
            continue
        key = r[2] if by == "ad" else r[4]
        a = agg.setdefault(key, dict(spend=0, imp=0, clicks=0, pur=0, rev=0,
                                     camp=r[3], creative=r[4]))
        a["spend"] += r[5]; a["imp"] += r[6]; a["clicks"] += r[7]
        a["pur"] += r[8]; a["rev"] += r[9]
    out = []
    for k, a in agg.items():
        out.append((k, round(a["spend"]), round(a["pur"]), round(a["rev"]),
                    a["rev"] / a["spend"] if a["spend"] else 0,
                    a["spend"] / a["pur"] if a["pur"] else 0,
                    a["rev"] / a["pur"] if a["pur"] else 0))
    out.sort(key=lambda r: -r[1])
    return out[:top] if top else out
