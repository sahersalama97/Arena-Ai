// Ported from WF1bu 'Plan row writes', adapted for Daily_Raw_TikTok_Ads.
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

const rows = $('Explode ad rows').all().map(i => i.json).filter(r => r && (r.Date || r.Ad_ID));
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
