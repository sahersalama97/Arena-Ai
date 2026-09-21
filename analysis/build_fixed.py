#!/usr/bin/env python3
"""Generate workflow.fixed.json from the reviewed findings.

Every change below is labelled FIX-N so it can be traced to WORKFLOW.md.
Run:  python3 analysis/build_fixed.py
"""
import json, os, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = "1ENZCyFBgTNiPuE7nRz5ofic5pao_zjdhwiFLIEyo5LE"
CRED = {"googleSheetsOAuth2Api": {"id": "rqsBKtQ08F7jiPT4", "name": "Google Sheets account"}}

# ---------------------------------------------------------------- shared code --
# FIX-2 (hardened parsing) + FIX-4 (period guard). One normalizer per raw tab so
# date/number coercion lives in exactly one place, not in 9 aggregators.
NORMALIZE = """// Normalizes one Daily_Raw_* tab: clean Date -> ISO, measures -> real numbers,
// and ABORTS the run instead of letting a later Clear node publish zeros.
// Set DATE_ORDER to 'dmy' if your raw tab displays 25/9/2026, 'mdy' if it displays 9/25/2026.
const SOURCE = '__SOURCE__';
const TAB = '__TAB__';
const DATE_ORDER = 'auto';

const MEASURES = ['Spend','Impressions','Reach','Clicks','LPV','Profile_Visits','Follows',
  'Adds_to_Cart','Initiate_Checkout','Purchases','Purchases_Value'];

function toISODate(v) {
  if (v === null || v === undefined || v === '') return '';
  if (v instanceof Date) return v.toISOString().slice(0,10);
  const s = String(v).trim();
  let m = s.match(/^(\\d{4})-(\\d{2})-(\\d{2})/);                     // already ISO
  if (m) return m[1]+'-'+m[2]+'-'+m[3];
  m = s.match(/^(\\d{1,2})[\\/.](\\d{1,2})[\\/.](\\d{4})$/);            // a/b/yyyy
  if (m) {
    const a = +m[1], b = +m[2], y = m[3];
    let day, mon;
    if (DATE_ORDER === 'dmy') { day = a; mon = b; }
    else if (DATE_ORDER === 'mdy') { mon = a; day = b; }
    else if (a > 12) { day = a; mon = b; }                             // 25/9 -> dmy
    else if (b > 12) { mon = a; day = b; }                             // 9/25 -> mdy
    else { day = a; mon = b; }                                        // ambiguous: matches d/m/yyyy export
    if (mon < 1 || mon > 12 || day < 1 || day > 31) return '';
    const pad = (n) => String(n).padStart(2,'0');
    return y+'-'+pad(mon)+'-'+pad(day);
  }
  m = s.match(/^(\\d{4})[\\/.](\\d{1,2})[\\/.](\\d{1,2})$/);            // yyyy/m/d
  if (m) { const pad = (n) => String(n).padStart(2,'0'); return m[1]+'-'+pad(+m[2])+'-'+pad(+m[3]); }
  const n = Number(s.replace(/[^0-9.]/g,''));                          // Sheets serial number
  if (Number.isFinite(n) && n > 20000 && n < 80000)
    return new Date(Date.UTC(1899,11,30) + n*86400000).toISOString().slice(0,10);
  return '';
}

function num(v) {
  if (v === null || v === undefined || v === '') return 0;
  const n = Number(String(v).replace(/[,\\s\\u00a0]/g,'').replace(/[^\\d.\\-]/g,''));
  return Number.isFinite(n) ? n : 0;
}

const out = [];
let unparsed = 0;
for (const it of items) {
  const r = it.json || {};
  if (r.error) throw new Error(`Read of ${TAB} failed upstream: ${r.error.message || JSON.stringify(r.error)}`);
  const d = toISODate(r.Date);
  if (!d) { unparsed++; continue; }
  const row = Object.assign({}, r, { Date: d, DateISO: d, Source: SOURCE });
  for (const k of MEASURES) if (r[k] !== undefined) row[k] = num(r[k]);
  out.push({ json: row, pairedItem: it.pairedItem });
}
if (!out.length) throw new Error(
  `${TAB}: no usable rows (read ${items.length} row(s), ${unparsed} with an unparseable Date). ` +
  `Stopping before any report tab is cleared. If your dates are d/m/yyyy set DATE_ORDER='dmy'.`);
return out;"""

