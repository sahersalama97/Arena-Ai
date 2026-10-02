# Arena-Ai — TikTok scheduled-report import

This repository contains the n8n workflow exports for the automated ads reporting system. The new workflow requested for TikTok scheduled reports is:

**`Automated Ads Reporting System_files/WF2e TikTok Scheduled Report Email Import (Raw + Reports).json`**

It is an email-based alternative to the existing TikTok API workflow (`WF2u TikTok Daily Sync (All Brands).json`). It:

1. Polls Gmail every 10 minutes and finds unread messages from any sender with CSV/XLS/XLSX attachments.
2. Downloads and parses each report attachment.
3. Matches each report to the active row in the Brand Registry using the TikTok advertiser ID or brand name. For a one-brand registry, it has a safe single-brand fallback.
4. Normalizes TikTok labels and metrics into the existing raw-sheet schema.
5. Upserts account rows into `Daily_Raw_TikTok` using `Date` and ad rows into `Daily_Raw_TikTok_Ads` using `Date + Ad_ID`.
6. Reads the updated raw tabs and refreshes the TikTok monthly report tabs: `TikTok Overview`, `TikTok Ad Performance`, `TikTok Creative Rollup`, and `TikTok Weekly`.
7. Marks the source Gmail message as read only after the import/report path completes. Mapping failures are sent to the configured alert address instead.

## n8n setup

1. Import the `WF2e ...json` file into n8n.
2. Select a Gmail OAuth2 credential on **Find unread TikTok report emails** and **Mark imported emails as read**. The exported credential is intentionally a placeholder: `REPLACE_WITH_GMAIL_CREDENTIAL_ID`.
3. Select/configure SMTP on **Alert on unmatched TikTok report**, or remove that optional node.
4. Confirm the Google Sheets credential and the Brand Registry ID. The export uses the same registry as the other workflows:
   - Spreadsheet: `1ytFhXwRpANDR5HB1NnKFcmeQspVZ-Ves3h03dsFq4xU`
   - Tab: `Sheet1`
5. Make sure the registry has active TikTok rows with at least:
   - `Brand_Name`
   - `Platform` = `TikTok` (or blank)
   - `TikTok_Advertiser_ID` when the source export contains it
   - `Raw_Sheet_ID`
   - `Current_Month_Report_Sheet_ID`
6. Optional: add `Weekly_Report_Sheet_ID` to the registry. If it is blank or absent, `TikTok Weekly` is written to `Current_Month_Report_Sheet_ID` as a tab in the monthly report workbook.
7. Confirm the raw template tabs and headers. The workflow expects:

### `Daily_Raw_TikTok`

`Date`, `Spend`, `Impressions`, `Reach`, `CPM`, `Clicks`, `CTR_Pct`, `Frequency`, `Profile_Visits`, `Follows`, `Adds_to_Cart`, `Initiate_Checkout`, `Purchases`, `Purchases_Value`, `ROAS`, `AOV`, `Purchase_CVR_Pct`, `Pulled_At`

### `Daily_Raw_TikTok_Ads`

`Date`, `Ad_ID`, `Ad_Name`, `Campaign_Name`, `AdGroup_Name`, `Creative_Key`, `Spend`, `Impressions`, `Reach`, `CPM`, `Clicks`, `CTR_Pct`, `Profile_Visits`, `Follows`, `Adds_to_Cart`, `Initiate_Checkout`, `Purchases`, `Purchases_Value`, `ROAS`, `AOV`, `Purchase_CVR_Pct`, `Pulled_At`

The existing one-off template workflow creates these tabs and writes the headers. Run it once if a raw template copy does not have them.

## Matching a TikTok export

The **Normalize TikTok rows to raw-sheet headers** Code node is the mapping layer. It already accepts common TikTok labels such as `Stat Time Day`, `Spend`, `Impressions`, `Reach`, `Clicks (All)`, `Complete Payment`, `Complete Payment Value`, `Purchase ROAS`, `Ad ID`, `Ad Name`, `Campaign Name`, and `Adgroup Name`. Add an alias in that node if TikTok uses a different label in the account.

The source must be an attachment. The Gmail search is intentionally sender-agnostic, but the attachment still needs to contain TikTok-style report columns so the normalizer can map it. If a report arrives as a Google Sheets link rather than CSV/XLSX, change the Gmail branch to extract the link and add a Google Drive/Sheets download branch; the current workflow deliberately does not scrape arbitrary links from email bodies.

## Report timing and ownership

The importer refreshes the current month's TikTok tabs after every successful email import. `TikTok Weekly` contains Monday–Sunday rollups for the current month. The existing `WF3u Report Generator + Email (All Brands).json` remains the owner of the full Meta + TikTok report cycle and the `Combined` tab; keep its weekly/monthly triggers enabled if those outputs and report emails are required.

For a first run, use **Manual Test** with one known unread TikTok report email, inspect the normalized rows, and only then activate the 10-minute poll. The workflow is inactive in the export.
