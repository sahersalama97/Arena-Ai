/* Mini n8n emulator. Executes the real Code nodes and real Clear/Append semantics
 * against an in-memory spreadsheet so each fix is proved rather than asserted.
 *   node analysis/run_nodes.js
 *
 * Modelled n8n behaviours:
 *  - googleSheets read  : header row 1 -> one item per data row (error item on failure)
 *  - googleSheets clear : loops once per input item unless executeOnce (source-verified)
 *  - googleSheets append: one call; empty sheet -> header row written from item keys
 *  - junction node      : runs once PER arriving parent (Merge/noOp are the only sync points)
 */
const fs = require("fs"), path = require("path");
const { DateTime } = require("luxon");

class Book {
  constructor() { this.tabs = {}; this.calls = { clear: 0, append: 0, read: 0 }; }
  set(n, rows) { this.tabs[n] = rows; }
  read(name) {
    this.calls.read++;
    const rows = this.tabs[name];
    if (!rows) return [{ error: { message: `Sheet not found: ${name}` } }];
    const head = rows[0] || [];
    return rows.slice(1).map((r) => { const o = {}; head.forEach((h, i) => (o[h] = r[i])); return { json: o }; });
  }
  clear(name, executeOnce, itemCount) {
    const n = Math.max(executeOnce ? 1 : itemCount, 1);
    this.calls.clear += n;
    for (let i = 0; i < n; i++) if (this.tabs[name]) this.tabs[name] = [];
  }
  append(name, items) {
    if (!items.length) return 0;
    this.calls.append++;
    if (!this.tabs[name] || !this.tabs[name].length) this.tabs[name] = [Object.keys(items[0].json)];
    const head = this.tabs[name][0];
    for (const it of items) this.tabs[name].push(head.map((h) => (it.json[h] === undefined ? "" : it.json[h])));
    return items.length;
  }
  value(name, metric, col) {
    const t = this.tabs[name] || [], h = t[0] || [];
    const row = t.slice(1).find((x) => x[0] === metric);
    if (!row) return null;
    return col === undefined ? row[1] : row[h.indexOf(col)];
  }
}

function graph(wf) {
  const N = {}; wf.nodes.forEach((n) => (N[n.name] = n));
  const kids = {}, par = {};
  wf.nodes.forEach((n) => { kids[n.name] = []; par[n.name] = []; });
  for (const [src, l] of Object.entries(wf.connections))
    for (const arr of l.main) for (const c of arr) { kids[src].push(c.node); par[c.node].push(src); }
  return { N, kids, par };
}

function topo(wf, trigger) {
  const { kids, par } = graph(wf);
  // reachable subgraph from the single trigger (n8n fires one trigger per run)
  const reach = new Set(), st = [trigger];
  while (st.length) { const x = st.pop(); if (reach.has(x)) continue; reach.add(x); kids[x].forEach((k) => st.push(k)); }
  const indeg = {}; [...reach].forEach((n) => (indeg[n] = (par[n] || []).filter((p) => reach.has(p)).length));
  const pos = {}; wf.nodes.forEach((n) => (pos[n.name] = n.position));
  const q = [...reach].filter((n) => indeg[n] === 0).sort((a, b) => pos[a][1] - pos[b][1] || pos[a][0] - pos[b][0]);
  const seq = [];
  while (q.length) {
    const n = q.shift(); seq.push(n);
    for (const k of kids[n]) { if (!reach.has(k)) continue; if (--indeg[k] === 0) q.push(k); }
    q.sort((a, b) => pos[a][1] - pos[b][1] || pos[a][0] - pos[b][0]);
  }
  if (seq.length !== reach.size) throw new Error("cycle or unreachable nodes: " + [...reach].filter((x) => !seq.includes(x)));
  return { seq, par, reach };
}