# Shared prologue for every aggregator: period + FIX-4 guard.
PROLOGUE = """function num(v){if(v==null||v==='')return 0;const n=Number(String(v).replace(/[,\\s]/g,'').replace(/[^\\d.\\-]/g,''));return Number.isFinite(n)?n:0;}
function round(n,p){const f=10**p;return Math.round(n*f)/f;}
const period=$('Set Period').first().json;
const rows=items.map(i=>i.json).filter(r=>r.DateISO>=period.periodStart&&r.DateISO<=period.periodEnd);
if(!rows.length) throw new Error('__NAME__: 0 raw rows inside '+period.periodStart+'..'+period.periodEnd+' - aborting rather than clearing the report with zeros');"""

OVERVIEW_CALC = """let spend=0,impressions=0,reach=0,atc=0,ic=0,purchases=0,purchasesValue=0,clicks=0;
for(const r of rows){spend+=num(r.Spend);impressions+=num(r.Impressions);reach+=num(r.Reach);atc+=num(r.Adds_to_Cart);ic+=num(r.Initiate_Checkout);purchases+=num(r.Purchases);purchasesValue+=num(r.Purchases_Value);clicks+=num(r.Clicks);}
const cpm=impressions?(spend/impressions)*1000:0;
const frequency=reach?impressions/reach:0;
const ctr=impressions?(clicks/impressions)*100:0;
const roas=spend?purchasesValue/spend:0;
const aov=purchases?purchasesValue/purchases:0;
const cvr=clicks?(purchases/clicks)*100:0;
const out=[
 {'Metric':'Spend','Value':round(spend,2)},
 {'Metric':'CPM','Value':round(cpm,2)},
 {'Metric':'Outbound CTR %','Value':round(ctr,4)},
 {'Metric':'Impressions','Value':impressions},
 {'Metric':'Reach','Value':reach},
 {'Metric':'Frequency','Value':round(frequency,2)},
 {'Metric':'Adds to Cart','Value':atc},
 {'Metric':'Initiate Checkout','Value':ic},
 {'Metric':'Purchases','Value':purchases},
 {'Metric':'Purchases Value','Value':round(purchasesValue,2)},
 {'Metric':'ROAS','Value':round(roas,4)},
 {'Metric':'AOV','Value':round(aov,2)},
 {'Metric':'Purchase CVR %','Value':round(cvr,4)},
];
return [{ json: { rows: out } }];"""

TIKTOK_OVERVIEW_CALC = """let spend=0,impressions=0,reach=0,atc=0,ic=0,purchases=0,purchasesValue=0,clicks=0,profileVisits=0,follows=0;
for(const r of rows){spend+=num(r.Spend);impressions+=num(r.Impressions);reach+=num(r.Reach);atc+=num(r.Adds_to_Cart);ic+=num(r.Initiate_Checkout);purchases+=num(r.Purchases);purchasesValue+=num(r.Purchases_Value);clicks+=num(r.Clicks);profileVisits+=num(r.Profile_Visits);follows+=num(r.Follows);}
const cpm=impressions?(spend/impressions)*1000:0;
const ctr=impressions?(clicks/impressions)*100:0;
const roas=spend?purchasesValue/spend:0;
const aov=purchases?purchasesValue/purchases:0;
const cvr=clicks?(purchases/clicks)*100:0;
const out=[
 {'Metric':'Spend','Value':round(spend,2)},
 {'Metric':'CPM','Value':round(cpm,2)},
 {'Metric':'CTR %','Value':round(ctr,4)},
 {'Metric':'Impressions','Value':impressions},
 {'Metric':'Reach','Value':reach},
 {'Metric':'Adds to Cart','Value':atc},
 {'Metric':'Initiate Checkout','Value':ic},
 {'Metric':'Purchases','Value':purchases},
 {'Metric':'Purchases Value','Value':round(purchasesValue,2)},
 {'Metric':'ROAS','Value':round(roas,4)},
 {'Metric':'AOV','Value':round(aov,2)},
 {'Metric':'Purchase CVR %','Value':round(cvr,4)},
 {'Metric':'Paid Profile Visits','Value':profileVisits},
 {'Metric':'Paid Follows','Value':follows},
];
return [{ json: { rows: out } }];"""

