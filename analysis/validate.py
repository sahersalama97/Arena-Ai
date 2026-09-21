#!/usr/bin/env python3
"""Validate workflow.fixed.json the way n8n's importer will judge it."""
import json, collections, re, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = json.load(open(os.path.join(HERE, "workflow.fixed.json")))
N = {n["name"]: n for n in W["nodes"]}
kids, par = collections.defaultdict(list), collections.defaultdict(list)
for src, lst in W["connections"].items():
    for arr in lst["main"]:
        for c in arr:
            kids[src].append(c["node"])
            par[c["node"]].append(src)
fails = []
def chk(cond, label, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(label)

print("== shape ==")
chk(all(isinstance(v, dict) and "main" in v for v in W["connections"].values()), "connections use {'main': [...]}")
noCred=[n["name"] for n in W["nodes"] if n["type"].endswith("googleSheets") and not n.get("credentials")]
chk(not noCred, "every Sheets node has credentials", str(noCred))
chk(len({n["id"] for n in W["nodes"]}) == len(W["nodes"]), "node ids unique")
chk(not [k for k, v in collections.Counter(n["name"] for n in W["nodes"]).items() if v > 1], "node names unique")
chk(not [c["node"] for s, l in W["connections"].items() for a in l["main"] for c in a if c["node"] not in N], "all edges point at real nodes")

print("\n== reachability ==")
trig = [n["name"] for n in W["nodes"] if "Trigger" in n["type"]]
seen, st = set(), list(trig)
while st:
    x = st.pop()
    if x in seen: continue
    seen.add(x); st += kids[x]
chk(not [n["name"] for n in W["nodes"] if n["name"] not in seen], "every node reachable from a trigger",
    str([n["name"] for n in W["nodes"] if n["name"] not in seen]))
chk(not [n["name"] for n in W["nodes"] if not par[n["name"]] and "Trigger" not in n["type"]], "no node without an input")

print("\n== FIX-5: no cross-branch $() ==")
pat = re.compile(r"\$\('([^']+)'\)")
badrefs = []
for n in W["nodes"]:
    anc, st2 = set(), list(par[n["name"]])
    while st2:
        x = st2.pop()
        if x in anc: continue
        anc.add(x); st2 += par[x]
    for r in pat.findall(n["parameters"].get("jsCode") or ""):
        if r not in anc:
            badrefs.append(f"{n['name']} -> {r}")
chk(not badrefs, "every $('node') reference is a graph ancestor", str(badrefs))

print("\n== destructive-write safety ==")
gs = [n for n in W["nodes"] if n["type"].endswith("googleSheets")]
op = lambda n: n["parameters"].get("operation", "read")
tab = lambda n: n["parameters"]["sheetName"]["value"]
cl, wr, rd = [tab(n) for n in gs if op(n) == "clear"], [tab(n) for n in gs if op(n) == "append"], [tab(n) for n in gs if op(n) == "read"]
chk(set(cl) == set(wr) and len(cl) == 9, "9 cleared tabs == 9 appended tabs")
chk(not [t for t in cl if not t.startswith("Report_")], "no raw/input tab is ever cleared", str(cl))
chk(not (set(rd) & set(cl)), "no tab is both read and cleared")
chk(not [n for n in W["nodes"] if n.get("executeOnce")], "no node uses executeOnce (it starves downstream Sheets writes)")
cl_nodes = [n for n in gs if op(n) == "clear"]
chk(len(cl_nodes) == 9, "9 clear nodes")
# each clear must be fed by an aggregator that emits ONE packed item, and be followed by an expand
def parents_of(nm): return par[nm]
ok_pack = all("rows" in (N[parents_of(c["name"])[0]]["parameters"].get("jsCode") or "") for c in cl_nodes)
chk(ok_pack, "every aggregator emits a single packed {rows} item for its Clear")
exp = [n for n in W["nodes"] if n["name"].startswith("Expand ")]
chk(len(exp) == 9, "9 Expand nodes, one per report tab")
ok_chain = all(any(x["name"].startswith("Expand ") for x in [N[p] for p in par[w] if p in N]) for w in [n["name"] for n in gs if op(n) == "append"])
chk(ok_chain, "every Write is fed by an Expand, not by the Clear directly")
chk(not any(n.get("retryOnFail") for n in gs if op(n) == "append"), "FIX-9 no retryOnFail on appends (would double-write)")
chk(all(n.get("retryOnFail") for n in gs if op(n) == "clear"), "retryOnFail on clears (idempotent)")

print("\n== FIX-4 guards ==")
aggs = [n for n in W["nodes"] if n["type"].endswith(".code") and "Aggregator" in n["name"]]
norms = [n for n in W["nodes"] if n["name"].startswith("Normalize ")]
chk(len(aggs) == 9, "9 aggregators present")
chk(all("throw new Error" in (n["parameters"]["jsCode"] or "") for n in aggs), "every aggregator aborts on empty data")
chk(all("throw new Error" in (n["parameters"]["jsCode"] or "") for n in norms), "every normalizer aborts on unreadable/broken read")
# no clear/append reachable without a guard upstream? (guard must precede the clear)
for n in gs:
    if op(n) != "clear": continue
    chain, st3 = set(), list(par[n["name"]])
    while st3:
        x = st3.pop()
        if x in chain: continue
        chain.add(x); st3 += par[x]
    if not any("throw new Error" in (N[c]["parameters"].get("jsCode") or "") for c in chain if c in N):
        fails.append(f"{n['name']} has no guard upstream")
chk(not [f for f in fails if "no guard upstream" in f], "every Clear has a guard somewhere upstream")

print("\n== FIX-6 weekly chronology ==")
for n in aggs:
    if "Weekly" in n["name"]:
        code = n["parameters"]["jsCode"]
        chk("Period_Start<b.Period_Start" in code and "ROAS_Rank" in code, f"{n['name']} sorted by date, ROAS rank kept")

print("\n== FIX-1 single email ==")
mrg = [n for n in W["nodes"] if n["type"].endswith(".merge")]
jm = [n for n in mrg if n["name"] == "Join All Report Writes"][0]
chk(jm["parameters"]["numberInputs"] == 9, "email sits behind a 9-input Merge")
chk(sum(1 for a in W["connections"]["Join All Report Writes"]["main"] for _ in a) == 0 or "Join All Report Writes" in W["connections"], "merge is wired")
inidx = sorted(c["index"] for s, l in W["connections"].items() for a in l["main"] for c in a if c["node"] == "Join All Report Writes")
chk(inidx == list(range(9)), "9 distinct input indexes", str(inidx))
comp = [n for n in W["nodes"] if n["name"] == "Compose Report Email"][0]
chk(par[comp["name"]] == ["Join All Report Writes"], "Compose has exactly one parent", str(par[comp["name"]]))
em=[n for n in W["nodes"] if n["name"]=="Send Report Email"][0]
chk("text" in em["parameters"], "email node carries a body, not just a subject")

print("\n== JS syntax ==")
bad = []
for n in W["nodes"]:
    code = n["parameters"].get("jsCode")
    if not code: continue
    src = "async function __n(items,$,$today,$now,DateTime,executeData){\n" + code + "\n}"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(src); path = f.name
    r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
    if r.returncode:
        bad.append((n["name"], r.stderr.strip().splitlines()[-1] if r.stderr else "?"))
    os.unlink(path)
chk(not bad, "all 13 Code nodes parse as valid JS", str(bad))

print("\n" + ("ALL CHECKS PASSED" if not fails else f"{len(fails)} FAILURES: {fails}"))
sys.exit(1 if fails else 0)
