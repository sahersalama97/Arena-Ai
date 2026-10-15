#!/usr/bin/env python3
"""Generate the WF2e repair patch.

WF2e ("TikTok Scheduled Report Email Import (Raw Only) FIXED") writes
Daily_Raw_TikTok_Ads with the n8n Google Sheets node set to `appendOrUpdate` +
`autoMapInputData`, matching on ['Date','Ad_ID'].  Two things go wrong with that
combination, and both are visible in the live GOFRESH sheet:

  1. Matching fails.  The Sheets node lets Google interpret the values it writes,
     so Date lands as a real datetime.  On the next run the incoming Date is the
     ISO string '2026-10-01' while the sheet reads back a datetime -- the keys
     never compare equal, so every row is appended instead of updated.
  2. Ad_ID gets coerced to a number.  A 16-digit TikTok ad ID written as a number
     is rounded to Google Sheets' 15-significant-digit limit, so the last digit is
     destroyed.  Those rows can then never be matched again, and the true ID is
     unrecoverable.

WF1bu (Meta ad-level) does not have either problem, because it reads the existing
rows, normalises both key fields in a Code node, forces Ad_ID to a string, and
writes with `values:batchUpdate` + `valueInputOption: RAW`.  This patch ports that
exact trio to the TikTok ads tab.

Run:  python3 build_wf2e_patch.py
Out:  ../n8n/WF2e_PATCH_TikTok_Ads_Upsert.json
      ../n8n/code_plan_tiktok_ad_writes.js   (the Code node, testable under node)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "n8n"))

# Credentials as they exist in this n8n install (same ones WF1bu uses).
SHEETS_CRED = {"googleSheetsOAuth2Api": {"id": "SBl4DBB9PIqzy5w0", "name": "Ai Saher Google Sheets"}}

SHEET = "Daily_Raw_TikTok_Ads"
RANGE = "'Daily_Raw_TikTok_Ads'!A:W"          # 23 columns -> A:W
BRAND_LOOP = "Loop Brands Ads"                 # WF2e's loop node for the ads branch
ROW_SOURCE = "Explode ad rows"                 # one item per parsed TikTok ad row
REPLACES = "Upsert Daily_Raw_TikTok_Ads"       # the node this patch removes

# Header contract of the live sheet, verified against GOFRESH's raw workbook.
NEED = [
    "Date", "Ad_ID", "Ad_Name", "Campaign_Name", "AdGroup_Name", "Creative_Key",
    "Spend", "Impressions", "Reach", "CPM", "Clicks", "CTR_Pct", "Profile_Visits",
    "Follows", "Adds_to_Cart", "Initiate_Checkout", "Purchases", "Purchases_Value",
    "ROAS", "AOV", "Purchase_CVR_Pct", "Pulled_At", "Frequency",
]

# ---------------------------------------------------------------------------
# The Code node.  Kept in a separate .js file too, so it can be unit-tested
# under `node` without an n8n install.
# ---------------------------------------------------------------------------
PLAN_JS = r"""// Ported from WF1bu 'Plan row writes', adapted for Daily_Raw_TikTok_Ads.
// Reads the sheet as it actually is, normalises BOTH key fields to a canonical
// string, then emits explicit per-row ranges for values:batchUpdate.  Nothing
// here lets Google guess a type: Date is written as a serial (the column already
// holds real dates) and Ad_ID is written as text (so a 16-digit ID survives).
const SHEET = 'Daily_Raw_TikTok_Ads';
const need = ['Date','Ad_ID','Ad_Name','Campaign_Name','AdGroup_Name','Creative_Key','Spend','Impressions','Reach','CPM','Clicks','CTR_Pct','Profile_Visits','Follows','Adds_to_Cart','Initiate_Checkout','Purchases','Purchases_Value','ROAS','AOV','Purchase_CVR_Pct','Pulled_At','Frequency'];

const EPOCH = Date.UTC(1899, 11, 30);            // Google Sheets serial epoch

// Date -> 'YYYY-MM-DD'.  Accepts a serial number, an ISO string, or a datetime
// string, because the sheet currently holds real dates while the incoming CSV
// holds text.  This is the function that makes matching work.
function normDate(v) {
  if (typeof v === 'number' && v > 20000 && v < 80000) {
    return new Date(EPOCH + Math.round(v) * 86400000).toISOString().slice(0, 10);
  }
  const s = String(v == null ? '' : v).trim();
  return /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : s;
}

