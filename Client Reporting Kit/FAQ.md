# Frequently Asked Questions

Answers to what buyers actually ask. If yours isn't here, email [address] — questions
before purchase are always welcome and usually get a same-day reply.

---

## Before you buy

### Do I need n8n?

No. **The Kit tier has no automation at all.** You connect it to your data with one formula
and an approved `IMPORTRANGE` prompt, and it works from there. The n8n workflows are the
Kit + Automation tier, and they're optional.

### Do I need to be technical?

For the Kit: if you can paste a formula into a Google Sheet and click "Allow access" on a
prompt, you're fine. The README walks it through with actual cell addresses.

For Kit + Automation: you need to be comfortable importing a JSON workflow into n8n,
creating OAuth credentials, and replacing eight configuration constants at the top of a
file. That's not programming, but it isn't nothing either. If that description makes you
hesitate, take the Done For You tier — that's exactly what it's for.

### Does it work in Excel?

**The manual path does not.** It uses `IMPORTRANGE`, which is a Google Sheets function and
does not exist in Excel, including Excel 365. The files are supplied as `.xlsx` because
Google Drive converts them on upload, and the automated path writes through the Sheets API.

If you're committed to Excel, you'd use Power Query or paste values in manually. The
formulas would work; the self-filling link would not.

### Which platforms?

**Meta and TikTok.** They're treated as genuinely separate — each gets its own dashboard
with no shared data, because blending them hides which one is actually failing. There's one
tab that combines them on purpose, where you can see share of spend against share of
revenue.

Google Ads isn't supported. Adding it means new tabs and new column mappings, not a setting.

### What currency?

Defaults to **EGP**. One cell changes it and every formatted number follows. If you bill in
USD, AED, SAR or anything else, change it before you enter data — see README → *Customising*.

### Can I see it before buying?

Yes. `samples/Sample_Monthly_Report.pdf` is a fully filled five-page report, so you can see
the finished artefact. The dashboard's **Start Here** tab explains every tab in the file
itself. And there's a short screen-recording walking a real account's week:
[link].

### What do I actually receive?

| File | What it is |
|---|---|
| `01_Google_Sheets_Reporting_Dashboard.xlsx` | 11 tabs. Set two dates, everything recalculates |
| `02_Client_Report_Template.xlsx` | 11 tabs. The client-facing report |
| `03_KPI_Calculator.xlsx` | 6 tabs. Margin, breakeven ROAS, POAS, profit bridge |
| `04_Monthly_Report_PDF_Template.pdf` | 5 pages, designed, print-ready |
| `05_AI_Prompts_Campaign_Performance.md` | Twelve grounded prompts |
| `README.md` | Setup, tab guide, customising |
| `samples/Sample_Monthly_Report.pdf` | A filled example |

Kit + Automation adds the `n8n/` folder: two workflows, an automation guide, three
standalone Code nodes, and a data-integrity patch.

---

## Setting it up

### How long does setup take?

Twenty minutes for the manual path, if your data is already in a Google Sheet with the
expected headers. Ninety minutes for the automated install, including running both workflows
by hand before you schedule them.

### My IMPORTRANGE isn't working

Three causes, in order of likelihood:

1. **You never approved the prompt.** The formula reads `#REF!` until you click the cell and
   hit "Allow access." It appears once per source sheet.
2. **You're in Excel.** See above.
3. **The sheet ID in `Fundamentals!N1` is wrong**, or the source sheet isn't shared with
   your account.

### Everything shows zero

Almost always **dates stored as text**. Date-bounded `SUMIFS` will not match a real date
against a text date, and it fails silently — no error, just zeros.

Check the date column in your raw sheet. If the values are left-aligned, they're text. The
fix is to wrap your criteria in `TEXT(range,"yyyy-mm-dd")`; the README's "Why TEXT() is in
there" note explains it, and the Start Here tab ships the corrected snippet.

### Landing Page Views are empty

**That's correct, not a bug.** Meta reports LPV only at *ad* level, never at account level,
and TikTok doesn't report it at all. The kit leaves the field blank rather than mixing Meta
LPVs with TikTok clicks to fake a page-speed metric.

Two ways to get the real number: the automated path already sums `Daily_Raw_Meta_Ads!LPV` up
by date; on the manual path, Start Here has an `ARRAYFORMULA` + `SUMIF` snippet for
`Fundamentals!G2`.

TikTok rows stay blank either way, and the TikTok Dashboard says so in words instead of
showing a misleading zero.

### There's a `#REF!` on the Start Here tab

Two cells on Start Here hold **example formulas as plain text**, on purpose, so you can read
them and copy them. They're not live formulas. Don't paste into them — paste into
`Fundamentals!A2` as the instructions say.

### Benchmarks says `PLACEHOLDER`

Also on purpose. The thresholds ship labelled as placeholders so the status column works the
moment you open the file, but they aren't your client's numbers. Replace rows 7–21 with
their trailing 90 days — **per platform**, since Meta and TikTok have very different CPM and
frequency norms — then set `Benchmarks!B28` to `TUNED`.

Health Check row 29 deliberately stays on `CHECK` until you do, because a benchmark check
pointed at a value nobody has ever edited is a check that can't fail, which is worse than no
check.

### My breakeven ROAS looks wrong and there's a red flag

`KPI Calc!I4` turns red when the cost inputs at `J5/J6/J7` are assumptions rather than
confirmed figures. That's the feature working. Breakeven ROAS = 1 ÷ contribution margin, and
contribution margin comes from your client's COGS, shipping and fees — put estimates in and
you get an estimate out, flagged.

