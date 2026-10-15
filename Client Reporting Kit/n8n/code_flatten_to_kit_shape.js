// Turns one brand's four raw tabs into the two shapes the Client Reporting Kit
// reads, and decides which two periods to compare.
//
// DATES GO OUT AS SHEETS SERIAL NUMBERS, NOT ISO STRINGS. The write uses
// valueInputOption RAW, which preserves JSON types: a number lands in the
// pre-formatted date column as a real date. A string would land as TEXT and
// silently zero every date-bounded SUMIFS in the kit. That is exactly the bug
// Daily_Raw_Meta_Ads already has, because it is written with RAW too.
//
// Columns are matched BY HEADER NAME, not by position, so the kit keeps working
// if a raw template ever gains or reorders a column. Positional mapping breaks
// silently instead -- it fills the wrong metric and nothing looks wrong.

const WINDOW_DAYS = 7;          // report the last N complete days vs the N before
const EPOCH = Date.UTC(1899, 11, 30);
const DAY = 86400000;

function num(v) {
  if (v === null || v === undefined || v === '') return 0;
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

// Accepts a Sheets serial, an ISO string, or anything Date can parse.
// Returns a serial number, or '' when the value is not a usable date.
function serial(v) {
  if (v === null || v === undefined || v === '') return '';
  if (typeof v === 'number') return (v > 20000 && v < 80000) ? v : '';
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(v).trim());
  if (m) return Math.round((Date.UTC(+m[1], +m[2] - 1, +m[3]) - EPOCH) / DAY);
  const d = new Date(String(v));
  if (isNaN(d.getTime())) return '';
  return Math.round((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - EPOCH) / DAY);
}

function isoOf(day) {
  return new Date(EPOCH + Math.round(day) * DAY).toISOString().slice(0, 10);
}

function table(valueRange) {
  const rows = (valueRange && valueRange.values) || [];
  const head = (rows[0] || []).map(h => String(h === null || h === undefined ? '' : h).trim());
  const idx = {};
  head.forEach((h, k) => { if (h && !(h in idx)) idx[h] = k; });
  return {
    header: head,
    rows: rows.slice(1).filter(r => r && r.length),
    // first name in `names` that this tab actually has
    pick(r, names) {
      for (const n of names) {
        if (n in idx) { const v = r[idx[n]]; return v === undefined ? '' : v; }
      }
      return '';
    }
  };
}

const valueRanges = ($json && $json.valueRanges) || [];
const brand = $('Loop brands').item.json;

// batchGet OMITS ranges that came back empty, so match on the quoted sheet name
// rather than on position. 'Daily_Raw_Meta' is a prefix of 'Daily_Raw_Meta_Ads',
// hence the exact "'name'!" test.
function findTab(name) {
  const needle = "'" + name + "'!";
  return table(valueRanges.find(v => v && typeof v.range === 'string' && v.range.indexOf(needle) === 0));
}

const meta = findTab('Daily_Raw_Meta');
const tt = findTab('Daily_Raw_TikTok');
const metaAds = findTab('Daily_Raw_Meta_Ads');
const ttAds = findTab('Daily_Raw_TikTok_Ads');

const present = [];
if (!meta.header.length) present.push('Daily_Raw_Meta');
if (!tt.header.length) present.push('Daily_Raw_TikTok');
if (!metaAds.header.length) present.push('Daily_Raw_Meta_Ads');
if (!ttAds.header.length) present.push('Daily_Raw_TikTok_Ads');
if (present.length === 4) {
  throw new Error('None of the four raw tabs came back for ' + brand.Brand_Name +
                  '. Is Raw_Sheet_ID correct, and is the sheet shared with the n8n Google account?');
}

// ---------------------------------------------------------------- FUNDAMENTALS
// Meta reports landing page views only at AD level, never account level, and
// TikTok does not report them at all. So sum the ad-level tab up by date --
// without this the Meta click-to-landing-page rate reads 0.0% and looks broken.
const lpvByDate = {};
metaAds.rows.forEach(r => {
  const d = serial(metaAds.pick(r, ['Date']));
  if (d === '') return;
  lpvByDate[d] = (lpvByDate[d] || 0) + num(metaAds.pick(r, ['LPV']));
});

function fundRow(t, r, platform, lpv) {
  return [
    serial(t.pick(r, ['Date'])),
    platform,
    num(t.pick(r, ['Spend'])),
    num(t.pick(r, ['Impressions'])),
    num(t.pick(r, ['Reach'])),
    num(t.pick(r, ['Clicks'])),
    lpv,
    num(t.pick(r, ['Adds_to_Cart', 'Add to Cart'])),
    num(t.pick(r, ['Initiate_Checkout', 'Initiate Checkout'])),
    num(t.pick(r, ['Purchases'])),
    num(t.pick(r, ['Purchases_Value', 'Purchases Value']))
  ];
}

const fundRows = [];
meta.rows.forEach(r => {
  const d = serial(meta.pick(r, ['Date']));
  if (d === '') return;
  fundRows.push(fundRow(meta, r, 'Meta', lpvByDate[d] || ''));
});
tt.rows.forEach(r => {
  const d = serial(tt.pick(r, ['Date']));
  if (d === '') return;
  fundRows.push(fundRow(tt, r, 'TikTok', ''));
});

