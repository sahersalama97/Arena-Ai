# START HERE — the whole system, A to Z

Read this top to bottom once, then follow it. Every step says what to do and how to
check it worked. If a check fails, fix it before moving on.

**Total time: about 2 hours.** If the data pipeline already runs for you, skip to
**Step 6** — that's about 30 minutes.

---

## What you are setting up

Two halves:

1. **The pipeline** — pulls your ad data from Meta and TikTok into Google Sheets every day.
2. **The reporting kit** — turns that data into a dashboard per client, automatically, every night.

When it's finished, this happens without you:

```
05:00  find your ad accounts
06:00  pull Meta account-level numbers
06:15  pull Meta ad-level numbers
10:00  make a Raw sheet and a Report sheet for any new client
10:30  make a dashboard for any new client          <- kit
12:00  import the TikTok report that arrived by email
13:00  fill this month's report and email it
14:00  fill every dashboard from the raw data        <- kit
```

You open a dashboard. It is already filled. That's the product.

---

## What you need before you start

- [ ] A Google account
- [ ] An n8n account (n8n.cloud, or your own server)
- [ ] Meta: a System User access token with `ads_read` permission
- [ ] TikTok: your advertiser IDs. If TikTok sends you reports by email, the mailbox
- [ ] About 2 hours

---

## Step 1 — Make a home for everything in Google Drive

Create one folder. Call it `Ads Reporting System`.

Inside it make three more folders:

| Folder | What goes in it |
|---|---|
| `Masters` | The two template sheets every client is copied from |
| `Clients` | One Raw sheet and one Report sheet per client, made automatically |
| `Dashboards` | One dashboard per client, made automatically |

You will need the **folder IDs** later. Get one by opening the folder and copying the
long string from the URL:

```
https://drive.google.com/drive/folders/<THIS PART>
```

✔ **Check:** four folders exist and you have written down the three IDs.

---

## Step 2 — Make the three sheets

You need three spreadsheets. Everything else is copied from these.

### 2a. Brand Registry

One sheet, one tab called `Sheet1`, with these headers in row 1 **in this order**:

```
A Brand_Name              B Platform              C Meta_Ad_Account_ID
D TikTok_Advertiser_ID    E Report_Email          F Raw_Sheet_ID
G Current_Month_Report_Sheet_ID                   H Status
I Discovered_At           J Kit_Sheet_ID
```

Leave every row below empty. The workflows fill it.

`J Kit_Sheet_ID` is the one people forget. WF4 writes each client's dashboard ID there
and WF5 reads it back. Without the header, dashboards get created and nothing can find
them — and there is no error message.

✔ **Check:** ten headers, spelled exactly, `Kit_Sheet_ID` in J1.

### 2b. Raw Data master template

An empty spreadsheet in `Masters`. It needs four tabs, with headers in row 1:

| Tab | Columns |
|---|---|
| `Daily_Raw_Meta` | Date, Spend, Impressions, Reach, Frequency, CPM, Clicks, CTR_Pct, Adds_to_Cart, Initiate_Checkout, Purchases, Purchases_Value, ROAS, AOV, Purchase_CVR_Pct, Pulled_At |
| `Daily_Raw_Meta_Ads` | Date, Ad_ID, Ad_Name, AdSet_Name, Campaign_Name, Creative_Key, Spend, Impressions, Reach, Frequency, CPM, Clicks, CTR_Pct, LPV, Adds_to_Cart, Initiate_Checkout, Purchases, Purchases_Value, ROAS, AOV, Purchase_CVR_Pct, Pulled_At |
| `Daily_Raw_TikTok` | Date, Spend, Impressions, Reach, CPM, Clicks, CTR_Pct, Frequency, Profile_Visits, Follows, Adds_to_Cart, Initiate_Checkout, Purchases, Purchases_Value, ROAS, AOV, Purchase_CVR_Pct, Pulled_At |
| `Daily_Raw_TikTok_Ads` | Date, Ad_ID, Ad_Name, Campaign_Name, AdGroup_Name, Creative_Key, Spend, Impressions, Reach, CPM, Clicks, CTR_Pct, Profile_Visits, Follows, Adds_to_Cart, Initiate_Checkout, Purchases, Purchases_Value, ROAS, AOV, Purchase_CVR_Pct, Pulled_At, Frequency |

