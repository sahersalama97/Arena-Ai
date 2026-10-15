#!/usr/bin/env python3
"""
Build GOFRESH's client report (02) from live pipeline data.

The blank template is built by build_client_report.py, which reads every number
from sample_data.py. Rather than fork that builder -- which would let the sample
and live versions drift apart -- this module patches sample_data in place with
GOFRESH's real figures *before* build_client_report is imported, then calls its
build().

That means the report and the LIVE dashboard provably come from the same
collection code: both go through build_gofresh_live's fund/ads lists, including
its duplicate ad-day removal and its adaptive period choice.

Output goes to google_drive/, which .gitignore excludes, because this is a real
client's revenue data and must not land in a public repository.

Run:  python3 build_gofresh_report.py
"""
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

KIT_ROOT = os.path.dirname(HERE)
OUT_DIR = "/home/user/Arena-Ai/google_drive"

# Importing this runs the live dashboard build as a side effect and gives us the
# collected data. Idempotent: same input data produces the same file.
import build_gofresh_live as G

import sample_data as SD

# ---------------------------------------------------------------- patch the data
# These functions read their constants from module globals at call time, so
# patching the module object is enough -- weekly_rows() and aggregate_ads() will
# default to GOFRESH's window rather than the sample's September.
SD.BRAND = G.BRAND_NAME
SD.PREPARED_BY = "Media Buyer Ops"
SD.CURRENCY = G.CUR

# The only invented numbers in the whole build, and they are flagged red in the
# sheet at KPI Calc!I4. Breakeven ROAS is an estimate until GOFRESH confirms them.
SD.COGS_PCT = G.ASSUMED_COGS_PCT
SD.OTHER_VAR_PCT = G.ASSUMED_OTHER_VAR_PCT
SD.SHIP_PER_ORDER = G.ASSUMED_SHIP_PER_ORDER

SD.DATA_START = G.USABLE[0]
SD.DATA_END = G.USABLE[-1]
SD.CUR_START, SD.CUR_END = G.CUR_START, G.CUR_END
SD.CMP_START, SD.CMP_END = G.CMP_START, G.CMP_END

SD.fundamentals_rows = lambda: G.fund
SD.ad_rows = lambda fundamentals=None: G.ads

# ------------------------------------------------------- now import the builder
import build_client_report as BCR


def label(a, b):
    """'8-14 October 2026'. Avoids strftime('%-d'), which is glibc-only."""
    if a.month == b.month and a.year == b.year:
        return f"{a.day}\u2013{b.day} {a.strftime('%B %Y')}"
    if a.year == b.year:
        return f"{a.day} {a.strftime('%B')} \u2013 {b.day} {b.strftime('%B %Y')}"
    return f"{a.isoformat()} \u2013 {b.isoformat()}"


def build():
    # Never write over the blank template.
    BCR.OUT = os.path.join(
        OUT_DIR, f"GOFRESH - Client Report - {label(G.CUR_START, G.CUR_END)}.xlsx")
    BCR.PERIOD_LABEL = label(G.CUR_START, G.CUR_END)
    BCR.COMPARE_LABEL = label(G.CMP_START, G.CMP_END)

    os.makedirs(OUT_DIR, exist_ok=True)
    BCR.build()

    print("\n--- verification against the LIVE dashboard ---")
    print(f"  brand                {SD.BRAND}")
    print(f"  period               {BCR.PERIOD_LABEL}")
    print(f"  compared against     {BCR.COMPARE_LABEL}")
    print(f"  account rows         {len(G.fund)}")
    print(f"  ad rows              {len(G.ads)}   (duplicate ad-days dropped: "
          f"{G.DUPLICATE_AD_ROWS_REMOVED})")
    for nm, d in (("Meta", BCR.cur_meta), ("TikTok", BCR.cur_tt), ("Combined", BCR.cur_all)):
        print(f"  {nm:<9} spend {d['spend']:>10,.0f}  revenue {d['rev']:>10,.0f}  "
              f"ROAS {d['roas']:.2f}x  AOV {d['aov']:,.0f}  freq {d['freq']:.2f}")
    for nm, d in (("Meta", BCR.prv_meta), ("TikTok", BCR.prv_tt), ("Combined", BCR.prv_all)):
        print(f"  prev {nm:<5} spend {d['spend']:>10,.0f}  revenue {d['rev']:>10,.0f}  "
              f"ROAS {d['roas']:.2f}x")
    print(f"  breakeven ROAS       {BCR.BREAKEVEN:.2f}x  "
          f"(ASSUMED costs: COGS {SD.COGS_PCT:.0%}, other {SD.OTHER_VAR_PCT:.0%}, "
          f"ship {SD.SHIP_PER_ORDER} {SD.CURRENCY})")
    return BCR.OUT


if __name__ == "__main__":
    build()