// -------------------------------------------------------------------- AD DATA
function adRow(t, r, platform) {
  const d = serial(t.pick(r, ['Date']));
  const name = String(t.pick(r, ['Ad_Name', 'Ad Name']) || '').trim();
  if (d === '' || !name) return null;          // no name = nothing to rank on
  return [
    d, platform, name,
    String(t.pick(r, ['Campaign_Name', 'Campaign Name']) || ''),
    String(t.pick(r, ['AdSet_Name', 'AdGroup_Name', 'Ad Set', 'Ad Group']) || ''),
    String(t.pick(r, ['Creative_Key', 'Creative Key']) || ''),
    num(t.pick(r, ['Spend'])),
    num(t.pick(r, ['Impressions'])),
    num(t.pick(r, ['Clicks'])),
    num(t.pick(r, ['Purchases'])),
    num(t.pick(r, ['Purchases_Value', 'Purchases Value']))
  ];
}

// De-duplicate on (Date, Ad_ID) before emitting, keeping the most recently
// PULLED version. The Meta ad-level sync already upserts on Date|Ad_ID upstream;
// the TikTok CSV import appends instead, so one ad-day can appear twice -- once
// per sync run -- and quietly double its spend and revenue. The two copies are
// not identical: TikTok restates reach and conversions as attribution matures,
// so which one you keep changes the numbers. Newest Pulled_At wins.
// NOTE: in the raw sheet the newest row is often FIRST, so "last row wins"
// would keep the stale copy. Rank on Pulled_At explicitly.
function pulledRank(v) {
  if (v === null || v === undefined || v === '') return 0;
  const t = Date.parse(String(v));
  if (!isNaN(t)) return t;
  const n = Number(v);
  return Number.isFinite(n) ? n * DAY : 0;          // a Sheets serial
}

const adRows = [];
let duplicateAdRowsRemoved = 0;
function collect(t, platform) {
  const byKey = new Map();
  const rankByKey = new Map();
  t.rows.forEach(r => {
    const d = serial(t.pick(r, ['Date']));
    const x = adRow(t, r, platform);
    if (d === '' || !x) return;
    const adId = String(t.pick(r, ['Ad_ID', 'Ad ID', 'ad_id']) || '').trim();
    const key = d + '|' + (adId || (x[2] + '|' + x[3] + '|' + x[4]));
    const rank = pulledRank(t.pick(r, ['Pulled_At', 'Pulled At']));
    if (byKey.has(key)) {
      duplicateAdRowsRemoved++;
      if (rank < rankByKey.get(key)) return;        // older pull: ignore it
    }
    byKey.set(key, x);
    rankByKey.set(key, rank);
  });
  byKey.forEach(x => adRows.push(x));
}
collect(metaAds, 'Meta');
collect(ttAds, 'TikTok');

// Sort so the sheet reads chronologically. The formulas do not care about order,
// but a human scanning Fundamentals does.
const byThenPlat = (a, b) => (a[0] - b[0]) || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0);
fundRows.sort(byThenPlat);
adRows.sort(byThenPlat);

// ------------------------------------------------------- WHICH PERIOD TO REPORT
// Drop a trailing day only when it is obviously mid-sync: impressions recorded
// but no reach. Then report the last WINDOW_DAYS complete days against the
// WINDOW_DAYS before them. Comparing against a half-written day is how a
// dashboard ends up telling the client the wrong story.
const byDate = {};
fundRows.forEach(r => { (byDate[r[0]] = byDate[r[0]] || []).push(r); });
const days = Object.keys(byDate).map(Number).sort((a, b) => a - b);
const droppedPartial = [];
const isPartial = d => byDate[d].some(r => num(r[3]) > 0 && num(r[4]) === 0);
while (days.length && isPartial(days[days.length - 1])) droppedPartial.push(isoOf(days.pop()));

let cur, cmp;
if (days.length >= 2 * WINDOW_DAYS) {
  cur = days.slice(-WINDOW_DAYS);
  cmp = days.slice(-2 * WINDOW_DAYS, -WINDOW_DAYS);
} else if (days.length >= 2) {
  // Not enough history yet (new client). Split what exists rather than failing.
  const half = Math.floor(days.length / 2);
  cur = days.slice(half);
  cmp = days.slice(0, half);
} else {
  cur = days.slice();
  cmp = [];
}

const span = a => a.length ? isoOf(a[0]) + ' to ' + isoOf(a[a.length - 1]) : 'none';

// ------------------------------------------------------------------- _CONTROL
// Written as one 7x2 block, keys included, so the tab self-heals if a human ever
// reorders or retypes it. Row order must stay as the template ships it.
const control = [
  ['Current_Start', cur.length ? cur[0] : ''],
  ['Current_End', cur.length ? cur[cur.length - 1] : ''],
  ['Compare_Start', cmp.length ? cmp[0] : ''],
  ['Compare_End', cmp.length ? cmp[cmp.length - 1] : ''],
  ['Brand_Name', brand.Brand_Name || ''],
  ['Last_Refresh', (Date.now() - EPOCH) / DAY],
  ['Rows_Synced', adRows.length]
];

const data = [];
if (fundRows.length) data.push({ range: "'Fundamentals'!A2:K" + (1 + fundRows.length), values: fundRows });
if (adRows.length) data.push({ range: "'Ad Data'!A2:K" + (1 + adRows.length), values: adRows });
data.push({ range: "'_Control'!A2:B8", values: control });

return [{
  json: {
    brand: brand.Brand_Name || '',
    kitId: brand.Kit_Sheet_ID,
    data: data,
    clearRanges: ["'Fundamentals'!A2:K6000", "'Ad Data'!A2:K6000"],
    fundRows: fundRows.length,
    adRows: adRows.length,
    duplicateAdRowsRemoved: duplicateAdRowsRemoved,
    daysKept: days.length,
    missingTabs: present,
    droppedPartialDays: droppedPartial,
    currentPeriod: span(cur),
    comparePeriod: span(cmp),
    currentDays: cur.length,
    compareDays: cmp.length
  }
}];