WEEKLY_CALC = """const weeks={};
for(const r of rows){
 const ws=DateTime.fromISO(r.DateISO).startOf('week');
 const key=ws.toISODate();
 if(!weeks[key])weeks[key]={start:ws,end:ws.plus({days:6}),spend:0,impressions:0,purchases:0,purchasesValue:0};
 const w=weeks[key];
 w.spend+=num(r.Spend); w.impressions+=num(r.Impressions); w.purchases+=num(r.Purchases); w.purchasesValue+=num(r.Purchases_Value);
}
let list=Object.values(weeks).map(w=>({
 Week:w.start.toFormat('MMM d')+'-'+w.end.toFormat('d'),
 Period_Start:w.start.toISODate(), Period_End:w.end.toISODate(),
 Spend:round(w.spend,2), CPM:round(w.impressions?(w.spend/w.impressions)*1000:0,2),
 Purchases:w.purchases, Purchases_Value:round(w.purchasesValue,2),
 ROAS: w.spend? round(w.purchasesValue/w.spend,4) : ''
}));
// FIX-6: chronological order for a time series; ROAS ranking kept separately.
list.sort((a,b)=>a.Period_Start<b.Period_Start?-1:1);
const byRoas=[...list].sort((a,b)=>(b.ROAS===''?-1:b.ROAS)-(a.ROAS===''?-1:a.ROAS));
const roasRank=new Map(byRoas.map((r,i)=>[r.Period_Start,i+1]));
const ranked = list.map((r, idx) => ({ Rank: idx + 1, ROAS_Rank: roasRank.get(r.Period_Start), ...r }));
return [{ json: { rows: ranked } }];"""

META_AD_CALC = """const groups={};
for(const r of rows){
 const key=r.Ad_ID||r.Ad_Name;
 if(!groups[key])groups[key]={Ad_ID:r.Ad_ID,Ad_Name:r.Ad_Name,AdSet_Name:r.AdSet_Name,Campaign_Name:r.Campaign_Name,Creative_Key:r.Creative_Key,spend:0,impressions:0,reach:0,clicks:0,lpv:0,atc:0,ic:0,purchases:0,purchasesValue:0};
 const g=groups[key];
 g.spend+=num(r.Spend); g.impressions+=num(r.Impressions); g.reach+=num(r.Reach); g.clicks+=num(r.Clicks); g.lpv+=num(r.LPV); g.atc+=num(r.Adds_to_Cart); g.ic+=num(r.Initiate_Checkout); g.purchases+=num(r.Purchases); g.purchasesValue+=num(r.Purchases_Value);
}
let list=Object.values(groups).map(g=>({
 Ad_ID:g.Ad_ID, Ad_Name:g.Ad_Name, AdSet_Name:g.AdSet_Name, Campaign_Name:g.Campaign_Name, Creative_Key:g.Creative_Key,
 Spend:round(g.spend,2), Impressions:g.impressions, Reach:g.reach,
 Frequency:round(g.reach?g.impressions/g.reach:0,2), CPM:round(g.impressions?(g.spend/g.impressions)*1000:0,2),
 Clicks:g.clicks, CTR_Pct:round(g.impressions?(g.clicks/g.impressions)*100:0,4),
 LPV:g.lpv, Adds_to_Cart:g.atc, Initiate_Checkout:g.ic, Purchases:g.purchases,
 Purchases_Value:round(g.purchasesValue,2), ROAS:round(g.spend?g.purchasesValue/g.spend:0,4),
 AOV:round(g.purchases?g.purchasesValue/g.purchases:0,2), Purchase_CVR_Pct:round(g.clicks?(g.purchases/g.clicks)*100:0,4)
}));
list.sort((a,b)=>b.Spend-a.Spend);"""

META_CREATIVE_CALC = """const groups={};
for(const r of rows){
 const key=r.Creative_Key||'(unknown)';
 if(!groups[key])groups[key]={Creative_Key:key,adIds:new Set(),spend:0,impressions:0,clicks:0,lpv:0,atc:0,ic:0,purchases:0,purchasesValue:0};
 const g=groups[key];
 g.adIds.add(r.Ad_ID);
 g.spend+=num(r.Spend); g.impressions+=num(r.Impressions); g.clicks+=num(r.Clicks); g.lpv+=num(r.LPV); g.atc+=num(r.Adds_to_Cart); g.ic+=num(r.Initiate_Checkout); g.purchases+=num(r.Purchases); g.purchasesValue+=num(r.Purchases_Value);
}
let list=Object.values(groups).map(g=>({
 Creative_Key:g.Creative_Key, Instances:g.adIds.size,
 Spend:round(g.spend,2), Impressions:g.impressions,
 CPM:round(g.impressions?(g.spend/g.impressions)*1000:0,2),
 Clicks:g.clicks, CTR_Pct:round(g.impressions?(g.clicks/g.impressions)*100:0,4),
 LPV:g.lpv, Adds_to_Cart:g.atc, Initiate_Checkout:g.ic, Purchases:g.purchases,
 Purchases_Value:round(g.purchasesValue,2), ROAS:round(g.spend?g.purchasesValue/g.spend:0,4),
 AOV:round(g.purchases?g.purchasesValue/g.purchases:0,2), Purchase_CVR_Pct:round(g.clicks?(g.purchases/g.clicks)*100:0,4)
}));
list.sort((a,b)=>b.Spend-a.Spend);"""

