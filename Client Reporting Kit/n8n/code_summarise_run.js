// Runs once, after the loop has visited every brand. Collects the whole run into
// a single email instead of one per client, so a morning glance answers
// "did every client's dashboard refresh?" without opening twelve sheets.

function safeAll(name) {
  try {
    const a = $(name).all();
    return Array.isArray(a) ? a.map(i => i.json).filter(Boolean) : [];
  } catch (e) {
    return [];      // the node never ran (no brands qualified)
  }
}

const flats = safeAll('Flatten to kit shape');
const fetches = safeAll('Fetch raw tabs');
const writes = safeAll('Write kit data');

// Pair each brand with its write result by index. Every branch emits exactly one
// item per brand, so the positions line up.
const rows = flats.map((f, i) => {
  const w = writes[i] || {};
  const wrote = !w.error && (w.totalUpdatedCells > 0 || Array.isArray(w.responses));
  return {
    brand: f.brand || '(unknown)',
    ok: wrote,
    current: f.currentPeriod || 'none',
    compare: f.comparePeriod || 'none',
    days: f.currentDays || 0,
    fundRows: f.fundRows || 0,
    adRows: f.adRows || 0,
    dupes: f.duplicateAdRowsRemoved || 0,
    dropped: (f.droppedPartialDays || []).join(', ') || '-',
    missing: (f.missingTabs || []).join(', ') || '-',
    error: w.error ? JSON.stringify(w.error).slice(0, 300) : (wrote ? '' : 'write returned no confirmation')
  };
});

const okCount = rows.filter(r => r.ok).length;
const failed = rows.filter(r => !r.ok);
const totalDupes = rows.reduce((s, r) => s + r.dupes, 0);
const now = new Date().toISOString().slice(0, 16).replace('T', ' ');

function esc(s) {
  return String(s === null || s === undefined ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

const th = 'text-align:left;padding:6px 10px;border-bottom:2px solid #d1d5db;font-size:12px;color:#374151';
const td = 'padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:12px;color:#111827';

let body = '';
body += '<div style="font-family:Inter,Arial,sans-serif;max-width:900px">';
body += '<h2 style="font-size:18px;color:#111827;margin:0 0 4px">Client Reporting Kit — nightly refresh</h2>';
body += '<p style="font-size:13px;color:#6b7280;margin:0 0 16px">' + esc(now) + ' UTC</p>';

const banner = failed.length === 0
  ? '<div style="background:#dcfce7;color:#15803d;padding:10px 14px;border-radius:6px;font-size:14px;font-weight:600">'
    + okCount + ' of ' + rows.length + ' client dashboards refreshed. Nothing needs attention.</div>'
  : '<div style="background:#fee2e2;color:#b91c1c;padding:10px 14px;border-radius:6px;font-size:14px;font-weight:600">'
    + failed.length + ' of ' + rows.length + ' clients did NOT refresh. See the rows marked ✗ below.</div>';
body += banner;

if (rows.length) {
  body += '<table style="border-collapse:collapse;width:100%;margin-top:18px">';
  body += '<tr>'
       + '<th style="' + th + '"></th>'
       + '<th style="' + th + '">Client</th>'
       + '<th style="' + th + '">Reporting period</th>'
       + '<th style="' + th + '">Compared with</th>'
       + '<th style="' + th + '">Days</th>'
       + '<th style="' + th + '">Fund rows</th>'
       + '<th style="' + th + '">Ad rows</th>'
       + '<th style="' + th + '">Dupes dropped</th>'
       + '<th style="' + th + '">Partial day dropped</th>'
       + '</tr>';
  rows.forEach(r => {
    body += '<tr>'
         + '<td style="' + td + '">' + (r.ok ? '✓' : '✗') + '</td>'
         + '<td style="' + td + ';font-weight:600">' + esc(r.brand) + '</td>'
         + '<td style="' + td + '">' + esc(r.current) + '</td>'
         + '<td style="' + td + '">' + esc(r.compare) + '</td>'
         + '<td style="' + td + '">' + r.days + '</td>'
         + '<td style="' + td + '">' + r.fundRows + '</td>'
         + '<td style="' + td + '">' + r.adRows + '</td>'
         + '<td style="' + td + '">' + (r.dupes || '') + '</td>'
         + '<td style="' + td + '">' + esc(r.dropped) + '</td>'
         + '</tr>';
    if (!r.ok) {
      body += '<tr><td></td><td colspan="8" style="' + td + ';color:#b91c1c">' + esc(r.error) + '</td></tr>';
    }
  });
  body += '</table>';
}

// Two things a media buyer should never have to open a sheet to notice.
const notes = [];
if (totalDupes > 0) {
  notes.push('<b>' + totalDupes + ' duplicate ad rows were dropped.</b> The TikTok CSV import appends '
    + 'instead of upserting on (Date, Ad_ID), so the same ad-day arrives once per sync run. The kit keeps '
    + 'the newest pull and discards the rest, but the Raw sheet still holds both copies — which means '
    + 'anything else reading Daily_Raw_TikTok_Ads at ad level is double-counting spend and revenue.');
}
const partial = rows.filter(r => r.dropped && r.dropped !== '-');
if (partial.length) {
  notes.push('<b>' + partial.length + ' client(s) had a partial day dropped:</b> '
    + partial.map(r => esc(r.brand) + ' (' + esc(r.dropped) + ')').join(', ')
    + '. A day with impressions but no reach is mid-sync, so it was excluded rather than reported as a collapse.');
}
const missing = rows.filter(r => r.missing && r.missing !== '-');
if (missing.length) {
  notes.push('<b>Missing raw tabs:</b> '
    + missing.map(r => esc(r.brand) + ' — ' + esc(r.missing)).join('; ')
    + '. Those platforms are simply absent from the dashboard, not zero.');
}
if (notes.length) {
  body += '<div style="background:#fef3c7;border-left:4px solid #b45309;padding:12px 14px;margin-top:18px;border-radius:4px">';
  notes.forEach(n => { body += '<p style="font-size:12.5px;color:#7c2d12;margin:0 0 8px">' + n + '</p>'; });
  body += '</div>';
}

body += '<p style="font-size:12px;color:#6b7280;margin-top:18px">'
     + 'Each dashboard re-ranks its own top ads, re-grades every metric against Benchmarks, and rewrites the '
     + 'Meta, TikTok and blended commentary from these numbers. Open the Health Check tab of any dashboard '
     + 'before sending it to a client — a red row there is a data problem, not a performance problem.'
     + '</p></div>';

return [{
  json: {
    subject: failed.length === 0
      ? 'Kit refresh OK — ' + okCount + '/' + rows.length + ' dashboards updated'
      : 'Kit refresh FAILED for ' + failed.length + ' of ' + rows.length + ' dashboards',
    html: body,
    okCount: okCount,
    failedCount: failed.length,
    duplicateAdRowsRemoved: totalDupes
  }
}];