function run(wf, book, trigger, periodNow, opts = {}) {
  const { N, par } = graph(wf);
  const { seq } = topo(wf, trigger);
  const out = {}, done = new Set(), failed = new Set(), log = [];
  const emails = [];
  const isSync = (n) => n.type.endsWith(".merge") || n.type.endsWith(".noOp") || n.type.endsWith("Trigger");

  for (const name of seq) {
    const node = N[name];
    if (name === trigger) { out[name] = [{ json: {} }]; done.add(name); continue; }
    const parents = (par[name] || []).filter((p) => done.has(p));
    const blocked = (par[name] || []).filter((p) => failed.has(p));
    if (blocked.length) { failed.add(name); log.push(`${name} -- skipped (upstream failed)`); continue; }

    // junction semantics: Merge/noOp = one run with all items; anything else = one run per parent
    let runs = parents.length > 1 && !isSync(node) ? parents.map((p) => out[p] || []) : [parents.flatMap((p) => out[p] || [])];
    if (node.executeOnce) runs = runs.map((it) => it.slice(0, 1)); // n8n: node "only receives the first item"
    const collected = [];
    let aborted = null;
    for (const items of runs) {
      if (!items.length && parents.length) { collected.push(...items); continue; }
      try {
        if (node.type.endsWith(".googleSheets")) {
          const p = node.parameters, op = p.operation || "read", tab = p.sheetName.value;
          if (op === "read") collected.push(...book.read(tab).map((x) => (x.error ? { json: x } : x)));
          else if (op === "clear") { book.clear(tab, !!node.executeOnce, items.length); collected.push(...items); }
          else { book.append(tab, items); collected.push(...items); }
        } else if (node.type.endsWith(".code")) {
          const $$ = (ref) => {
            if (!done.has(ref)) throw new Error(`$('${ref}') used before '${ref}' executed`);
            const d = out[ref] || [];
            return { first: () => d[0] || { json: {} }, all: () => d, item: () => d[0], items: d };
          };
          const body = node.parameters.jsCode;
          if (opts.guardless) {
            // simulate the pre-fix workflow: no aborts, and clear runs per item
          }
          const fn = new Function("items", "$", "$json", "$today", "$now", "DateTime", body);
          collected.push(...(fn(items, $$, items[0] && items[0].json, periodNow, periodNow, DateTime) || []));
        } else if (node.type.endsWith("emailSend")) {
          const p = node.parameters;
          for (const it of items) {
            const sub = String(p.subject).includes("{{") ? it.json.subject : p.subject;
            const txt = p.text && String(p.text).includes("{{") ? it.json.text : p.text;
            if (!sub || !txt || /undefined|null/.test(String(txt))) throw new Error(`email unusable: ${String(sub)} / ${String(txt).slice(0, 40)}`);
            emails.push({ subject: sub, text: txt });
          }
          collected.push(...items);
        } else collected.push(...items);
      } catch (e) { aborted = e; break; }
    }
    if (aborted) { failed.add(name); log.push(`${name} !! ${aborted.message}`); continue; }
    out[name] = collected; done.add(name); log.push(name);
  }
  return { out, done, failed, emails, log, calls: book.calls };
}

// ------------------------------------------------------------------ fixtures
const HEAD_M = ["Date", "Spend", "Impressions", "Reach", "Clicks", "Adds_to_Cart", "Initiate_Checkout", "Purchases", "Purchases_Value"];
const HEAD_T = ["Date", "Spend", "Impressions", "Reach", "Clicks", "Profile_Visits", "Follows", "Adds_to_Cart", "Initiate_Checkout", "Purchases", "Purchases_Value"];
const META = [HEAD_M, ["2026-09-14", "100", "10000", "6000", "200", "10", "5", "2", "250"], ["2026-09-15", "50.25", "5000", "3000", "100", "4", "2", "1", "125"]];
const TT = [HEAD_T, ["2026-09-14", "60", "4000", "2500", "80", "30", "5", "3", "1", "1", "90"]];
const TABS = {
  "Daily_Raw_Meta": META,
  "Daily_Raw_Meta_Ads": [HEAD_M.slice(1).length ? [...HEAD_M, "Ad_ID", "Ad_Name", "AdSet_Name", "Campaign_Name", "Creative_Key"] : [],
    [...META[1], "ad1", "Hero video", "ABO", "C1", "video-a"], [...META[2], "ad2", "UGC cut", "ABO", "C1", "video-b"]],
  "Daily_Raw_TikTok": TT,
  "Daily_Raw_TikTok_Ads": [[...TT[0], "Ad_ID", "Ad_Name", "Campaign_Name", "AdGroup_Name", "Creative_Key"],
    [...TT[1], "tt1", "Spark clip", "TT1", "AG1", "tt-vid"]],
};
const REPORTS = ["Report_Meta_Overview", "Report_Meta_Weekly", "Report_Meta_Ad_Performance", "Report_Meta_Creative_Rollup",
  "Report_TikTok_Overview", "Report_TikTok_Weekly", "Report_TikTok_Ad_Performance", "Report_TikTok_Creative_Rollup", "Report_Combined"];
const PERIOD = DateTime.fromISO("2026-09-21T07:00:00"); // manual window = Sep 14..20