**Set column B of both `_Ads` tabs to Plain text** (Format → Number → Plain text) before
anything writes to it. TikTok ad IDs are 16 digits; Google Sheets keeps only 15 significant
digits in a number, so the last digit is destroyed. Plain text prevents that. See
`n8n/WF2e_FIX_TikTok_Raw_Integrity.md`.

The workflow `00_ONE-OFF_Template_Prep` can build these headers for you — see Step 4.

### 2c. Ads Report master template

An empty spreadsheet in `Masters` with nine tabs:

```
Meta Overview        Meta Ad Performance      Meta Creatives Performance    Meta Weekly
TikTok Overview      TikTok Ad Performance    TikTok Creatives Performance  TikTok Weekly
Combined
```

✔ **Check:** three sheets exist. **Write down all three IDs** — you need them in Step 5.

---

## Step 3 — Upload the reporting kit

Upload `01_Google_Sheets_Reporting_Dashboard.xlsx` to the `Masters` folder and let Google
convert it to a Google Sheet.

This is the **kit template**. WF4 copies it once per client. Treat it as read-only:
anything you change here appears in every future client's dashboard.

✔ **Check:** it opens in Google Sheets and shows **11 tabs** — Start Here, Fundamentals,
Ad Data, KPI Calc, `_Control`, Dashboard, Meta Dashboard, TikTok Dashboard, Ad Performance,
Benchmarks, Health Check. Write down its ID.

You now have **four IDs**: Registry, Raw master, Report master, Kit template.

---

## Step 4 — Create your n8n credentials

In n8n go to **Credentials → Add credential** and make these five:

| Credential | Type | Used by |
|---|---|---|
| Google Sheets | Google Sheets OAuth2 | everything |
| Google Drive | Google Drive OAuth2 | making and sharing client sheets |
| SMTP | SMTP | sending reports |
| Gmail | Gmail OAuth2 | reading TikTok report emails |
| Meta token | Header Auth | calling the Meta API |

For the Meta one: Header Auth, name the header `Authorization`, value
`Bearer YOUR_TOKEN`.

After each is saved, open it again — **the ID is in the browser URL**. Write down all five
IDs and the five names you gave them.

✔ **Check:** five credentials, ten values written down.

---

## Step 5 — Make the workflows yours

The ten workflow files contain the original author's sheet IDs, credential IDs and email
addresses — **17 distinct values appearing 254 times** between them. Do not edit them by
hand.

Open `_build/personalise_workflows.py` and fill in the `CONFIG` block at the top with the
values you wrote down in Steps 2, 3 and 4. Then run:

```bash
python3 "_build/personalise_workflows.py"
```

It writes your copies to `n8n/workflows_READY/`.

The script protects you three ways:

- It **refuses to run** while any CONFIG value is still `CHANGE_ME`.
- It **refuses to run** if one of its patterns no longer matches the shipped files, because
  that would mean part of the output silently keeps the original author's ID.
- Afterwards it **re-reads every output file** and reports any original value that survived.

To see what is currently inside the files without changing anything:

```bash
python3 "_build/personalise_workflows.py" --check
```

✔ **Check:** the script printed `Done. Import the 10 files…` and the leftover check said
`none`. If it printed the `TEST_MODE` warning, that's expected — read Step 9.

**Can't run Python?** (This is the normal case if you downloaded the kit from Google Drive
rather than the git repo.) Open each of the ten JSON files in a text editor and use
find-and-replace with exactly these 17 values. The table is complete — there is nothing
else to change.

| Find this exact string | Replace with | Times it appears |
|---|---|---|
| `1ytFhXwRpANDR5HB1NnKFcmeQspVZ-Ves3h03dsFq4xU` | your **Brand Registry Id** value | 15 |
| `1_FdrtJsPsi8bi2K55P1vUn-Y_bzb5cQGwIkrzdzJ3Fs` | your **Raw Template Id** value | 22 |
| `1ENZCyFBgTNiPuE7nRz5ofic5pao_zjdhwiFLIEyo5LE` | your **Report Template Id** value | 10 |
| `1LT44dvW6b3iuhvUDA9k_zUuRlz4KUXTqxDXinq4dP9s` | your **Kit Template Id** value | 2 |
| `SBl4DBB9PIqzy5w0` | your **Cred Google Sheets Id** value | 54 |
| `Ai Saher Google Sheets` | your **Cred Google Sheets Name** value | 54 |
| `5KJlnp3mTAKGBAdb` | your **Cred Google Drive Id** value | 6 |
| `Ai Saher Google Drive` | your **Cred Google Drive Name** value | 6 |
| `cEBcWP6Pk9IcmcvL` | your **Cred Smtp Id** value | 11 |
| `Report Email SMTP` | your **Cred Smtp Name** value | 11 |
| `zzQuQyhvHs6xuSu1` | your **Cred Gmail Id** value | 11 |
| `n8n Gmail TikTok Reports` | your **Cred Gmail Name** value | 11 |
| `qQUVSfCeWtFUWkkM` | your **Cred Meta Id** value | 3 |
| `Meta-Access Tokens` | your **Cred Meta Name** value | 3 |
| `sahersalama97@gmail.com` | your **Owner Email** value | 31 |
| `saherahmed773@gmail.com` | your **Owner Email** value | 1 |
| `thebreadbutteragency@gmail.com` | your **Owner Email** value | 3 |