TT_AD_CALC = """const groups={};
for(const r of rows){
 const key=r.Ad_ID||r.Ad_Name;
 if(!groups[key])groups[key]={Ad_ID:r.Ad_ID,Ad_Name:r.Ad_Name,Campaign_Name:r.Campaign_Name,AdGroup_Name:r.AdGroup_Name,Creative_Key:r.Creative_Key,spend:0,impressions:0,reach:0,clicks:0,profileVisits:0,follows:0,atc:0,ic:0,purchases:0,purchasesValue:0};
 const g=groups[key];
 g.spend+=num(r.Spend); g.impressions+=num(r.Impressions); g.reach+=num(r.Reach); g.clicks+=num(r.Clicks); g.profileVisits+=num(r.Profile_Visits); g.follows+=num(r.Follows); g.atc+=num(r.Adds_to_Cart); g.ic+=num(r.Initiate_Checkout); g.purchases+=num(r.Purchases); g.purchasesValue+=num(r.Purchases_Value);
}
let list=Object.values(groups).map(g=>({
 Ad_ID:g.Ad_ID, Ad_Name:g.Ad_Name, Campaign_Name:g.Campaign_Name, AdGroup_Name:g.AdGroup_Name, Creative_Key:g.Creative_Key,
 Spend:round(g.spend,2), Impressions:g.impressions, Reach:g.reach,
 CPM:round(g.impressions?(g.spend/g.impressions)*1000:0,2),
 Clicks:g.clicks, CTR_Pct:round(g.impressions?(g.clicks/g.impressions)*100:0,4),
 Profile_Visits:g.profileVisits, Follows:g.follows,
 Adds_to_Cart:g.atc, Initiate_Checkout:g.ic, Purchases:g.purchases,
 Purchases_Value:round(g.purchasesValue,2), ROAS:round(g.spend?g.purchasesValue/g.spend:0,4),
 AOV:round(g.purchases?g.purchasesValue/g.purchases:0,2), Purchase_CVR_Pct:round(g.clicks?(g.purchases/g.clicks)*100:0,4)
}));
list.sort((a,b)=>b.Spend-a.Spend);"""

TT_CREATIVE_CALC = """const groups={};
for(const r of rows){
 const key=r.Creative_Key||'(unknown)';
 if(!groups[key])groups[key]={Creative_Key:key,adIds:new Set(),spend:0,impressions:0,clicks:0,profileVisits:0,follows:0,atc:0,ic:0,purchases:0,purchasesValue:0};
 const g=groups[key];
 g.adIds.add(r.Ad_ID);
 g.spend+=num(r.Spend); g.impressions+=num(r.Impressions); g.clicks+=num(r.Clicks); g.profileVisits+=num(r.Profile_Visits); g.follows+=num(r.Follows); g.atc+=num(r.Adds_to_Cart); g.ic+=num(r.Initiate_Checkout); g.purchases+=num(r.Purchases); g.purchasesValue+=num(r.Purchases_Value);
}
let list=Object.values(groups).map(g=>({
 Creative_Key:g.Creative_Key, Instances:g.adIds.size,
 Spend:round(g.spend,2), Impressions:g.impressions,
 CPM:round(g.impressions?(g.spend/g.impressions)*1000:0,2),
 Clicks:g.clicks, CTR_Pct:round(g.impressions?(g.clicks/g.impressions)*100:0,4),
 Profile_Visits:g.profileVisits, Follows:g.follows,
 Adds_to_Cart:g.atc, Initiate_Checkout:g.ic, Purchases:g.purchases,
 Purchases_Value:round(g.purchasesValue,2), ROAS:round(g.spend?g.purchasesValue/g.spend:0,4),
 AOV:round(g.purchases?g.purchasesValue/g.purchases:0,2), Purchase_CVR_Pct:round(g.clicks?(g.purchases/g.clicks)*100:0,4)
}));
list.sort((a,b)=>b.Spend-a.Spend);"""

