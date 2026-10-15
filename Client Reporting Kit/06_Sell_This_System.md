# Selling This System — positioning, tiers, pricing, and what is honestly ready

You are selling to **other media buyers, freelancers and small agencies** — people who
already have clients. You have **no pricing model yet** and you sell into **a mix of
markets**. This document answers all three.

Read it once end to end, then use `07`, `08` and `09` as the working documents.

> **How to read the prices here.** I had no internet access to competitor pricing when I
> wrote this, so every number is reasoned from *what the buyer gets* and *what it
> replaces*, not from market research. They are starting anchors to test, not truths.
> Section 4 tells you how to validate them in two weeks without guessing.

---

## 1. What you are actually selling

Not a spreadsheet. Media buyers already have spreadsheets.

**You are selling the end of "a number I can't defend."**

Every media buyer has had the moment: the client asks why ROAS moved, and the honest
answer is *I don't know, the dashboard doesn't tell me*. Or worse — you send a report
with a number that turns out to be wrong, and you find out from the client.

This system is built around that fear. Concretely, it does four things a Looker Studio
template does not:

1. **It puts breakeven ROAS next to ROAS.** A 2.4x looks fine until you know breakeven
   is 2.8x — at which point every order lost money. The KPI Calculator derives breakeven
   from the client's own COGS, shipping and fees. Not an industry benchmark. Their numbers.
2. **It refuses to blend two platforms.** Meta and TikTok get separate dashboards with
   zero shared data. The combination exists on exactly one tab, deliberately, where you
   can see share-of-spend against share-of-revenue.
3. **It checks its own input data.** The Health Check tab reconciles ad-level against
   account-level totals and flags the gap. On the real client it was built on, that check
   caught a **17.6% shortfall in TikTok ad-level spend** and **13 duplicated ad-days
   worth 1,545 EGP of double-counted spend** — errors sitting in the raw data that nobody
   had noticed.
4. **Every number is an auditable formula.** 1,316 live formulas across the three
   spreadsheets, zero hard-coded results. AI writes the *language*, never the arithmetic.

Point 3 is your best sales story and you should lead with it. See §6.

---

## 2. What is honestly ready to sell

Sell against this table. The ✅ rows are safe to promise. The ⚠️ and ❌ rows are where
refunds and bad reviews come from, so script them in rather than discovering them in a
support ticket.

| Claim | State | Say this in sales |
|---|---|---|
| Five components exist (dashboard, report, calculator, PDF, prompts) | ✅ verified | Promise it |
| 1,316 live formulas; 2,069 formulas audited across 4 workbooks, 0 errors | ✅ verified | Promise it |
| Two fully separate platform dashboards + one Combined tab | ✅ verified — all 49 cross-platform SUMIFS carry their own platform qualifier, zero leakage | Promise it |
| Live-ranked Ad Performance (top 25 on the selected window, re-ranks itself) | ✅ verified | Promise it |
| Zero clipped cells / clean visual layout | ✅ verified by layout checker | Promise it |
| Manual path: one `IMPORTRANGE` formula fills the dashboard | ✅ built and documented | Promise it — **Google Sheets only**, `IMPORTRANGE` does not exist in Excel |
| Twelve grounded AI prompts | ✅ verified | Promise it |
| WF4 + WF5 n8n workflows generated, graph validated, Code nodes executed under Node v22 against real data | ⚠️ logic tested, **n8n itself was never run** | Say: *"built and unit-tested at the logic layer; your first run is supervised."* Do not say "fully automated, works out of the box" |
| Nightly end-to-end automation in production | ❌ never executed | **Do not promise.** This is why Tier 3 exists |
| Registry needs a `Kit_Sheet_ID` column added | ❌ buyer must add it | List as a 2-minute prerequisite in the runbook |
| Upstream WF2e duplicates rows and rounds 16-digit Ad_IDs | ❌ bug in the TikTok import workflow | **Ship the patch with every Tier 2+ sale and disclose it.** See `n8n/WF2e_FIX_TikTok_Raw_Integrity.md` |
| TikTok's ad-level export under-reports spend vs account level | ❌ platform-side, not fixable | Reframe as a feature: *"this is why Health Check exists"* |
| Benchmarks ship as `PLACEHOLDER` | ⚠️ by design | Disclose — it's honest positioning, not a defect. The status column works immediately and they tune it to their client's trailing range |
| Breakeven needs the client's COGS / shipping / fees | ⚠️ buyer must collect | Ship `09`'s intake form with the product |
| GOFRESH cost inputs are assumed (COGS 30%, other 4%, ship 65 EGP) | ⚠️ flagged red in-sheet at `KPI Calc!I4` | Only relevant to your own demo, not to buyers |

