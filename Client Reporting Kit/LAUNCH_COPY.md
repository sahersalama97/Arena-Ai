# Launch Copy

Ready to paste. Three assets: the store listing, the buyer welcome email, and the community
post that isn't an advert. Plus the two follow-ups that do the actual selling.

Replace `[brackets]`. Delete the notes to yourself before publishing.

---

## 1. Store listing (Gumroad / Lemon Squeezy)

### Product name

**The Media Buyer's Client Reporting System — Meta + TikTok**

### Subtitle / one-liner

> A Google Sheets reporting system for media buyers: separate Meta and TikTok dashboards,
> a client report, breakeven-ROAS maths, a PDF template, and twelve AI prompts. Works
> standalone; automates fully if you run n8n.

### Description

**You report on two platforms. Your client asks why ROAS moved. Your dashboard shows one
blended number, so the honest answer is "I don't know."**

This is the system that fixes that.

It was built for a live e-commerce account running Meta and TikTok through an n8n pipeline,
and in its first week it found two things nobody had noticed: thirteen duplicated ad-days
double-counting 1,545 EGP of spend, and TikTok's ad-level export coming in 17.6% short
against the platform's own account-level total.

**What makes it different from Looker Studio or AgencyAnalytics:**

- **Breakeven ROAS sits next to ROAS.** A 2.4x looks fine until you know breakeven is 2.8x
  — at which point every order lost money. Derived from your client's own COGS, shipping and
  fees. Not an industry benchmark.
- **The platforms stay separate, deliberately.** Meta and TikTok each get their own
  dashboard with zero shared data. One tab combines them on purpose, showing share of spend
  against share of revenue — because that comparison is the whole argument.
- **It checks its own input data.** Health Check reconciles ad-level against account-level
  totals and flags the gap instead of reporting numbers you can't defend.
- **Every number is an auditable formula.** 1,316 live formulas across three spreadsheets.
  Zero hard-coded results. The AI writes the language; the arithmetic stays in the sheet.

**The difference the split makes, on real data.** One week, blended: *"ROAS fell 21%, cut
spend."* Split apart: TikTok at frequency 4.10 with a 1.65% click-to-purchase rate — creative
fatigue, fix with new creative and a cap. Meta at 1.46 frequency and 5.23% — healthy, and its
dip was attribution lag, so the fix was do nothing. One blended dashboard tells you to cut
both.

**What's included**

| | |
|---|---|
| Reporting dashboard | 11 tabs — set two dates, everything recalculates. Separate Meta and TikTok dashboards, live-ranked top-25 ad table, benchmarks, Health Check |
| Client report | 11 tabs — cover, executive summary, performance, platform detail, combined, top ads, creatives, weekly trend, next steps, metric dictionary |
| KPI calculator | 6 tabs — contribution margin, breakeven ROAS, POAS, profit bridge, period compare |
| Monthly PDF | 5 pages, designed, print-ready, Meta / TikTok / Combined columns |
| AI prompts | 12 — the narrative, the bad month, creative learnings, the budget recommendation, the 9pm complaint email, the platform split decision, the self-audit |
| Docs | Setup guide with real cell addresses, FAQ, sample filled report |

**Requirements**

- Google Sheets (the manual path uses `IMPORTRANGE`, which does not exist in Excel)
- A data source: either the included n8n workflows, or a sheet with the documented headers
- For the Automation tier: your own n8n instance

**Honest limitations**

- It doesn't pull from the ad APIs. It's the reporting layer on top of a pipeline you
  already have.
- Benchmark thresholds ship as labelled placeholders for you to replace with your client's
  trailing data.
- TikTok's ad-level export can under-report spend. That's platform-side; the kit surfaces it
  rather than hiding it.
- The n8n workflow logic is unit-tested against real data. Nobody has yet run it unattended
  for a month — which is why the Automation tier says "supervised first run," and why Done
  For You includes running the first cycle with you.

