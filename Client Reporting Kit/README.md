# The Media Buyer's Client Reporting Kit

Everything a freelance media buyer or small agency needs to report on Meta and TikTok ads — without rebuilding the same spreadsheet every month, and without explaining a number you can't defend.

Built to pair with the **Automated Ads Reporting System** already in this repo (the n8n pipeline). It works completely standalone too — the automation saves you the copy-paste, it isn't required.

---

## What's in the kit

| File | What it is | Open it when |
|------|-----------|--------------|
| `01_Google_Sheets_Reporting_Dashboard.xlsx` | Live dashboard. Set two dates, everything recalculates. | Every day |
| `02_Client_Report_Template.xlsx` | The client-facing report. Ten tabs, mirroring the pipeline's report sheets. | Once a month |
| `03_KPI_Calculator.xlsx` | The math engine: breakeven ROAS, contribution margin, POAS, driver decomposition. | Every month, before you report |
| `04_Monthly_Report_PDF_Template.pdf` | Five-page designed PDF report. Blank, print-ready. | Once a month |
| `05_AI_Prompts_Campaign_Performance.md` | Eleven prompts for turning numbers into language. | Every week and month |
| `samples/Sample_Monthly_Report.pdf` | A filled-in example of the PDF, so you can see the finished thing. | First, to see what you're aiming at |

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
Open `02_Client_Report_Template.xlsx` → `_Inputs` tab. Fill the cover block, paste your platform overviews, and fill the six CONTEXT lines. Then open `05_AI_Prompts...md` and run **Prompt 1** (the monthly narrative) on the whole thing. Paste the output into row 56–60 of `_Inputs`.

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

**One-formula link, instead of pasting.** On the Dashboard's **Start Here** tab there's a `VSTACK` / `HSTACK` / `CHOOSECOLS` formula. Put your Raw Data sheet ID in `Fundamentals!N1`, paste that one formula into `Fundamentals!A2`, and the dashboard fills itself from the pipeline — Meta and TikTok both, labels included. Approve the IMPORTRANGE prompt once.

**Known limit, handled honestly.** TikTok doesn't report landing page views, so the kit leaves that blank for TikTok rather than mixing Meta LPVs with TikTok clicks to fake a page-speed metric. The pipeline's own report generator makes the same distinction.

**The currency.** Both the pipeline and this kit default to **EGP**. To change it: see *Customising* below.

---

## The tabs, briefly

### Dashboard (`01_…`)
**Start Here** — how to use it, plus the pipeline link.
**Fundamentals / Ad Data** — your data goes here. Column order is the contract.
**KPI Calc** — every metric, current vs comparison, with a status column that reads from Benchmarks. Also the four cells you set each period.
**Dashboard** — the client-facing view: KPI tiles, platform split, funnel with targets, and five auto-written commentary lines you can paste into an email.
**Ad Performance** — one row per ad, ranked by spend, with a verdict that reads against breakeven.
**Benchmarks** — the thresholds that decide every status. Placeholders ship so it works on day one; replace them with your own trailing 90 days.
**Health Check** — proves ad-level data reconciles to account-level data, and flags impossible numbers. Run it before every client conversation.

### Client Report (`02_…`)
**`_Inputs`** — internal. All numbers live here; every other tab reads from it.
**Cover / Executive Summary / Performance / Platform Detail / Top Ads / Creatives / Weekly Trend / What We Did & Next / Dictionary** — the client-facing pages.

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

## Licence and reuse

Kit contents: use them with your clients, edit them, white-label them, sell your reporting service with them. The Inter typeface is included under the SIL Open Font License — see `_build/fonts/`.