// 'YYYY-MM-DD' -> Sheets serial number, so the Date column keeps its existing
// real-date type instead of turning into text like Daily_Raw_Meta_Ads did.
function dateSerial(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ''));
  if (!m) return iso;                            // leave anything unexpected alone
  const t = Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return (t - EPOCH) / 86400000;
}

// Ad_ID -> plain digit string.  toFixed(0) matters: it stops a 16-digit ID from
// being emitted in exponential notation, which would never match anything.
function normId(v) {
  if (typeof v === 'number') return v.toFixed(0);
  return String(v == null ? '' : v).trim();
}

const rows = $(ROW_SOURCE_EXPR).all().map(i => i.json).filter(r => r && (r.Date || r.Ad_ID));
const resp = $input.first().json;
const values = Array.isArray(resp && resp.values) ? resp.values : [];
if (!values.length) throw new Error('Sheet returned no header row - not writing');

const header = values[0].map(h => String(h).trim());
const missing = need.filter(c => !header.includes(c));
if (missing.length) throw new Error('Header mismatch, missing: ' + missing.join(', '));
if (header.length > 30) throw new Error('Unexpected column count: ' + header.length);

const iD = header.indexOf('Date'), iA = header.indexOf('Ad_ID');

// Index what is already there.  Later duplicate wins nothing: we keep the row
// with the NEWEST Pulled_At, because a re-pull of the same ad-day is a correction.
const iP = header.indexOf('Pulled_At');
const existing = new Map();
let dupes = 0;
for (let r = 1; r < values.length; r++) {
  const row = values[r] || [];
  const d = normDate(row[iD]), a = normId(row[iA]);
  if (!d || !a) continue;                        // blank line in the sheet
  const k = d + '|' + a;
  if (existing.has(k)) {
    dupes++;
    const prev = values[existing.get(k) - 1] || [];
    if (String(row[iP] || '') > String(prev[iP] || '')) existing.set(k, r + 1);
  } else {
    existing.set(k, r + 1);
  }
}

// Collapse this run's rows on the same key too, so one run cannot create a dupe.
const byKey = new Map();
for (const row of rows) {
  const k = normDate(row.Date) + '|' + normId(row.Ad_ID);
  if (!k.startsWith('|') && k.length > 1) byKey.set(k, row);
}