**Licence** — use it with unlimited clients, edit it, white-label it. Reselling the files
needs an agency licence. [Full terms]

### Pricing tiers on the listing

| Name | Price | One line |
|---|---|---|
| The Kit | $149 | Everything above, manual setup, no n8n |
| Kit + Automation | $449 | Adds both n8n workflows, the code nodes, the integrity patch, 30 days support |
| Done For You | $1,500 + $79/mo | I install it in your n8n, onboard two clients, run the first cycle with you, 60 days support |

**Upgrade note to put on the page:** upgraded within 90 days, you pay the difference, not
the full price.

### Call to action

> Get the Kit — $149, instant download. Watch the four-minute demo first if you like; it
> uses a real account's real week.

---

## 2. Buyer welcome email

Send automatically on purchase. Keep it short — they want the files, not a newsletter.

**Subject:** Your reporting system — start here (20 minutes)

```
Thanks — here's everything.

[download link]

Start with README.md → "Quick start (20 minutes)". It uses real cell
addresses, so you can follow it click by click.

Three things that save most people an hour:

1. It's Google Sheets only. The manual path uses IMPORTRANGE, which does
   not exist in Excel — not even 365. If you're in Excel, reply now and
   I'll tell you what will and won't work.

2. Set your currency in one cell BEFORE you enter data. It defaults to
   EGP. README → Customising.

3. If every number comes out as zero, your dates are stored as text.
   Date-bounded SUMIFS will not match a real date against a text date,
   and it fails silently. The fix is one TEXT() wrapper — README explains
   it, and the Start Here tab ships the corrected formula.

Two things that look like bugs but aren't:

- Landing Page Views are blank. Correct. Meta reports LPV only at ad
  level and TikTok doesn't report it at all. There's a snippet for Meta
  on the Start Here tab.
- Benchmarks says PLACEHOLDER. Also correct. They're deliberately
  labelled so you replace them with your client's trailing data. Until
  you do, Health Check row 29 stays on CHECK on purpose.

The FAQ covers the rest: [link]

[Buyers of Kit + Automation, add:]
Your n8n folder has one prerequisite people miss: the eight constants at
the top of build_n8n_workflows.py contain MY sheet IDs and credential
IDs. Replace them before importing, and run both workflows MANUALLY once
before you schedule them. SETUP_GUIDE.md Part A walks it in order with a
check at every step.

Reply to this email if you get stuck. I answer them personally.

[your name]
```

**Note to self:** for Kit + Automation buyers, add one line asking them to reply with the
result of their first manual run. It's the only way you'll learn where the install actually
breaks, and early buyers will do it.

---

## 3. The community post

For r/PPC, r/FacebookAds, media-buyer Slack and Facebook groups. **Post the finding, not
the product.** These communities ban self-promotion and reward specificity — and a genuine
finding gets further than an ad anyway.

No link in the post. Link in your profile. Answer every comment.

**Title:** Built a check that reconciles ad-level spend against account-level. It immediately found 13 duplicated ad-days and a 17.6% TikTok shortfall.

```
I got tired of not knowing whether the numbers in my reports were actually
right, so I built a Health Check tab that reconciles ad-level totals against
account-level totals for the same period and flags any gap over 5% on spend
or 8% on purchases.

Ran it on a live e-commerce account doing Meta + TikTok. It fired immediately.

Two findings:

1. Thirteen (date, ad ID) pairs were stored twice in the TikTok ad-level tab
   — the same ad-day from two different sync runs. Double-counted 1,545 EGP
   of spend and 4,935 of revenue. The import workflow was configured to
   upsert on date + ad ID, so it looked correct. It matched nothing: the
   dates were written as real dates and read back as datetimes, so the keys
   never compared equal and every row got appended.

2. TikTok's ad-level export came in 17.6% short on spend against TikTok's
   own account-level total for the same week — 25.8% short on revenue, 30.1%
   on purchases. Meta reconciled to 0.00%. So it isn't my math.

The second one changed how I report. Ad-level data is still fine for ranking
ads against each other, but I now quote TikTok platform totals from
account-level only. I'd have kept quoting the ad-level total as "TikTok
spend" and been confidently wrong.

Separately — and this is the part I'd want someone to have told me — the same
account showed why you shouldn't blend two platforms into one dashboard.

Blended, the week read "ROAS fell 21%." Split apart:

- TikTok: frequency 4.10, click-to-purchase 1.65%. Creative fatigue. Fix is
  new creative and a frequency cap.
- Meta: frequency 1.46, click-to-purchase 5.23%. Healthy. The dip was
  attribution lag. Fix is do nothing.

A blended dashboard tells you to cut both. One of those would have been
exactly wrong.

Happy to answer questions about the reconciliation approach. Curious whether
anyone else has seen the TikTok ad-level shortfall, or whether it's specific
to how that account's scheduled report is configured.
```