**The single biggest sales risk is the ⚠️ on n8n.** You have built and tested the logic
hard — the flatten node was executed against an emulated `batchGet` payload built from a
real sheet and its output matched the delivered workbook as a multiset (28 fund rows, 387
ad rows). That is real work. But you have never watched the workflow run on a schedule.

Do not hide that and do not oversell it. Run WF4 and WF5 yourself, end to end, on one
brand, **before you take a single Tier 2 or Tier 3 payment**. It is a couple of hours and
it converts your weakest claim into your strongest one. Until then, sell Tier 1 and take
Tier 3 orders as paid installs where the first run happens together.

---

## 3. The offer — three tiers

Keep it to three. More than three and buyers stall.

### Tier 1 — The Kit · self-serve
**For:** solo freelancer, 1–3 clients, no n8n, wants it today.

Ships: `01` dashboard (11 tabs) · `02` client report (11 tabs) · `03` KPI calculator
(6 tabs) · `04` PDF template (5 pages) · `05` twelve AI prompts · README · sample filled
PDF · the manual `IMPORTRANGE` link formula.

They connect it to their data with one formula and approve an IMPORTRANGE prompt. No
server, no credentials, no automation.

**Anchor: USD $149 one-time.**

### Tier 2 — The Kit + Automation
**For:** buyer with 3–10 clients who already runs n8n, or will.

Everything in Tier 1, plus: `WF4` (provisions a dashboard per client, 13 nodes) · `WF5`
(nightly refresh, 17 nodes, **3 Sheets API calls per brand** — one batchGet, one clear,
one batchUpdate, so a refresh cannot break a formula) · `AUTOMATION_GUIDE` · the three
Code nodes as standalone testable `.js` · the WF2e integrity patch and diagnosis ·
30 days email support.

They need: their own n8n (self-hosted or cloud), Google Sheets + Drive OAuth credentials,
an SMTP or Gmail credential, and the raw sheets their pipeline already writes.

**Anchor: USD $449 one-time.**

### Tier 3 — Done for you
**For:** small agency, 10+ clients, nobody in-house who wants to touch n8n.

Everything in Tier 2, plus: you install it in *their* n8n, connect their Meta and TikTok
accounts, add the registry column, onboard their first **two** clients end to end, run the
first nightly cycle with them watching, tune Benchmarks to their real trailing data, and
stay on call for 60 days.

**Anchor: USD $1,500 install + $79/month**, or **$2,400 all-in** with the first three
months of support prepaid. The monthly is what makes this a business rather than a
one-off — protect it.

### Add-on — Agency licence
White-label rights: remove your branding, use with unlimited clients, seat up to five
people internally, use it inside their own client onboarding.

**Anchor: +USD $1,200 one-time** on top of Tier 2 or 3. Without it, the licence in
`LICENCE.md` covers one business entity using the kit *for* their clients — which is what
99% of buyers want and is not a restriction they'll notice.

### What Tier 1 buyers will ask about upgrading
Make the upgrade price **the difference**, not the full Tier 2 price, for 90 days. It
costs you nothing and converts your cheapest tier into your best lead source.