let next = values.length + 1;
const last = String.fromCharCode(64 + header.length);
const data = [];
let updated = 0, appended = 0;
const textFixed = [];
for (const [k, row] of byKey) {
  let n = existing.get(k);
  if (n) { updated++; } else { n = next++; appended++; }
  const arr = header.map(h => {
    let v = row[h];
    if (v === undefined || v === null) v = '';
    if (h === 'Ad_ID') v = String(v);                        // never a number
    else if (h === 'Date') v = dateSerial(normDate(v));      // serial, stays a date
    return v;
  });
  // Report any row we are about to overwrite that currently holds a numeric
  // Ad_ID, so the one-off cleanup can be verified.
  if (n) {
    const cur = (values[n - 1] || [])[iA];
    if (typeof cur === 'number') textFixed.push(k);
  }
  data.push({ range: "'" + SHEET + "'!A" + n + ':' + last + n, values: [arr] });
}
// Never hand a malformed range to the Sheets API. A partial batchUpdate is worse
// than a failed one, so fail loudly here instead.
for (const d of data) {
  if (!/^'[^']+'!A\d+:[A-Z]+\d+$/.test(d.range)) throw new Error('Bad write range: ' + d.range);
}
return [{ json: { data, updated, appended, existing_duplicates: dupes, numeric_ids_repaired: textFixed } }];
""".replace("ROW_SOURCE_EXPR", "'" + ROW_SOURCE + "'")


def node_read():
    return {
        "parameters": {
            "url": (
                "=https://sheets.googleapis.com/v4/spreadsheets/"
                "{{ $('" + BRAND_LOOP + "').first().json.Raw_Sheet_ID }}/values/"
                "{{ encodeURIComponent(\"" + RANGE + "\") }}"
                "?majorDimension=ROWS&valueRenderOption=UNFORMATTED_VALUE"
                "&dateTimeRenderOption=SERIAL_NUMBER"
            ),
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "googleSheetsOAuth2Api",
            "options": {},
        },
        "id": "b7c1f0a4-2d51-4c66-9a3f-0e5f1c2b7a10",
        "name": "Read existing TikTok ad rows",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1360, 928],
        "retryOnFail": True,
        "maxTries": 3,
        "waitBetweenTries": 2000,
        "credentials": SHEETS_CRED,
        "onError": "continueErrorOutput",
        "notes": (
            "UNFORMATTED_VALUE + SERIAL_NUMBER means Date comes back as a serial "
            "number and Ad_ID as whatever it really is (string OR number). The Code "
            "node normalises both. If this read fails nothing is written for the "
            "brand -- error output goes to the alert node."
        ),
    }


def node_plan():
    return {
        "parameters": {"mode": "runOnceForAllItems", "jsCode": PLAN_JS},
        "id": "b7c1f0a4-2d51-4c66-9a3f-0e5f1c2b7a11",
        "name": "Plan TikTok ad row writes",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1580, 928],
        "notes": (
            "Returns one item carrying the whole batchUpdate payload plus counters "
            "(updated / appended / existing_duplicates / numeric_ids_repaired). Log "
            "those counters: existing_duplicates > 0 means the sheet still has "
            "duplicated ad-days from before this patch was installed."
        ),
    }


def node_write():
    return {
        "parameters": {
            "method": "POST",
            "url": (
                "=https://sheets.googleapis.com/v4/spreadsheets/"
                "{{ $('" + BRAND_LOOP + "').first().json.Raw_Sheet_ID }}/values:batchUpdate"
            ),
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "googleSheetsOAuth2Api",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ valueInputOption: 'RAW', data: $json.data }) }}",
            "options": {},
        },
        "id": "b7c1f0a4-2d51-4c66-9a3f-0e5f1c2b7a12",
        "name": "Write TikTok ad rows",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1800, 928],
        "retryOnFail": True,
        "maxTries": 3,
        "waitBetweenTries": 3000,
        "credentials": SHEETS_CRED,
        "onError": "continueErrorOutput",
        "notes": (
            "RAW is the whole point: Google stores exactly what we send, so the "
            "Ad_ID string is never re-parsed as a 16-digit number. Explicit row "
            "numbers make a retry safe -- the same rows are rewritten, not appended."
        ),
    }


def build():
    nodes = [node_read(), node_plan(), node_write()]
    connections = {
        "Read existing TikTok ad rows": {
            "main": [[{"node": "Plan TikTok ad row writes", "type": "main", "index": 0}]],
            "error": [[{"node": "Send a message", "type": "main", "index": 0}]],
        },
        "Plan TikTok ad row writes": {
            "main": [[{"node": "Write TikTok ad rows", "type": "main", "index": 0}]]
        },
        "Write TikTok ad rows": {
            "error": [[{"node": "Send a message", "type": "main", "index": 0}]],
        },
    }
    wf = {
        "name": "PATCH - WF2e TikTok Ads Upsert (copy these 3 nodes into WF2e)",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
        "tags": [],
        "_patch": {
            "target_workflow": "WF2e TikTok Scheduled Report Email Import (Raw Only) FIXED",
            "removes_node": REPLACES,
            "rewire": (
                ROW_SOURCE + "  ->  Read existing TikTok ad rows  ->  Plan TikTok ad row writes  "
                "->  Write TikTok ad rows  ->  (whatever " + REPLACES + " was connected to)"
            ),
            "why": "See WF2e_FIX_TikTok_Raw_Integrity.md in this folder.",
        },
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    pj = os.path.join(OUT_DIR, "WF2e_PATCH_TikTok_Ads_Upsert.json")
    with open(pj, "w", encoding="utf-8") as fh:
        json.dump(wf, fh, indent=2, ensure_ascii=False)
    pj2 = os.path.join(OUT_DIR, "code_plan_tiktok_ad_writes.js")
    with open(pj2, "w", encoding="utf-8") as fh:
        fh.write(PLAN_JS)
    return pj, pj2, wf


if __name__ == "__main__":
    a, b, wf = build()
    print("wrote", os.path.relpath(a), len(wf["nodes"]), "nodes")
    print("wrote", os.path.relpath(b), len(PLAN_JS), "chars")