Replace **both** halves of each credential pair: the ID and the display name, or n8n will
show the original author's credential name next to your own credential.

Two strings you should **not** touch:

- `PASTE_YOUR_EMAIL@example.com` — a safety catch, not a mistake. WF4 refuses to share a
  client sheet with it, so nothing goes to the wrong address. Leave it until Step 9.
- The 64-character `meta.instanceId` values — n8n rewrites those on import.

Afterwards confirm the node counts, because a bad replace can quietly break the JSON:

```
00 = 31   01 = 12   02 = 13   03 = 16   04 = 16
05 = 28   05b = 3   06 = 24   07 = 13   08 = 17
```

---

## Step 6 — Import the workflows, in order

In n8n: **Workflows → Import from File**. Import all ten from `n8n/workflows_READY/`.
The filenames are already numbered in the order that makes sense.

| # | File | What it does |
|---|---|---|
| 00 | `ONE-OFF_Template_Prep` | Builds the raw-tab headers in your masters. **Run once, then archive** |
| 01 | `WF0_Brand_Auto_Discovery` | Finds your Meta ad accounts and adds new ones to the registry |
| 02 | `WF1u_Meta_Account_Level_Sync` | Pulls Meta account numbers daily |
| 03 | `WF1bu_Meta_Ad_Level_Sync` | Pulls Meta ad-level numbers daily |
| 04 | `WF_Provision_Brand_Sheets` | Makes a Raw sheet and Report sheet per client |
| 05 | `WF2e_TikTok_Report_Import` | Reads the TikTok report from your email |
| 05b | `PATCH_for_WF2e_TikTok_Ads` | Three nodes that fix a duplication bug in 05 — see Step 7 |
| 06 | `WF3_Ads_Reports` | Fills this month's report and emails it |
| 07 | `WF4_Provision_Client_Reporting_Kit` | Makes a dashboard per client |
| 08 | `WF5_Kit_Nightly_Refresh` | Fills every dashboard from the raw data |

**Leave every workflow switched OFF for now.** You turn them on in Step 10.

✔ **Check:** ten workflows imported, all inactive, no red "missing credential" badges.

---

## Step 7 — Install the TikTok patch

Skip this if you don't import TikTok by email.

Workflow 05 writes `Daily_Raw_TikTok_Ads` using n8n's Google Sheets node set to
`appendOrUpdate`. That node lets Google interpret every value, which causes two problems:
dates stop matching (so rows get appended instead of updated, forever), and 16-digit ad IDs
get stored as numbers and lose their last digit.

Workflow 05b is the fix — the same pattern the Meta workflow already uses successfully.

1. Open `05b_PATCH_for_WF2e_TikTok_Ads` and copy its three nodes.
2. Paste them into workflow 05.
3. Delete the node called `Upsert Daily_Raw_TikTok_Ads`.
4. Connect: `Explode ad rows` → `Read existing TikTok ad rows` → `Plan TikTok ad row writes`
   → `Write TikTok ad rows` → wherever the deleted node went.

✔ **Check:** workflow 05 no longer contains a node called `Upsert Daily_Raw_TikTok_Ads`,
and the three new nodes are in the chain.

Full explanation and evidence: `n8n/WF2e_FIX_TikTok_Raw_Integrity.md`.

---

## Step 8 — Run everything once by hand

Still nothing scheduled. Click each workflow and press **Execute Workflow**, in this order:

| Order | Workflow | What you should see |
|---|---|---|
| 1 | `00 ONE-OFF Template Prep` | Headers appear in the four raw tabs. **Then archive it** |
| 2 | `01 WF0 Brand Discovery` | Your ad accounts appear in the registry |
| 3 | `04 WF_Provision` | A Raw sheet and a Report sheet appear in `Clients/` |
| 4 | `02 WF1u Meta Account` | Rows appear in `Daily_Raw_Meta` |
| 5 | `03 WF1bu Meta Ad Level` | Rows appear in `Daily_Raw_Meta_Ads` |
| 6 | `05 WF2e TikTok` | Rows appear in the two TikTok tabs (needs a report email to read) |
| 7 | `06 WF3 Reports` | The report sheet fills and you get an email |
| 8 | `07 WF4 Kit Provision` | A dashboard appears and its ID lands in registry column J |
| 9 | `08 WF5 Kit Refresh` | The dashboard fills |

**The last one is the moment it works.** Open the dashboard WF4 just made and check:

- [ ] `_Control` cells `B2`–`B8` are filled — dates, brand name, today's refresh date,
      and a row count above zero
- [ ] `Fundamentals` and `Ad Data` have rows
- [ ] `Meta Dashboard` shows only Meta numbers
- [ ] `TikTok Dashboard` shows only TikTok numbers
- [ ] Neither platform tab shows the same total as the other
- [ ] `Ad Performance` lists ads, ranked by spend

Then two settings inside the dashboard:

- [ ] `KPI Calc!J5`, `J6`, `J7` — your client's product cost %, other variable cost %, and
      shipping per order. Until these are real, `KPI Calc!I4` shows **red**, which means
      breakeven ROAS is a guess. Ask the client for the real numbers.
- [ ] `Benchmarks` rows 7–21 — replace the placeholder thresholds with your client's last
      90 days, **separately for each platform**. Then type `TUNED` into `Benchmarks!B28`.

✔ **Check:** every box above ticked.

---

## Step 9 — Turn off test mode

Workflow 06 (`WF3_Ads_Reports`) ships with a line inside one of its Code nodes:

```js
const TEST_MODE = true;
```

**While that is true, every report goes to your address and no client receives one.**
Nothing errors, so it is easy to miss and easy to leave.

Keep it `true` while you are testing. Before you go live, open that Code node and change it:

```js
const TEST_MODE = false;
```

Then each client's report goes to the address in registry column E (`Report_Email`).

Also check registry column E. It may still say `PASTE_YOUR_EMAIL@example.com`. WF4
**deliberately skips sharing** a dashboard while that placeholder is there — that's a
safety feature, not a bug, but it looks like one.

✔ **Check:** `TEST_MODE = false`, and every active client has a real address in column E.

---

## Step 10 — Turn on the schedules

Now switch each workflow to **Active**. The times are already set:

| Time | Workflow |
|---|---|
| 05:00 daily | 01 Brand Discovery |
| 06:00 daily | 02 Meta Account |
| 06:15 daily | 03 Meta Ad Level |
| 10:00 daily | 04 Provision Sheets |
| **10:30 daily** | **07 WF4 Kit Provision** |
| 12:00 daily | 05 TikTok Import |
| 13:00 daily | 06 WF3 Reports — month-to-date |
| **07:00 Mondays** | **06 WF3 Reports — last full week** |
| **14:00 on the 1st** | **06 WF3 Reports — previous full month** |
| **14:00 daily** | **08 WF5 Kit Refresh** |

Workflow 06 has **three** schedule triggers, not one: `Daily Trigger` (13:00, month to
date), `Weekly Trigger` (Mondays 07:00, last full week) and `Monthly Trigger` (14:00 on the
first, previous full month). All three feed the same report builder with a different period.
If you only want the monthly report, switch the other two triggers off rather than deleting
them.

Only two ordering rules matter:

- WF4 must run **after** the sheets are provisioned
- WF5 must run **after every data-collection workflow**

The clock times themselves don't matter. If your data lands at different times, move WF4
and WF5 to keep those two rules.

Archive workflow `00` — it has done its job.

✔ **Check:** the next morning, `_Control!B7` in every dashboard shows today's date.

---

## Adding a client later

You don't do anything. That's the point.

1. Give them access to your Meta ad account, or get their TikTok advertiser ID.
2. At 05:00 WF0 finds the account and adds a row to the registry.
3. At 10:00 WF4 makes their Raw sheet and Report sheet.
4. At 10:30 WF4 (kit) makes their dashboard and records its ID in column J.
5. At 14:00 WF5 fills it.
6. You add their email to registry column E, and their three cost numbers to
   `KPI Calc!J5:J7` in their dashboard.

