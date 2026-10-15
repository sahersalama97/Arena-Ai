# The Media Buyer's Client Reporting Kit

Everything a freelance media buyer or small agency needs to report on Meta and TikTok ads — without rebuilding the same spreadsheet every month, and without explaining a number you can't defend.

Built to pair with the **Automated Ads Reporting System** already in this repo (the n8n pipeline). It works completely standalone too — the automation saves you the copy-paste, it isn't required.

> ### 👉 Setting the whole thing up? Start with [`START_HERE.md`](START_HERE.md)
>
> One guide, ten numbered steps, from an empty Google Drive to dashboards that fill
> themselves every night. It covers the three template sheets, the five n8n credentials,
> all ten workflow files in import order, and how to check each step worked. About two
> hours — or 30 minutes if your data pipeline already runs.
>
> The ten workflow JSONs are in [`n8n/workflows/`](n8n/workflows), numbered in the order you
> import them. Run [`_build/personalise_workflows.py`](_build/personalise_workflows.py)
> once to replace all 254 hardcoded IDs, credentials and email addresses with your own —
> it refuses to run until they're all filled in, and re-checks its own output afterwards.

---

## What's in the kit

| File | What it is | Open it when |
|------|-----------|--------------|
| `01_Google_Sheets_Reporting_Dashboard.xlsx` | Live dashboard. Set two dates, everything recalculates. | Every day |
| `02_Client_Report_Template.xlsx` | The client-facing report. Eleven tabs, mirroring the pipeline's report sheets. | Once a month |
| `03_KPI_Calculator.xlsx` | The math engine: breakeven ROAS, contribution margin, POAS, driver decomposition. | Every month, before you report |
| `04_Monthly_Report_PDF_Template.pdf` | Five-page designed PDF report. Blank, print-ready. | Once a month |
| `05_AI_Prompts_Campaign_Performance.md` | Twelve prompts for turning numbers into language, each grounded in a specific tab. | Every week and month |
| `samples/Sample_Monthly_Report.pdf` | A filled-in example of the PDF, so you can see the finished thing. | First, to see what you're aiming at |
| `START_HERE.md` | The A-to-Z setup guide for the whole system, workflows included. | **Before anything else** |
| `n8n/workflows/` | All ten workflow JSONs, numbered in import order. | During setup |

---

## The one idea behind all of it

**Never report ROAS without breakeven ROAS next to it.**

A 2.4x ROAS sounds fine until you learn that client's breakeven is 2.8x — at which point every order has been losing money, and nobody noticed because nobody had asked for the cost structure.

Breakeven ROAS is `1 ÷ contribution margin %`, and contribution margin comes from the client's own numbers: product cost, shipping, payment fees, returns. It is not an industry benchmark, and it is different for every client. The KPI Calculator works it out; everything else in the kit reads against it.

This is the difference between a report that lists metrics and a report that answers the question the client is actually asking. It is also what makes you hard to replace with a cheaper freelancer who sends prettier charts.

---

## Quick start (20 minutes)

**1 · Set your numbers up once**
Open `03_KPI_Calculator.xlsx` → **Calculator** tab. Fill the nine amber cells under *Media Inputs* and the nine under *Business Inputs*. The business inputs are the ones you have to ask the client for — product margin, shipping cost per order, payment fees, return rate. Get these. A worked example is already loaded so you can see how it behaves.

**2 · Read the verdict**
Section 5 writes five plain-English sentences from your numbers, including which funnel step is your tightest bottleneck. Section 6 runs sanity checks — if any row goes red, fix the data before you report anything.

**3 · Point the dashboard at your data**
Open `01_Google_Sheets_Reporting_Dashboard.xlsx` → **Fundamentals** and **Ad Data** tabs. Paste your exports. Sample data is included; delete it. Column order matters — don't reorder columns. If you run the n8n pipeline, the **Start Here** tab has a one-formula link that pulls straight from your Raw Data sheet so you never paste again.