# FIX-3: the Clear node loops `for (let i = 0; i < items.length; i++)`, so N items = N
# values.clear calls. executeOnce is NOT the answer (n8n trims the node's input to the first
# item and the Clear passes that trimmed list on, starving the Write). Instead every
# aggregator hands its rows down as ONE packed item, and the tab is expanded again after
# the clear: Aggregator -> Clear (1 call) -> Expand -> Write (N rows).
RANK_TAIL = """
const ranked = list.map((r, idx) => ({ Rank: idx + 1, ...r }));
return [{ json: { rows: ranked } }];"""

EXPAND = "return (items[0] && items[0].json && items[0].json.rows) || [];"""
EXPAND_SAFE = """const rows = (items[0] && items[0].json && items[0].json.rows) || [];
if (!rows.length) throw new Error('Expand __NAME__: received no rows - refusing to write an empty tab after the clear');
return rows.map((r) => ({ json: r && r.json ? r.json : r }));"""

# FIX-5: Combined reads its inputs (tagged by Source) instead of reaching across
# branches with $() calls that only work because of canvas position.
COMBINED_CALC = """function num(v){if(v==null||v==='')return 0;const n=Number(String(v).replace(/[,\s]/g,'').replace(/[^\d.\-]/g,''));return Number.isFinite(n)?n:0;}
function round(n,p){const f=10**p;return Math.round(n*f)/f;}
const period=$('Set Period').first().json;
const rows=items.map(i=>i.json).filter(r=>r.DateISO>=period.periodStart&&r.DateISO<=period.periodEnd);
if(!rows.length) throw new Error('Combined: 0 raw rows inside '+period.periodStart+'..'+period.periodEnd+' - aborting rather than clearing the report with zeros');
function totals(src){
 let spend=0,purchases=0,purchasesValue=0;
 for(const r of rows){ if(r.Source!==src) continue;
  spend+=num(r.Spend); purchases+=num(r.Purchases); purchasesValue+=num(r.Purchases_Value); }
 return {spend,purchases,purchasesValue,roas:spend?purchasesValue/spend:0,aov:purchases?purchasesValue/purchases:0};
}
const m=totals('meta'), t=totals('tiktok');
const combinedSpend=m.spend+t.spend, combinedPurchases=m.purchases+t.purchases, combinedValue=m.purchasesValue+t.purchasesValue;
const combinedRoas=combinedSpend?combinedValue/combinedSpend:0;
const combinedAov=combinedPurchases?combinedValue/combinedPurchases:0;
const out=[
 {'Metric':'Spend','Meta':round(m.spend,2),'TikTok':round(t.spend,2),'Combined':round(combinedSpend,2)},
 {'Metric':'Purchases','Meta':m.purchases,'TikTok':t.purchases,'Combined':combinedPurchases},
 {'Metric':'Purchases Value','Meta':round(m.purchasesValue,2),'TikTok':round(t.purchasesValue,2),'Combined':round(combinedValue,2)},
 {'Metric':'ROAS','Meta':round(m.roas,4),'TikTok':round(t.roas,4),'Combined':round(combinedRoas,4)},
 {'Metric':'AOV','Meta':round(m.aov,2),'TikTok':round(t.aov,2),'Combined':round(combinedAov,2)},
 {'Metric':'Meta Share of Spend %','Meta':round(combinedSpend?(m.spend/combinedSpend)*100:0,2),'TikTok':'','Combined':''},
 {'Metric':'TikTok Share of Spend %','Meta':'','TikTok':round(combinedSpend?(t.spend/combinedSpend)*100:0,2),'Combined':''},
];
return [{ json: { rows: out } }];"""

# FIX-7: compose stops instead of emailing "undefined" if the data is not there.
COMPOSE_CALC = """const period=$('Set Period').first().json;
const packed=$('Combined Aggregator').first().json.rows || [];
const combined=packed;
const get=(metric)=>combined.find(r=>r.Metric===metric)||{};
const spend=get('Spend'), purchases=get('Purchases'), value=get('Purchases Value'), roas=get('ROAS');
const money=(v)=>v===''||v===undefined||v===null?'n/a':Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const x=(v)=>v===''||v===undefined||v===null?'n/a':v;
if(!combined.length) throw new Error('Combined Aggregator produced no rows - refusing to send an empty report');
const sheetUrl='https://docs.google.com/spreadsheets/d/__DOC__/edit';
const text=`GoFresh Ads Report - ${period.periodLabel}\\n\\n`+
`Period: ${period.periodStart} to ${period.periodEnd}\\n\\n`+
`Combined Spend: ${money(spend.Combined)}\\n`+
`Combined Purchases: ${x(purchases.Combined)}\\n`+
`Combined Purchases Value: ${money(value.Combined)}\\n`+
`Combined ROAS: ${x(roas.Combined)}\\n\\n`+
`Meta   - Spend: ${money(spend.Meta)}, ROAS: ${x(roas.Meta)}\\n`+
`TikTok - Spend: ${money(spend.TikTok)}, ROAS: ${x(roas.TikTok)}\\n\\n`+
`Full report: ${sheetUrl}`;
return [{json:{subject:`GoFresh Ads Report - ${period.periodLabel}`, text}}];"""