---

## 4. Pricing across mixed markets

You sell into Egypt, the Gulf and international. Do **not** build a country price list —
it invites arbitrage on a borderless digital product (someone buys at the Egyptian price
and resells) and it's a maintenance burden.

**Price by who pays, not where they live.** One question decides it:

> *"What currency do your clients pay you in?"*

- They invoice in USD/EUR/GBP → charge USD list, no adjustment.
- They invoice in EGP → charge the EGP tier.
- They invoice in SAR/AED → charge USD list. Gulf agencies bill at international rates.

Indicative, at the time of writing — **recompute the conversions on the day, do not
hard-code them**:

| | Tier 1 | Tier 2 | Tier 3 install | Tier 3 monthly |
|---|---|---|---|---|
| USD list | $149 | $449 | $1,500 | $79 |
| EGP market (≈45% of list) | ~$67 equiv. in EGP | ~$202 equiv. | ~$675 equiv. | ~$36 equiv. |
| Gulf / international | list | list | list | list |

Three rules that matter more than the numbers:

1. **Never discount below ~40% of list for any market.** Below that you're not adjusting
   for purchasing power, you're signalling the product is worth less — and buyers who
   pay $50 support you as hard as buyers who pay $150.
2. **Sell through a merchant of record** — Gumroad or Lemon Squeezy. They handle VAT,
   GST and EU sales tax, which you do not want to be doing by hand across three markets.
   They take ~5–10%; that's cheap for it. Stripe directly means you own the tax problem.
3. **The monthly is the business.** $79/mo × 20 agencies = $1,580/mo recurring. The
   one-time tiers are a funnel into it. Do not let Tier 3 be sold install-only.

### Validate the anchors in two weeks

Post Tier 1 at $149 in one place where media buyers are (§7). Then:

- **Nobody clicks** → the positioning is wrong, not the price. Fix §1's hook.
- **Clicks, no buys** → price or trust. Add the sample PDF and a screen-recording.
- **Buys immediately, no questions** → you priced too low. Raise 30% and watch.
- **Most common question is "does it do n8n?"** → Tier 2 is your real product; lead with it.

Change one variable at a time. Twenty data points beats any model I can give you.

---

## 5. What the buyer gets that justifies the number

Build the pitch on the buyer's economics, not yours.

A media buyer reporting Meta + TikTok for five clients spends roughly **2–4 hours per
client per month** assembling the dashboard, reconciling platforms, computing margin and
writing the narrative. Call it 3 hours. Fifteen hours a month.

With this kit the assembly and reconciliation go away; what's left is the judgement and
the writing — which is the part they should be spending time on anyway, and the part
`05`'s twelve prompts accelerate.

Two ways to say it, and the second is stronger:

- *"Saves you ~2 hours per client per month."* — true, but it's a soft saving.
- *"Lets you take on one more client without adding hours."* — that's revenue, not time.
  One more client is worth more than the entire Tier 2 price, usually in the first month.

Lead with the second. Then close on the risk reversal: **it stops you sending a number
you can't defend**, and one of those costs you a client.

---

## 6. Your demo — the GOFRESH story

This is the most valuable asset you have and it's real, not a mockup. Screen-record it.

The system was built on a live e-commerce account running Meta and TikTok through the n8n
pipeline. On the week of 8–14 October it produced:

| | Meta | TikTok | Combined |
|---|---|---|---|
| Spend | 26,508 EGP (+18.2%) | 14,143 EGP (+0.3%) | 40,651 (+11.3%) |
| Revenue | 118,475 | 57,105 | 175,580 (−12.7%) |
| **ROAS** | **4.47x** | **4.04x** | **4.32x** |
| Frequency | 1.46 | **4.10** | 2.70 |
| Click → purchase | **5.23%** | 1.65% | 2.87% |
| AOV | 779 | 614 | 717 |

**The pitch, in three beats:**