Step 6 is the only manual part, and it's about two minutes.

If you want to add a client by hand instead of waiting: put their `Brand_Name`,
`Platform`, `Meta_Ad_Account_ID` or `TikTok_Advertiser_ID`, `Report_Email`, and set
`Status` to `active` in the registry. Then run WF4 and WF5 by hand.

---

## Your routine once it's running

**Every morning — 30 seconds.** Open a dashboard. Check `_Control!B7` says today. Glance at
the **Health Check** tab. If a row flipped to `CHECK`, look at it before your client does.

**Every Monday — 15 minutes.** Read `Meta Dashboard` and `TikTok Dashboard` **separately**.
They are separate on purpose: two platforms almost never fail for the same reason, and a
blended number tells you to cut both when usually only one needs it.

**Every month — about an hour.**
1. Confirm the three cost numbers in `KPI Calc!J5:J7` are still right
2. Read Health Check rows 17–29
3. Fill the client report and run Prompt 1 from `05_AI_Prompts…` for the narrative
4. Export the PDF and send it with the email Prompt 9 writes
5. Run Prompt 11 (the self-audit) on your own account

**One rule worth memorising:** quote TikTok totals from `Fundamentals`, never from
`Ad Performance`. TikTok's ad-level export can under-report spend against its own
account-level total. Ad-level data is fine for ranking ads against each other — not for
platform totals.

---

## When something breaks

| You see | It means | Do this |
|---|---|---|
| Registry column J stays empty | `Kit_Sheet_ID` header missing or misspelt | Step 2a |
| Dashboards made but not shared | `Report_Email` still says `PASTE_YOUR_EMAIL` | Step 9 — by design |
| A client gets skipped silently | `Status` isn't `active` | Registry column H |
| Dashboard empty, `Rows_Synced` = 0 | Wrong `Raw_Sheet_ID` for that client | Registry column F |
| Every number is zero | Dates stored as **text**; `SUMIFS` can't match them | Wrap criteria in `TEXT(range,"yyyy-mm-dd")` |
| No client ever receives a report | `TEST_MODE` still true in WF3 | Step 9 |
| `#REF!` on the Start Here tab | You pasted into a cell that holds example text | Paste into `Fundamentals!A2` instead |
| Landing Page Views blank | Correct — TikTok has none, Meta only at ad level | Start Here has a snippet |
| Health Check rows 23/24 say CHECK | Real gap between ad-level and account-level | Expected. Quote from `Fundamentals` |
| Duplicate rows in `Daily_Raw_TikTok_Ads` | The patch isn't installed | Step 7 |
| `KPI Calc!I4` is red | Cost numbers are guesses | Step 8 |
| Benchmarks row 29 always CHECK | Tuning flag still `PLACEHOLDER` | Type `TUNED` in `B28` |
| Funnel bars look empty | Normal for 1–2% steps — bars are scaled to each step's target | Not a bug |

---

## You're finished when

- [ ] Ten workflows imported, `00` archived, the other nine active
- [ ] Every client has a Raw sheet, a Report sheet and a dashboard
- [ ] Registry column J has an ID for every active client
- [ ] `_Control!B7` shows today on every dashboard
- [ ] Meta Dashboard and TikTok Dashboard each show only their own platform
- [ ] `KPI Calc!I4` is **not** red
- [ ] `Benchmarks!B28` says `TUNED`
- [ ] `TEST_MODE = false` in WF3
- [ ] One full scheduled night has run without you touching anything

---

## Where everything is

| | |
|---|---|
| **This guide** | `START_HERE.md` |
| The five templates | `01`…`05` in the kit folder |
| All ten workflows | `n8n/workflows/` — numbered in import order |
| Your personalised copies | `n8n/workflows_READY/` — made in Step 5 |
| The script that makes them | `_build/personalise_workflows.py` |
| Full kit documentation | `README.md` |
| Automation detail | `n8n/AUTOMATION_GUIDE.md` |
| The TikTok bug and its fix | `n8n/WF2e_FIX_TikTok_Raw_Integrity.md` |
| Arabic version of this system | `README_AR.md` and `05_AI_Prompts_AR.md` |
| Troubleshooting in more depth | `SETUP_GUIDE.md` and `FAQ.md` |