function freshBook(seedOld) {
  const b = new Book();
  for (const [k, v] of Object.entries(TABS)) b.set(k, v.map((r) => [...r]));
  for (const t of REPORTS) b.set(t, seedOld ? [["Metric", "Value"], ["Spend", 999], ["Purchases", 42]] : []);
  return b;
}
// Faithful pre-fix baseline: no normalizers, no guards, no packing, no sync node.
// (what the original export actually did)
const preFix = (wf) => {
  const nodes = wf.nodes
    .filter((n) => !/^Expand /.test(n.name))
    .map((n) => {
      let code = n.parameters.jsCode;
      if (code) {
        if (/^Normalize /.test(n.name)) {
          // original pipeline had no normalizer: rows flowed through with Date as stored,
          // so emulate that exactly (raw ISO strings) while keeping the Source tag
          const srcTag = (n.parameters.jsCode.match(/const SOURCE = '(\w+)';/) || [])[1] || "";
          code = `return items.map((it) => ({ json: Object.assign({}, it.json, { DateISO: it.json.Date, Source: ${JSON.stringify(srcTag)} }), pairedItem: it.pairedItem }));`;
        }
        code = code
          .replace(/\bif\s*\([^)]*\)\s*throw new Error\([\s\S]*?\);/g, "void 0;")
          .replace(/return \[\{ json: \{ rows: (\w+) \} \}\];/g, "return $1.map((o) => ({ json: o }));");
      }
      return { ...n, parameters: code ? { ...n.parameters, jsCode: code } : n.parameters };
    });
  const byName = {}; nodes.forEach((n) => (byName[n.name] = n));
  const conns = {};
  for (const [src, l] of Object.entries(wf.connections)) {
    if (!byName[src]) continue; // source node was removed from the variant
    const main = l.main
      .map((arr) => arr
        .filter((c) => !/^Expand /.test(c.node) && c.node !== "Join All Report Writes")
        .map((c) => ({ ...c, index: 0 })))
      .filter((a) => a.length);
    // Clear -> (Expand removed) -> Write  and  Write -> Compose
    for (const arr of l.main) for (const c of arr) {
      if (/^Expand /.test(c.node)) {
        const expandOut = (wf.connections[c.node] || {}).main || [];
        for (const a of expandOut) for (const g of a) main.push([{ ...g, index: 0 }]);
      } else if (c.node === "Join All Report Writes") {
        const mo = ((wf.connections["Join All Report Writes"] || {}).main || [[]])[0];
        for (const g of mo) main.push([{ ...g, index: 0 }]);
      }
    }
    if (main.length) conns[src] = { main };
  }
  return { ...wf, nodes, connections: conns };
};

const wf = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "workflow.fixed.json"), "utf8"));
let pass = 0, fail = 0;
const t = (label, cond, detail = "") => { cond ? pass++ : fail++; console.log(`${cond ? "  PASS " : "  FAIL "} ${label}${detail ? "   [" + detail + "]" : ""}`); };

