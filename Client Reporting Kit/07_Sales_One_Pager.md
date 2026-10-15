# The Media Buyer's Reporting System
### Stop sending a client a number you can't defend

A Google Sheets reporting system for media buyers, freelancers and small agencies running
**Meta and TikTok**. Live dashboard, client report, KPI calculator, PDF template, and twelve
AI prompts for writing the narrative. Works standalone; automates fully if you run n8n.

**[▶ Watch the 4-minute demo]** · **[Get the kit]**

---

## The problem it solves

You report on two platforms. Your client asks why ROAS moved. Your dashboard shows one
blended number, so the honest answer is *"I don't know."*

And somewhere in your raw data, ad-level spend doesn't match the platform's own account
total — you just haven't looked.

---

## What it does that Looker Studio doesn't

**1. Breakeven ROAS sits next to ROAS.**
A 2.4x looks fine until you know breakeven is 2.8x — at which point every order lost money.
Derived from *your client's* COGS, shipping and fees. Not an industry benchmark.

**2. The platforms stay separate. Deliberately.**
Meta and TikTok each get their own dashboard with zero shared data. There is one tab that
combines them, on purpose, showing share of spend against share of revenue — because that
comparison is the whole argument.

**3. It checks its own input data.**
The Health Check tab reconciles ad-level against account-level totals and flags the gap.
On the live account this was built on, it caught **13 duplicated ad-days double-counting
1,545 EGP of spend** and a **17.6% shortfall in TikTok's ad-level export**. Errors sitting
in the raw data that nobody had noticed.

**4. Every number is a formula you can audit.**
1,316 live formulas across three spreadsheets. Zero hard-coded results. The AI writes the
language; the arithmetic stays in the sheet where you can check it.

---

## Real output, real account, one week

*8–14 October vs 1–7 October. E-commerce, Meta + TikTok.*

| | Meta | TikTok | Combined |
|---|---|---|---|
| Spend | 26,508 (+18.2%) | 14,143 (+0.3%) | 40,651 (+11.3%) |
| Revenue | 118,475 | 57,105 | 175,580 (−12.7%) |
| **ROAS** | **4.47x** | **4.04x** | **4.32x** |
| Frequency | 1.46 | **4.10** | 2.70 |
| Click → purchase | **5.23%** | 1.65% | 2.87% |

**The blended read: "ROAS fell 21%. Cut spend."**

**The split read:** TikTok hit frequency 4.10 with a 1.65% click-to-purchase rate — creative
fatigue, fix is new creative and a frequency cap. Meta sat at 1.46 frequency and 5.23%
conversion — healthy, and its dip is attribution lag, so the fix is *do nothing*.

One blended dashboard tells you to cut both. That would have been a mistake.

---

## What's in the box

| | |
|---|---|
| **Reporting dashboard** | 11 tabs. Set two dates, everything recalculates. Separate Meta and TikTok dashboards, live-ranked top-25 ad table, benchmarks, Health Check |
| **Client report** | 11 tabs. Cover, executive summary, performance, platform detail, combined, top ads, creatives, weekly trend, next steps, metric dictionary |
| **KPI calculator** | Contribution margin, breakeven ROAS, POAS, profit bridge, period compare, 13 sensitivity checks |
| **Monthly PDF** | 5 pages, designed, print-ready. Meta / TikTok / Combined columns |
| **12 AI prompts** | The narrative, the bad month, creative learnings, the budget recommendation, the 9pm complaint email, the platform split decision, the self-audit |

Currency defaults to **EGP**; one cell changes it. Everything is **Google Sheets** — free to
seat, your client opens a link.

---

## Three ways to buy

| | **The Kit** | **Kit + Automation** | **Done For You** |
|---|---|---|---|
| For | 1–3 clients, no n8n | 3–10 clients, you run n8n | 10+ clients, nobody wants to touch n8n |
| The five components | ✅ | ✅ | ✅ |
| Manual `IMPORTRANGE` setup | ✅ | ✅ | ✅ |
| n8n workflows (provision + nightly refresh) | — | ✅ | ✅ |
| I install it in your n8n | — | — | ✅ |
| I onboard your first 2 clients | — | — | ✅ |
| First nightly cycle run together | — | — | ✅ |
| Benchmarks tuned to your real data | — | — | ✅ |
| Support | FAQ + community | 30 days email | 60 days + calls |
| **Price** | **$149 one-time** | **$449 one-time** | **$1,500 + $79/mo** |

Upgrading within 90 days costs the difference, not the full price.

---

## Straight answers

**Do I need n8n?** No. The Kit tier runs on one formula and an approved `IMPORTRANGE`
prompt. Automation is the upgrade, not the requirement.

**Is the automation proven?** The workflow logic is unit-tested against real data — the
ingest node was run against an actual client sheet and its output matched the delivered
workbook exactly, row for row. The scheduled end-to-end run is supervised on install.
That's why Tier 3 includes me running the first cycle with you.

**Is my client's data safe?** On the Kit and Automation tiers I never touch it. Everything
runs in your Google account and your n8n. On Tier 3 we sign a data clause before I get any
credentials.

**What if TikTok changes its export?** The automated path matches columns **by header name**,
not position. The mapping layer is one Code node with column aliases at the top — a renamed
column is one added line, not a rebuild.

**What does it not do?** It doesn't pull from the ad APIs — that's your pipeline's job, this
is the reporting and interpretation layer. It doesn't invent benchmarks; thresholds ship
labelled as placeholders for you to replace with your client's trailing range. And it doesn't
calculate in AI.

---

## The pitch in one line

It costs less than one hour of your billable time per month, and it lets you take on one
more client without adding hours.

**[Get the kit]** · **[Book a 20-minute walkthrough]**

*Prices in USD. Regional pricing available — ask.*