**4 · Run the month**
Open `02_Client_Report_Template.xlsx` → `_Inputs` tab. Fill the cover block, paste your platform overviews, and fill the six CONTEXT lines. Then open `05_AI_Prompts_Campaign_Performance.md` and run **Prompt 1** (the monthly narrative) on the whole thing. Paste the output into row 56–60 of `_Inputs`.

**5 · Ship it**
Export the report template as PDF, or use `04_Monthly_Report_PDF_Template.pdf` as the designed shell. Delete the `_Inputs` tab before sending — it holds your internal notes.

---

## How it plugs into the automated pipeline

The n8n system in `Automated Ads Reporting System_files/` writes to predictable places. The kit is built to match them exactly, so nothing contradicts anything the automation already produces.

**What the kit reads**

| Automation tab | Kit tab | Notes |
|---|---|---|
| `Daily_Raw_Meta`, `Daily_Raw_TikTok` | Dashboard → `Fundamentals` | Account-level daily rows |
| `Daily_Raw_Meta_Ads`, `Daily_Raw_TikTok_Ads` | Dashboard → `Ad Data` | Ad-level daily rows |
| `Meta Overview`, `TikTok Overview` | Report → `_Inputs` blocks 2 & 3 | Metric rows already match, 1:1 |
| `Combined` | Report → `_Inputs` block 1 | Spend, Purchases, Cost Per Purchase, Purchases Value, ROAS, AOV |
| `Meta/TikTok Ad Performance`, `… Creatives Performance`, `… Weekly` | Report → `Top Ads`, `Creatives`, `Weekly Trend` | Top 10 by spend, same ranking |


**Data-integrity note for the TikTok raw tab.** While building WF5 we found that `Daily_Raw_TikTok_Ads` accumulates duplicate `(Date, Ad_ID)` rows and stores two Ad_IDs as 16-digit *numbers*, which Google Sheets silently rounds to 15 significant digits — the last digit is destroyed and those rows can never be matched again. The kit deduplicates on read, so nothing here is wrong, but the raw sheet is. Full diagnosis, a tested three-node patch for WF2e, and a one-off cleanup procedure: **[`n8n/WF2e_FIX_TikTok_Raw_Integrity.md`](n8n/WF2e_FIX_TikTok_Raw_Integrity.md)**.
**Fully automated — two n8n workflows.** If you run the pipeline, you don't paste anything and you don't maintain a link formula either. See **[`n8n/AUTOMATION_GUIDE.md`](n8n/AUTOMATION_GUIDE.md)**. WF4 copies a dashboard per client; WF5 reads the four raw tabs and fills it every night at 14:00, choosing the reporting window from the data. Three Sheets API calls per brand.

**Manual alternative — one formula.** On the Dashboard's **Start Here** tab there's a `LET` / `VSTACK` / `HSTACK` / `CHOOSECOLS` formula. Put your Raw Data sheet ID in `Fundamentals!N1`, paste that one formula into `Fundamentals!A2`, and the dashboard fills itself from the pipeline — Meta and TikTok both, labels included. Approve the IMPORTRANGE prompt once.

The column mapping is explicit and verified against the `ONE-OFF Template Prep` headers. The automated path matches these **by header name** rather than by position, so it survives a raw template gaining a column; the manual formula uses the positions below:


| Kit column | `Daily_Raw_Meta` | `Daily_Raw_TikTok` |
|---|---|---|
| Date | 1 | 1 |
| Spend | 2 | 2 |
| Impressions | 3 | 3 |
| Reach | 4 | 4 |
| Clicks | 7 | 6 |
| Add to Cart | 9 | 11 |
| Initiate Checkout | 10 | 12 |
| Purchases | 11 | 13 |
| Revenue | 12 | 14 |

**Google Sheets only.** `IMPORTRANGE` doesn't exist in Excel, even Excel 365. In Excel, use Power Query or paste.

**Known limit, handled honestly.** The *manual* link formula leaves Landing Page Views blank, on purpose. Meta reports LPV only at *ad* level (column N of `Daily_Raw_Meta_Ads`), never at account level, and TikTok doesn't report it at all. The kit leaves it blank rather than mixing Meta LPVs with TikTok clicks to fake a page-speed metric. Two ways to get the real number:

- **Automated installs:** WF5 already sums `Daily_Raw_Meta_Ads!LPV` up by date into the Meta rows, so nothing to do.
- **Manual installs:** the **Start Here** tab has an `ARRAYFORMULA` + `SUMIF` snippet for `Fundamentals!G2`. Note it wraps the criteria in `TEXT(...,"yyyy-mm-dd")` — `Daily_Raw_Meta_Ads` stores dates as *text*, and `SUMIF` will not match a real date against text, so without the wrapper it silently returns 0 and the click-to-landing-page rate reads 0.0%.

TikTok rows stay blank either way; the TikTok Dashboard says so in words instead of showing a zero.

**The currency.** Both the pipeline and this kit default to **EGP**. To change it: see *Customising* below.

---

## The tabs, briefly

### Dashboard (`01_…`) — 11 tabs
**Start Here** — how to use it, plus the pipeline link.
**Fundamentals / Ad Data** — your data goes here. Column order is the contract.
**KPI Calc** — every metric, current vs comparison, with a status column that reads from Benchmarks. Its four period cells read from `_Control`, so there is only ever one place to change the dates.
**`_Control`** — the automation's write target, and the only tab it writes. Four period dates plus `Brand_Name`, `Last_Refresh` and `Rows_Synced`, so a stale dashboard is obvious at a glance.
**Dashboard** — the blended, client-facing view: KPI tiles, platform split, funnel with targets, and auto-written commentary lines you can paste into an email.
**Meta Dashboard** — Meta only. Every figure on the tab is filtered to Meta, and it is graded against Benchmarks on its own.
**TikTok Dashboard** — TikTok only. Same shape, its own numbers. States plainly that TikTok reports no landing page views rather than showing 0%.
**Ad Performance** — one row per ad, ranked by spend *inside the selected period*, with a verdict that reads against breakeven. Column A is a live query, so it re-ranks itself whenever the period changes.
**Benchmarks** — the thresholds that decide every status. Placeholders ship so it works on day one; replace them with your own trailing 90 days.
**Health Check** — proves ad-level data reconciles to account-level data, and flags impossible numbers. Run it before every client conversation.

**Why three dashboards instead of one.** Blended numbers let a weak channel hide behind a strong one. On one live client account, 8–14 Oct against 1–7 Oct, the blended read is "ROAS fell 21%". Split apart it is two unrelated problems: TikTok's frequency hit 4.10 with click-to-purchase at 1.65%, while Meta sat at 1.46 frequency and 5.23% click-to-purchase. One says *refresh creative and cap frequency*; the other says *leave it alone*. A single blended dashboard cannot tell you that.

### Client Report (`02_…`) — 11 tabs
**`_Inputs`** — internal. All numbers live here; every other tab reads from it.
**Cover / Executive Summary / Performance / Platform Detail / Combined / Top Ads / Creatives / Weekly Trend / What We Did & Next / Dictionary** — the client-facing pages.
**Combined** — the one tab where Meta and TikTok deliberately share a row: side-by-side metrics with each platform's share of spend and revenue, a combined funnel, and a "which platform is earning its keep" block that compares share of spend against share of revenue.


### KPI Calculator (`03_…`)
**Calculator** — 9 media inputs + 9 business inputs → funnel rates, unit economics, breakeven ROAS, POAS, five sentences of verdict, seven sanity checks.
**Profit Bridge** — revenue-to-profit waterfall, plus a "what ROAS do you actually need" sensitivity table.
**Period Compare** — decomposes a ROAS move into CPM / CTR / CVR / AOV so you can name the cause.
**Benchmarks / Metric Dictionary** — thresholds and shared definitions.

---

## Customising

**Currency.** Change `CURRENCY_CODE` in `_build/kitstyle.py` and the `CURRENCY` value in `_build/sample_data.py`, then rebuild. Every money format and label follows.

**Your own numbers in the PDF.** Edit `monthly_data()` in `_build/build_pdf.py` to read from your source instead of the sample, then:

```bash
cd "Client Reporting Kit"
python3 "_build/build_pdf.py"          # both PDFs
python3 "_build/build_pdf.py" sample   # just the filled example
python3 "_build/build_pdf.py" template # just the blank template
```

**Rebuilding the spreadsheets.** Each builder is standalone and reads one shared style module:

```bash
python3 "_build/build_dashboard.py"
python3 "_build/build_kpi_calculator.py"
python3 "_build/build_client_report.py"
```

Requires `openpyxl`, `fpdf2`, and `matplotlib` (only for the bundled Inter font files). The sample data is seeded, so rebuilds are reproducible and the three workbooks always agree with each other.

**Fonts.** The kit ships Inter (SIL Open Font License) for the PDF report only — the spreadsheets use whatever the system has. Fonts live in `_build/fonts/`.

---

## What this kit deliberately does not do

- **It doesn't pull data from the APIs.** That's the n8n pipeline's job. This is the reporting and interpretation layer.
- **It doesn't invent benchmarks.** The placeholder thresholds exist so the status column works immediately; they are labelled as placeholders and should be replaced with the client's own trailing range.
- **It doesn't calculate in AI.** Every metric has a visible, auditable formula. AI writes the language, not the arithmetic.
- **It doesn't sum reach across a month and call it unique people.** Daily reach is summed and labelled as such, because platform reach is deduplicated within a day, not across a month.

---

## Sample data

Every file ships with a worked example: *Northwind Supply Co.*, September 2026 vs August 2026 — a D2C brand running Meta and TikTok in EGP, with realistic weekly seasonality, CPM creep, and one deliberately soft week. The numbers are internally consistent across all five deliverables, including ad-level spend reconciling to account-level spend.

Use it to understand how the kit behaves, then delete it.

---

## Arabic / العربية

Two files are available in Arabic, for buyers whose clients read Arabic:

| File | What it is |
|---|---|
| `README_AR.md` | This README, in Arabic — the setup walkthrough with the same cell addresses |
| `05_AI_Prompts_AR.md` | All twelve prompts in Arabic, so the narrative they produce is client-ready Arabic rather than a translation |

The input block inside the Arabic prompts keeps its field names in **English on purpose** —
they match the column headers in the sheets, and the prompts refer to them by name. The
instructions and the required output are Arabic. Sheet tab names and cell addresses stay in
Latin script in both versions, because the sheets themselves are English.

---

## Licence and reuse

**Using it to deliver work: wide open.** Use the kit with as many of your own clients as you
like, edit anything, white-label the output, charge whatever you want for your reporting
service, and share it with your own staff and contractors. No limit and no extra fee.

**Reselling the files themselves: not without an agency licence.** You may not redistribute
the templates, put them in a course or marketplace, publish them as a free download, or sell
the kit to other media buyers. The line is: delivering reporting *to your clients* is
unlimited; selling the tool *to people who deliver reporting* needs a separate licence.

Full terms — warranty, liability, support windows, refunds, data protection, termination —
are in **[`LICENCE.md`](LICENCE.md)**. If you're unsure which side of the line your use falls
on, ask before assuming.

The Inter typeface is included under the SIL Open Font License — see `_build/fonts/`.

---

## Selling this system

If you want to offer this to other media buyers and agencies rather than just use it
yourself, these are the working documents:

| File | What it is |
|---|---|
| `06_Sell_This_System.md` | Positioning, three-tier offer, pricing and how to price across markets, an honest readiness table of what is and isn't safe to promise, the demo script, channels, objections, support burden, launch sequence |
| `07_Sales_One_Pager.md` | The one page you send. Real numbers from a live account |
| `08_Proposal_and_Order_Form.md` | For done-for-you and agency sales: scope, deliverables, timeline, exclusions, disclosed limitations, data protection, warranty, acceptance test |
| `09_Delivery_Runbook.md` | What to do after a sale, per tier — including the eight constants a buyer must replace, the install order, the schedule map, the intake form, and a breakage table |

Start with `06` §2. It lists what is genuinely verified versus what is built but never run
end to end, and selling against it is the difference between a product with refunds and one
without.