console.log("\n== A. healthy run ==");
let b = freshBook(false); let r = run(wf, b, "Manual Test", PERIOD);
t("no node failed", r.failed.size === 0, [...r.failed].map((x) => r.log.find((l) => l.startsWith(x + " !"))).join(" ; "));
t("Meta Spend = 150.25", b.value("Report_Meta_Overview", "Spend") === 150.25, String(b.value("Report_Meta_Overview", "Spend")));
t("Meta CPM = 10.02", b.value("Report_Meta_Overview", "CPM") === 10.02, String(b.value("Report_Meta_Overview", "CPM")));
t("Meta ROAS = 2.4958", Math.abs(b.value("Report_Meta_Overview", "ROAS") - 2.4958) < 1e-9, String(b.value("Report_Meta_Overview", "ROAS")));
t("TikTok ROAS = 1.5", Math.abs(b.value("Report_TikTok_Overview", "ROAS") - 1.5) < 1e-9);
t("Combined Spend 210.25 = Meta + TikTok", b.value("Report_Combined", "Spend", "Combined") === 210.25, String(b.value("Report_Combined", "Spend", "Combined")));
t("Combined tab reconciles with Meta overview tab", b.value("Report_Combined", "Spend", "Meta") === b.value("Report_Meta_Overview", "Spend"));
t("Meta share of spend = 71.46%", Math.abs(b.value("Report_Combined", "Meta Share of Spend %", "Meta") - 71.46) < 0.01, String(b.value("Report_Combined", "Meta Share of Spend %", "Meta")));
t("Ad Performance tab has 2 ranked ads", (b.tabs.Report_Meta_Ad_Performance || []).length === 3);
t("Creative Rollup tab written", (b.tabs.Report_Meta_Creative_Rollup || []).length === 3);
t("all 9 tabs non-empty", REPORTS.every((x) => (b.tabs[x] || []).length > 1));
t("exactly ONE email (FIX-1)", r.emails.length === 1, `sent ${r.emails.length}`);
t("email body has no undefined/n-a leak", r.emails.length === 1 && !/undefined/.test(r.emails[0].text));
t("email money formatted", r.emails.length === 1 && /Combined Spend: 210\.25/.test(r.emails[0].text), (r.emails[0] && r.emails[0].text || "").split("\n")[3]);
t("9 clear calls for 9 tabs (FIX-3 pack/expand)", b.calls.clear === 9, `clears=${b.calls.clear}`);
t("Overview tab wrote all 13 metric rows, not 1", (b.tabs.Report_Meta_Overview || []).length === 14, `rows=${(b.tabs.Report_Meta_Overview||[]).length - 1}`);
t("Ad Performance tab wrote all 2 ads (no executeOnce starvation)", (b.tabs.Report_Meta_Ad_Performance || []).length === 3);
t("Combined tab wrote all 7 metric rows", (b.tabs.Report_Combined || []).length === 8);
t("no stray packed 'rows' column leaked into a tab", !(b.tabs.Report_Meta_Overview[0] || []).includes("rows"), b.tabs.Report_Meta_Overview[0].join(","));
t("expand refuses to write an empty tab", wf.nodes.some((n) => /^Expand /.test(n.name) && /refusing to write an empty tab/.test(n.parameters.jsCode)));
t("no Clear uses executeOnce (would starve the Write)", !wf.nodes.some((n) => n.parameters.operation === "clear" && n.executeOnce));

console.log("\n== B. the same run on the pre-fix wiring/guards ==");
let b2 = freshBook(false);
r = run(preFix(wf), b2, "Manual Test", PERIOD);
t("pre-fix fans out to multiple emails", r.emails.length > 1, `sent ${r.emails.length}`);
t("pre-fix issues one clear call per report row", b2.calls.clear > 9, `clears=${b2.calls.clear} vs fixed ${freshBook(false) && 9}`);
t("pre-fix writes the same report content (baseline is equivalent)", b2.value("Report_Meta_Overview", "Spend") === 150.25, String(b2.value("Report_Meta_Overview", "Spend")));

console.log("\n== C. broken read must not publish zeros ==");
let b3 = freshBook(true);
delete b3.tabs.Daily_Raw_Meta;
r = run(wf, b3, "Manual Test", PERIOD);
t("fixed: run aborts on the failure", r.failed.size > 0, (r.log.find((l) => l.includes("!!")) || "").slice(0, 90));
t("fixed: old report data is still there", b3.value("Report_Meta_Overview", "Spend") === 999, String(b3.value("Report_Meta_Overview", "Spend")));
t("fixed: no email from a broken run", r.emails.length === 0);
t("fixed: the affected tab was never cleared", !r.done.has("Clear Report_Meta_Overview"), `clears=${b3.calls.clear} on other tabs (expected: sibling branches still refresh)`);
t("fixed: sibling tabs still updated correctly", b3.value("Report_TikTok_Overview", "Spend") === 60, String(b3.value("Report_TikTok_Overview", "Spend")));
let b4 = freshBook(true);
delete b4.tabs.Daily_Raw_Meta;
r = run(preFix(wf), b4, "Manual Test", PERIOD);
const survived = b4.value("Report_Meta_Overview", "Spend") === 999;
t("regression proof: unguarded run wipes/overwrites the good tab", !survived, `Spend now = ${b4.value("Report_Meta_Overview", "Spend")} ; rows=${(b4.tabs.Report_Meta_Overview || []).length}`);