1. *"The blended read is 'ROAS fell 21%.' That's what a single dashboard tells you."*
2. *"Split apart, it's two unrelated problems. TikTok's frequency hit 4.10 with a 1.65%
   click-to-purchase rate — that's creative fatigue, the fix is new creative and a
   frequency cap. Meta sat at 1.46 frequency and 5.23% conversion — that's healthy, and
   its dip is attribution lag, so the fix is do nothing. **A blended dashboard tells you
   to cut both. That would have been a mistake.**"*
3. *"And the Health Check tab found the raw data was wrong: thirteen duplicated ad-days
   double-counting 1,545 EGP of spend, and TikTok's ad-level export coming in 17.6% short
   against its own account-level total. That's why the kit tells you to quote TikTok
   totals from one place and never another."*

Beat 3 is the one that lands with experienced buyers, because they have all been burned
by data they trusted. It also pre-empts the "is this just a pretty template?" objection —
a pretty template does not reconcile your spend against the platform's own account total.

Record it at 1080p, under four minutes, no music. Put the timestamp of the Health Check
flag on screen.

---

## 7. Where to find buyers

Ordered by effort-to-payoff, for a product in this price band:

1. **A screen-recording of §6 on YouTube and LinkedIn.** The GOFRESH story is
   self-evidently credible and nobody else is showing reconciliation failures on camera.
   This is your highest-leverage asset — make it first.
2. **r/PPC, r/FacebookAds, r/juststart.** Do not post an ad. Post the *finding*: "built a
   Health Check that reconciles ad-level vs account-level spend — here's what it caught on
   a live TikTok account." Answer the comments. Link in profile.
3. **Media-buyer Facebook and Slack communities.** Same approach. These groups ban
   self-promotion and reward specificity.
4. **Gumroad / Lemon Squeezy marketplace discovery** for Tier 1. Low volume, zero effort,
   handles the tax.
5. **Cold outreach to small agencies** for Tier 3 only. Ten hand-written emails a week
   referencing something specific about their accounts. Do not send a template — at
   $1,500 the buyer expects to be known.
6. **Egyptian and Gulf communities specifically**, since you're in Cairo and can do Tier 3
   installs in Arabic. That's a real moat for the Gulf market and almost nobody selling
   English-language kits offers it. **Consider an Arabic version of `05` and the README** —
   it would differentiate you immediately and it's a day of work.

---

## 8. Objections, answered

**"I already use AgencyAnalytics / Swydo / Looker Studio."**
Those pull platform data and chart it. They don't compute contribution margin, breakeven
ROAS or POAS from *your client's* cost structure, they don't reconcile ad-level against
account-level spend, and they don't separate two platforms so a weak one can't hide behind
a strong one. Different layer. Plenty of buyers run both — this one answers "are we making
money," theirs answers "what happened."

**"My clients don't read reports."**
Then send the PDF. Five pages, and `05` prompt 9 turns your notes into the email that goes
with it. Most "clients don't read reports" is actually "reports arrive as a spreadsheet
link with no narrative."

**"n8n is too technical for me."**
Tier 1 has no n8n at all — one formula and an IMPORTRANGE approval. If you want the
automation, that's Tier 3, and I install it.

**"Google Sheets looks unprofessional."**
Your client opens a link, it's live, they can filter and sort, and it costs nothing to
seat. The PDF is the designed artefact for the board; the sheet is the working one.
Agencies pay $99–$400/month per SaaS seat for worse.

**"Can't I just ask ChatGPT to do this?"**
The twelve prompts are included and you should use them. But an AI handed a metrics table
will confidently invent a reason for every movement. Here the arithmetic is 1,316 visible
formulas in a sheet you can audit, and the AI writes the language only. Prompt 11 is a
self-audit that exists specifically to catch you believing an AI's explanation.

**"Is my client's data safe with you?"**
For Tier 1 and 2 I never touch it — everything runs in your own Google account and your
own n8n. For Tier 3 I need temporary access to install it, and we sign the data clause in
`08` before I get credentials. Say this before they ask.