def sheet_node(nid, name, x, y, params, extra=None):
    n = {
        "parameters": params,
        "id": nid, "name": name,
        "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.7,
        "position": [x, y],
        "credentials": CRED,
    }
    n.update(extra or {})
    return n


def doc_ref(v):
    return {"__rl": True, "mode": "id", "value": v}


def code(nid, name, x, y, src):
    return {"parameters": {"jsCode": src}, "id": nid, "name": name,
            "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x, y]}


nodes, conns = [], {}

# --- stage 0: triggers (FIX-8: the 3 crons are unchanged; see WORKFLOW.md 4.7) --
nodes.append({"parameters": {}, "id": "t1", "name": "Manual Test",
              "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [-560, -48]})
nodes.append({"parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "0 7 * * 1"}]}},
              "id": "t2", "name": "Weekly Trigger", "type": "n8n-nodes-base.scheduleTrigger",
              "typeVersion": 1.2, "position": [-560, 160]})
nodes.append({"parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "15 7 1 * *"}]}},
              "id": "t3", "name": "Monthly Trigger", "type": "n8n-nodes-base.scheduleTrigger",
              "typeVersion": 1.2, "position": [-560, 368]})

# --- stage 1: period ----------------------------------------------------------
nodes.append(code("p1", "Set Manual Period", -320, -48,
    "const until=$today.minus({days:1});\nconst since=until.minus({days:6});\n"
    "return [{json:{reportType:'manual',periodStart:since.toISODate(),periodEnd:until.toISODate(),"
    "periodLabel:'Manual test - last 7 days'}}];"))
nodes.append(code("p2", "Set Weekly Period", -320, 160,
    "const start=$now.minus({weeks:1}).startOf('week');\nconst end=start.plus({days:6});\n"
    "return [{json:{reportType:'weekly',periodStart:start.toISODate(),periodEnd:end.toISODate(),"
    "periodLabel:start.toFormat('MMM d')+' - '+end.toFormat('MMM d, yyyy')}}];"))
nodes.append(code("p3", "Set Monthly Period", -320, 368,
    "const start=$now.minus({months:1}).startOf('month');\nconst end=start.endOf('month');\n"
    "return [{json:{reportType:'monthly',periodStart:start.toISODate(),periodEnd:end.toISODate(),"
    "periodLabel:start.toFormat('MMMM yyyy')}}];"))
nodes.append({"parameters": {}, "id": "sp", "name": "Set Period",
              "type": "n8n-nodes-base.noOp", "typeVersion": 1, "position": [-80, 160]})

conns["Manual Test"] = [[{"node": "Set Manual Period", "type": "main", "index": 0}]]
conns["Weekly Trigger"] = [[{"node": "Set Weekly Period", "type": "main", "index": 0}]]
conns["Monthly Trigger"] = [[{"node": "Set Monthly Period", "type": "main", "index": 0}]]
for p in ("Set Manual Period", "Set Weekly Period", "Set Monthly Period"):
    conns[p] = [[{"node": "Set Period", "type": "main", "index": 0}]]

READS = [("Read Daily_Raw_Meta", "r1", "Daily_Raw_Meta", -416),
         ("Read Daily_Raw_Meta_Ads", "r2", "Daily_Raw_Meta_Ads", -176),
         ("Read Daily_Raw_TikTok", "r3", "Daily_Raw_TikTok", 144),
         ("Read Daily_Raw_TikTok_Ads", "r4", "Daily_Raw_TikTok_Ads", 384)]
conns["Set Period"] = [[{"node": n, "type": "main", "index": 0} for n, _, _, _ in READS]]
# read -> normalizer wiring is emitted further down (after NORM is defined)
for name, nid, tab, y in READS:
    nodes.append(sheet_node(nid, name, 160, y, {"documentId": doc_ref(DOC),
                                                "sheetName": {"__rl": True, "mode": "name", "value": tab},
                                                "options": {}},
                            extra={"alwaysOutputData": True, "onError": "continueRegularOutput",
                                   # FIX-9: transient 429/timeouts retried (safe on a read)
                                   "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 2000}))

# --- stage 2.5: one normalizer per raw tab ------------------------------------
# name, id, Source tag, raw tab, x, y
NORM = [("Normalize Meta", "n1", "meta", "Daily_Raw_Meta", 64, -416),
        ("Normalize Meta Ads", "n2", "meta_ads", "Daily_Raw_Meta_Ads", 64, -176),
        ("Normalize TikTok", "n3", "tiktok", "Daily_Raw_TikTok", 64, 144),
        ("Normalize TikTok Ads", "n4", "tiktok_ads", "Daily_Raw_TikTok_Ads", 64, 384)]
READ_TO_NORM = {"Daily_Raw_Meta": "Normalize Meta", "Daily_Raw_Meta_Ads": "Normalize Meta Ads",
                "Daily_Raw_TikTok": "Normalize TikTok", "Daily_Raw_TikTok_Ads": "Normalize TikTok Ads"}
for name, nid, source, tab, x, y in NORM:
    nodes.append(code(nid, name, x, y, NORMALIZE.replace("__SOURCE__", source).replace("__TAB__", tab)))

# FIX-5: explicit join so Combined never depends on canvas position
nodes.append({"parameters": {"mode": "append", "numberInputs": 2,
                             "options": {"additionalOptions": {"alternateInputs": False}}},
              "id": "mg0", "name": "Join Overview Reads",
              "type": "n8n-nodes-base.merge", "typeVersion": 3, "position": [336, 560]})
MERGE_FEED = {"Normalize Meta": ("Join Overview Reads", 0), "Normalize TikTok": ("Join Overview Reads", 1)}

# --- stage 3: aggregators -----------------------------------------------------
# name, id, x, y, parent(normalizer), prologue-name, calc, tail
# name, id, x, y, parent normalizer, label, calc, needs "return list.map(...)" tail?
AGGS = [
    ("Meta Overview Aggregator", "a1", 880, -496, "Normalize Meta", "Meta Overview", OVERVIEW_CALC, False),
    ("Meta Weekly Aggregator", "a2", 880, -336, "Normalize Meta", "Meta Weekly", WEEKLY_CALC, False),
    ("Meta Ad Performance Aggregator", "a3", 880, -176, "Normalize Meta Ads", "Meta Ad Performance", META_AD_CALC, True),
    ("Meta Creative Rollup Aggregator", "a4", 880, -16, "Normalize Meta Ads", "Meta Creative Rollup", META_CREATIVE_CALC, True),
    ("TikTok Overview Aggregator", "a5", 880, 96, "Normalize TikTok", "TikTok Overview", TIKTOK_OVERVIEW_CALC, False),
    ("TikTok Weekly Aggregator", "a6", 880, 256, "Normalize TikTok", "TikTok Weekly", WEEKLY_CALC, False),
    ("TikTok Ad Performance Aggregator", "a7", 880, 416, "Normalize TikTok Ads", "TikTok Ad Performance", TT_AD_CALC, True),
    ("TikTok Creative Rollup Aggregator", "a8", 880, 576, "Normalize TikTok Ads", "TikTok Creative Rollup", TT_CREATIVE_CALC, True),
]
agg_pos = {}
for name, nid, x, y, parent, label, calc, needs_tail in AGGS:
    body = PROLOGUE.replace("__NAME__", label) + "\n" + calc + (RANK_TAIL if needs_tail else "")
    nodes.append(code(nid, name, x, y, body))
    agg_pos[name] = (x, y)

nodes.append(code("a9", "Combined Aggregator", 880, 736, COMBINED_CALC))
conns["Join Overview Reads"] = [[{"node": "Combined Aggregator", "type": "main", "index": 0}]]

# --- stage 4: clear + append, one pair per report tab ------------------------
REPORTS = [
    ("Report_Meta_Overview", "Meta Overview Aggregator", -496),
    ("Report_Meta_Weekly", "Meta Weekly Aggregator", -336),
    ("Report_Meta_Ad_Performance", "Meta Ad Performance Aggregator", -176),
    ("Report_Meta_Creative_Rollup", "Meta Creative Rollup Aggregator", -16),
    ("Report_TikTok_Overview", "TikTok Overview Aggregator", 96),
    ("Report_TikTok_Weekly", "TikTok Weekly Aggregator", 256),
    ("Report_TikTok_Ad_Performance", "TikTok Ad Performance Aggregator", 416),
    ("Report_TikTok_Creative_Rollup", "TikTok Creative Rollup Aggregator", 576),
    ("Report_Combined", "Combined Aggregator", 736),
]
for name, nid, source, tab, x, y in NORM:
    outs = []
    if name in MERGE_FEED:
        m, idx = MERGE_FEED[name]
        outs.append({"node": m, "type": "main", "index": idx})
    for an, _, _, _, parent, _, _, _ in AGGS:
        if parent == name:
            outs.append({"node": an, "type": "main", "index": 0})
    conns[name] = [outs]

for rn, rid, rtab, ry in READS:
    conns[rn] = [[{"node": READ_TO_NORM[rtab], "type": "main", "index": 0}]]

for i, (tab, agg, y) in enumerate(REPORTS, start=1):
    clear_name, write_name = f"Clear {tab}", f"Write {tab}"
    # FIX-3 executeOnce: n8n's clear loops per input item -> 1 call instead of N.
    # retryOnFail is safe here (clearing twice is a no-op) but deliberately NOT on append.
    nodes.append(sheet_node(f"c{i}", clear_name, 1140, y,
                            {"operation": "clear", "documentId": doc_ref(DOC),
                             "sheetName": {"__rl": True, "mode": "name", "value": tab},
                             "clear": "wholeSheet", "keepFirstRow": False},
                            extra={"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 2000}))
    expand_name = f"Expand {tab} Rows"
    nodes.append(code(f"e{i}", expand_name, 1380, y, EXPAND_SAFE.replace("__NAME__", tab)))
    nodes.append(sheet_node(f"w{i}", write_name, 1620, y,
                            {"operation": "append", "documentId": doc_ref(DOC),
                             "sheetName": {"__rl": True, "mode": "name", "value": tab},
                             "columns": {"mappingMode": "autoMapInputData", "value": {},
                                         "matchingColumns": [], "schema": [],
                                         "attemptToConvertTypes": False, "convertFieldsToString": False},
                             "options": {}}))
    conns[agg] = [[{"node": clear_name, "type": "main", "index": 0}]]
    conns[clear_name] = [[{"node": expand_name, "type": "main", "index": 0}]]
    conns[expand_name] = [[{"node": write_name, "type": "main", "index": 0}]]
    conns[write_name] = [[]]  # destination input index assigned below

# FIX-1: Merge is the sync point. A plain fan-in would fire Compose once per branch.
nodes.append({"parameters": {"mode": "append", "numberInputs": 9,
                             "options": {"additionalOptions": {"alternateInputs": False}}}, "id": "mg1", "name": "Join All Report Writes",
              "type": "n8n-nodes-base.merge", "typeVersion": 3, "position": [1408, 160]})
conns["Join All Report Writes"] = [[{"node": "Compose Report Email", "type": "main", "index": 0}]]
nodes.append(code("em1", "Compose Report Email", 1648, 160, COMPOSE_CALC.replace("__DOC__", DOC)))
nodes.append({"parameters": {"fromEmail": "PASTE_ALERT_SENDER_EMAIL@example.com",
                             "toEmail": "PASTE_YOUR_REPORT_EMAIL@example.com",
                             "subject": "={{ $json.subject }}", "text": "={{ $json.text }}",
                             "options": {"appendAttribution": False}},
              "id": "em2", "name": "Send Report Email", "type": "n8n-nodes-base.emailSend",
              "typeVersion": 2.1, "position": [1888, 160],
              "webhookId": "90e88a71-3cf4-4f5f-811b-f4b5b58338fa"})
conns["Compose Report Email"] = [[{"node": "Send Report Email", "type": "main", "index": 0}]]
for i, (tab, _, __) in enumerate(REPORTS, start=1):
    conns[f"Write {tab}"][0].append({"node": "Join All Report Writes", "type": "main", "index": i - 1})

# n8n requires {"Node": {"main": [[...]]}}; build as plain lists, wrap on the way out.
conn_out = {k: {"main": [a for a in v if a]} for k, v in conns.items() if any(v)}
out = {"nodes": nodes, "connections": conn_out, "pinData": {},
       "meta": {"instanceId": "9df071be3540d8b54994d231aeb8bda34843d4fc0415c70e3399690bf7e7c6ec"}}
for n in out["nodes"]:
    n.setdefault("parameters", {})
path = os.path.join(HERE, "workflow.fixed.json")
json.dump(out, open(path, "w"), indent=2)
print(f"wrote {path}: {len(nodes)} nodes, {len(conns)} connection sources")