Go ask your client for the real numbers. That conversation is usually worth more than the
report.

---

## Reading the numbers

### Health Check rows 23 and 24 say CHECK

Those rows reconcile **ad-level totals against account-level totals** and flag a gap wider
than 5% on spend or 8% on purchases. If they fire, the gap is real — your ad-level export is
missing rows.

This is common with TikTok, whose ad-level scheduled report can come in around 20% short of
its own account-level total. It isn't something the kit can fix, and hiding it would be
worse. **Quote TikTok totals from `Fundamentals`, never from `Ad Performance`** — ad-level
data is still fine for *ranking* ads against each other.

### Initiate Checkout is higher than Add to Cart

Not a formula error. On the account this was built on, IC ran at 199% of ATC. Two usual
explanations: a buy-now flow that skips the cart, or a mis-mapped event in the pixel. It's a
tracking or business-model question — raise it with the client, don't patch the sheet to
make it look tidy.

### Why are there two separate dashboards?

Because a blended number lets a weak channel hide behind a strong one. On the reference
account, the blended read for one week was "ROAS fell 21%." Split apart: TikTok was at
frequency 4.10 with a 1.65% click-to-purchase rate — creative fatigue, fix with new creative
and a frequency cap. Meta was at 1.46 frequency and 5.23% — healthy, and its dip was
attribution lag, so the fix was *do nothing*.

One blended dashboard tells you to cut both. That would have been a mistake.

### Reach looks too high for a month

Daily reach is summed and labelled "sum of days," because platform reach is deduplicated
*within* a day, not across a month. Summing it and calling it unique people would be a lie,
so the kit doesn't.

### The funnel bars are empty

They're scaled to each step's own target, not to 100%. A 1–2% step would draw nothing
against a full-scale bar. If a bar is empty, the step is far below its target — which is the
information you want.

---

## Automation

### How many API calls does the nightly refresh make?

**Three per brand.** One `values:batchGet` for all four raw tabs, one `values:clear` for the
two data ranges, one `values:batchUpdate` to write them. Twelve brands is about twelve reads
and twenty-four writes, comfortably under Google's 60-per-minute limit, so no throttling is
needed.

Nothing else touches the sheet. That's deliberate: a refresh physically cannot break a
formula, because it only ever writes to `Fundamentals`, `Ad Data` and `_Control`.

### What time does it run?

Whatever you set. The only constraints are that provisioning runs after your sheet-creation
workflow, and the refresh runs **after every data-collection workflow**. On the reference
install that's 10:30 and 14:00. The clock times are irrelevant; the order isn't.

### Is the automation actually proven?

Honestly: the workflow logic is unit-tested, the scheduled end-to-end run is supervised.

The ingest Code node was executed under Node v22 against a `batchGet` payload built from a
real client sheet, and its output matched a delivered workbook exactly as a multiset — 28
account rows and 387 ad rows. The workflow graphs validate with zero broken connections and
zero unreachable nodes.

What hasn't happened is a month of unattended nightly runs. That's why the Done For You tier
includes running the first cycle together, and why the automation guide tells you to run
both workflows manually before you schedule them.

### What if TikTok or Meta changes their export?

The automated path matches columns **by header name, not position**, so a raw template
gaining a column doesn't break it. The TikTok mapping layer is one Code node with column
aliases at the top — when a label changes you add one line.

That's a real answer and a real limitation: eventually someone has to add that line.

### There are duplicate rows in my TikTok raw sheet

That's an upstream bug in the email-import workflow, not in the kit — and it's documented,
diagnosed and patched. See `n8n/WF2e_FIX_TikTok_Raw_Integrity.md`. The kit deduplicates on
read, so your dashboard is already correct; the raw sheet still needs fixing.

---

## Commercial

### Can I use this with unlimited clients?

Yes. Use it with as many of your own clients as you like, forever. Edit anything,
white-label the output, remove the branding, charge whatever you want for your reporting
service.

### Can I resell the templates?

**Not without an agency licence.** You may not redistribute the files, put them in a course
or marketplace, publish them as a free download, or sell the kit to other media buyers.

The line: delivering reporting *to your clients* is unlimited. Selling the tool *to people
who deliver reporting* needs a separate licence. Full terms in `LICENCE.md`.

If you're unsure which side you're on, ask — the answer is usually yes, sometimes for a fee,
and asking costs nothing.

### Is my client's data safe?

On the Kit and Kit + Automation tiers, **the seller never touches it.** Everything runs in
your own Google account and your own n8n instance. There's no phone-home, no telemetry, no
external service.

On Done For You, access is limited to what's in the proposal, for the install period only.
You create every credential — no password, token or API key is ever handed over. Access is
revoked at handover with written confirmation that no copy is retained.

### What's the refund policy?

Fourteen days on the digital tiers, if you haven't already used it with a paying client.
After that, sales are final — files can't be un-downloaded, which is why the sample PDF and
the demo exist before you buy.

Done For You: full refund before the kickoff call; afterwards, pro-rata against undelivered
items.

### What support do I get?

| Tier | Support |
|---|---|
| The Kit | This FAQ and the community. No direct support |
| Kit + Automation | 30 days email |
| Done For You | 60 days email plus calls |

Support covers breakage caused by the product. It doesn't cover your own edits, your
clients' data problems, platform API changes, or general "how do I use n8n" questions.

### Do I get updates?

Minor fixes to the version you bought, at the seller's discretion. New features and new
platform support aren't included and may be sold as upgrades.

---

*Still stuck? Email [address] with a screenshot and the tab name. That's usually enough to
answer in one reply.*