**"What if Google changes Sheets, or TikTok changes its export?"**
The automated path matches columns **by header name**, not position, so a raw template
gaining a column doesn't break it. WF2e's mapping layer is one Code node with aliases at
the top — when TikTok renames a column you add one line. That's a genuine answer and a
genuine limitation: someone will eventually have to add that line.

---

## 9. Support burden — plan for it

Self-serve tiers generate support. Budget it before you sell, or Tier 1 becomes a job.

Expected contacts per Tier 1 buyer: **1–2**. Per Tier 2 buyer: **2–4**, clustered in week
one. The recurring ones, all of which have known answers:

| They'll say | The actual cause | Where the answer already lives |
|---|---|---|
| "IMPORTRANGE isn't working" | Prompt not approved, or they're in Excel | README, manual-path section |
| "All my dates are wrong / showing as numbers" | Dates written as text under `RAW`, or serials unformatted | `AUTOMATION_GUIDE`; `n8n/WF2e_FIX…` §Root cause |
| "My ROAS is 0 / everything is blank" | `Daily_Raw_Meta_Ads` stores **text** dates, so date-bounded `SUMIFS` silently returns nothing | README's "Why TEXT() is in there" note; Start Here tab |
| "Landing page views are empty" | Correct — TikTok doesn't report LPV at all, and Meta only at ad level | README, "Known limit, handled honestly" |
| "#REF! in a cell" | They pasted into the two documentation cells that hold example formulas as text | Start Here tab |
| "Health Check says CHECK on rows 23/24" | Working as designed — ad-level doesn't reconcile to account-level | `n8n/WF2e_FIX_TikTok_Raw_Integrity.md` |
| "IC is higher than ATC, is that a bug?" | No. Structural on the reference account (199%). Either buy-now skipping cart, or a mis-mapped event | Report it to *their* client, don't patch the sheet |
| "My registry has no Kit_Sheet_ID" | Prerequisite not done | `09_Delivery_Runbook` step 1 |

**Build this as a public FAQ page before launch.** It deflects most Tier 1 support and it
doubles as an SEO/trust asset. Every row above is already answered somewhere in the repo —
you are assembling, not writing.

Set the boundary in writing at checkout: Tier 1 = community + FAQ, no direct support.
Tier 2 = 30 days email. Tier 3 = 60 days plus a call. Otherwise a $149 buyer will send you
a screen-share request on a Sunday.

---

## 10. Launch sequence

In this order. Do not start selling before step 3.

1. **Run WF4 and WF5 end to end yourself, on one brand.** Fixes the ⚠️ in §2. ~2 hours.
2. **Record the §6 demo.** ~2 hours including retakes.
3. **Write the FAQ** from §9's table. ~2 hours, it's assembly.
4. **Set up Gumroad or Lemon Squeezy** with Tier 1 and Tier 2. Put `LICENCE.md` at checkout.
5. **Post the finding, not the product** (§7 items 2 and 3). One post, real numbers, no link.
6. **Take Tier 1 orders.** Answer every question personally for the first two weeks — the
   questions are your pricing and copy research.
7. **Only now offer Tier 3**, and cap it. You can personally install maybe 3–4 a month
   alongside doing this. Scarcity is honest here, not a tactic.

The `Kit_Sheet_ID` registry column and the WF2e patch are prerequisites inside step 1, not
separate work.

---

## What's in the rest of this package

| File | Use |
|---|---|
| `07_Sales_One_Pager.md` | The thing you send. One page, no fluff, links to the demo |
| `08_Proposal_and_Order_Form.md` | For Tier 3 and agency licences. Scope, deliverables, payment, data clause |
| `09_Delivery_Runbook.md` | What you do after a sale, per tier — including the buyer intake form |
| `LICENCE.md` | Terms of sale. What a buyer may and may not do with the files |