**Why this works:** it's a real finding with real numbers, it admits what you don't know
(the last line), and it asks a question the community can answer. Nobody gets sold to. The
people who want what you built will ask.

**Don't:** post the same text in five groups on the same day. Space it out, and vary the
opening line so it doesn't read as a campaign.

---

## 4. Follow-up sequence

Most sales happen here, not on the listing page.

### Day 3 — the check-in

**Subject:** Did the dates thing bite you?

```
Quick one — no pitch.

The single most common problem in the first week is every number coming out
as zero, and it's almost always dates stored as text. Date-bounded SUMIFS
won't match a real date against a text date, and Sheets fails silently
instead of erroring, so it looks like the sheet is broken.

Did that happen to you? If so, the fix is a one-line TEXT() wrapper and I'll
send it straight over.

If everything's working, ignore this — but tell me what you built first,
because I'd genuinely like to know what people use it for.

[your name]
```

### Day 10 — the upgrade, to Kit buyers only

**Subject:** The 90-day upgrade window

```
You're [N] days in, so you're inside the 90-day upgrade window — if you ever
want the n8n automation, you pay the difference between tiers, not the full
Kit + Automation price.

Worth knowing what it actually buys you: three Sheets API calls per brand per
night, and nothing else touches the sheet, so a refresh can't break a
formula. On the reference install that's twelve brands refreshed every night
at 14:00 with no one doing anything.

The honest caveat: the workflow logic is unit-tested against real data, but
nobody has run it unattended for a month yet. That's why the guide has you
run both workflows manually before you schedule them.

If you'd rather I just did it, that's the Done For You tier — I install it in
your n8n, onboard two of your clients, and we run the first nightly cycle
together. I take a limited number of those a month because I do them
personally.

Either way, no rush. Reply if you want details.

[your name]
```

---

## 5. Launch checklist

In order. Don't skip step 1.

- [ ] **Run WF4 and WF5 end to end yourself, on one brand.** This is the only thing standing
      between "built" and "sellable." `SETUP_GUIDE.md` Part A.
- [ ] Confirm `_Control!B2:B8` populated and both platform tabs show only their own platform
- [ ] Ask GOFRESH for real COGS / other / shipping so `KPI Calc!I4` stops being red
- [ ] Install the WF2e patch and clean the existing duplicates (Part C)
- [ ] Record the four-minute demo. Under four minutes, 1080p, no music. Show the Health
      Check flag on screen
- [ ] Fill every `[bracket]` in `LICENCE.md`, `07`, `08`
- [ ] Publish the FAQ somewhere with a URL
- [ ] Set up Gumroad or Lemon Squeezy — **merchant of record**, so VAT/GST across three
      markets isn't your problem
- [ ] Upload the sample PDF and put the demo on the listing page
- [ ] Post §3 in **one** community. One. Answer every comment
- [ ] Take orders. Answer every question personally for two weeks — the questions are your
      pricing and copy research
- [ ] Only now offer Done For You, and cap it at what you can personally install

**Do not build an audience before step 1 passes.** You'd be advertising something you
haven't watched work.