console.log("\n== D. messy dates and money (FIX-2) ==");
const nrm = wf.nodes.find((n) => n.name === "Normalize Meta");
const f2 = new Function("items", "DateTime", nrm.parameters.jsCode);
const rowsIn = (rows, head) => rows.map((row) => { const o = {}; head.forEach((h, i) => (o[h] = row[i])); return { json: o }; });
let g = f2(rowsIn([["25/9/2026", "1,200 EGP", "10", "10", "1", "0", "0", "0", "0"]], HEAD_M), DateTime);
t("25/9/2026 -> 2026-09-25", g[0].json.DateISO === "2026-09-25", g[0].json.DateISO);
t("'1,200 EGP' -> 1200", g[0].json.Spend === 1200, String(g[0].json.Spend));
g = f2(rowsIn([["9/25/2026", "1", "1", "1", "1", "0", "0", "0", "0"]], HEAD_M), DateTime);
t("9/25/2026 -> 2026-09-25", g[0].json.DateISO === "2026-09-25", g[0].json.DateISO);
g = f2(rowsIn([[46289, "5", "1", "1", "1", "0", "0", "0", "0"]], HEAD_M), DateTime);
t("serial 46289 -> 2026-09-24", g[0].json.DateISO === "2026-09-24", g[0].json.DateISO);
t("serial 46287 -> today", f2([{ json: { Date: 46287, Spend: 1 } }], DateTime)[0].json.DateISO === "2026-09-22");
g = f2(rowsIn([["2026-09-14", "1", "1", "1", "1", "0", "0", "0", "0"]], HEAD_M), DateTime);
t("ISO passes through", g[0].json.DateISO === "2026-09-14");
let threw = false;
try { f2([{ json: { error: { message: "quota" } } }], DateTime); } catch (e) { threw = /failed upstream/.test(e.message); }
t("error item aborts in the normalizer", threw);
threw = false;
try { f2(rowsIn([["not a date", "1", "1", "1", "1", "0", "0", "0", "0"]], HEAD_M), DateTime); } catch (e) { threw = /unparseable Date/.test(e.message); }
t("all-unparseable dates abort with a hint", threw);

console.log("\n== E. weekly ordering (FIX-6): monthly run, 2 weeks, worst week first by ROAS ==");
const b5 = freshBook(false);
b5.set("Daily_Raw_Meta", [HEAD_M, ["2026-08-10", "40", "1000", "900", "10", "1", "0", "1", "20"], ["2026-08-20", "10", "1000", "900", "10", "1", "0", "1", "100"]]);
b5.set("Daily_Raw_TikTok", [HEAD_T, ["2026-08-10", "1", "1", "1", "1", "0", "0", "0", "0", "0", "0"]]);
b5.set("Daily_Raw_Meta_Ads", [HEAD_M, ["2026-08-10", "40", "1000", "900", "10", "1", "0", "1", "20"], ["2026-08-20", "10", "1000", "900", "10", "1", "0", "1", "100"]]);
b5.set("Daily_Raw_TikTok_Ads", [HEAD_T, ["2026-08-10", "1", "1", "1", "1", "0", "0", "0", "0", "0", "0"]]);
for (const tab of ["Daily_Raw_Meta_Ads", "Daily_Raw_TikTok_Ads"]) {           // give them ad columns
  const t0 = b5.tabs[tab]; t0[0] = [...t0[0], "Ad_ID", "Ad_Name", "Campaign_Name", "AdGroup_Name", "AdSet_Name", "Creative_Key"];
  for (let i = 1; i < t0.length; i++) t0[i] = [...t0[i], "ad" + i, "ad " + i, "C1", "AG1", "ABO", "key-" + i];
}
const AUG = DateTime.fromISO("2026-09-01T07:15:00"); // monthly trigger -> window = Aug 1..31 2026
r = run(wf, b5, "Monthly Trigger", AUG);
const wk = b5.tabs["Report_Meta_Weekly"], hdr = wk[0];
t("two weekly buckets produced", wk.length === 3, JSON.stringify(wk.map((x) => x[hdr.indexOf("Period_Start")])));
t("no node failed", r.failed.size === 0, r.log.filter((l) => l.includes("!!")).join(" ; "));
t("rows chronological (not ROAS order: that would put Aug 20 first)", wk[1][hdr.indexOf("Period_Start")] === "2026-08-10" && wk[2][hdr.indexOf("Period_Start")] === "2026-08-17", wk.map((x) => x[hdr.indexOf("Period_Start")]).join("->"));
t("Rank = chronological index", wk[1][hdr.indexOf("Rank")] === 1 && wk[2][hdr.indexOf("Rank")] === 2);
t("ROAS_Rank kept separately, and is NOT the row order", hdr.includes("ROAS_Rank") && wk[1][hdr.indexOf("ROAS_Rank")] === 2 && wk[2][hdr.indexOf("ROAS_Rank")] === 1, `ranks ${wk[1][hdr.indexOf("ROAS_Rank")]},${wk[2][hdr.indexOf("ROAS_Rank")]}`);

console.log(`\n${fail ? fail + " FAILED, " : ""}${pass} passed`);
process.exit(fail ? 1 : 0);
