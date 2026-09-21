import json, collections, re, os

here = os.path.dirname(os.path.abspath(__file__))
w = json.load(open(os.path.join(here, "workflow.json")))
nodes = {n["name"]: n for n in w["nodes"]}
con = w["connections"]

children = collections.defaultdict(list)
parents = collections.defaultdict(list)
for src, lst in con.items():
    for out_idx, arr in enumerate(lst.get("main", [])):
        for c in arr or []:
            children[src].append(c["node"])
            parents[c["node"]].append(src)

gs = [n for n in w["nodes"] if n["type"].endswith("googleSheets")]
op = lambda n: n["parameters"].get("operation", "read(default)")
tab = lambda n: n["parameters"]["sheetName"]["value"]
cleared = [tab(n) for n in gs if op(n) == "clear"]
written = [tab(n) for n in gs if op(n) == "append"]
read = [tab(n) for n in gs if op(n) == "read(default)"]

print("== TABS ==")
print("cleared:", len(cleared), "| appended:", len(written), "| read:", len(read))
print("clear set == write set:", set(cleared) == set(written))
print("non-Report tab cleared:", [t for t in cleared if not t.startswith("Report_")] or "NONE  <-- raw data never wiped")
print("read & cleared:", set(read) & set(cleared) or "NONE  <-- nothing is both read and cleared")

print("\n== CLEAR PARAMS ==")
for n in gs:
    if op(n) == "clear":
        p = n["parameters"]
        print(f"  {n['name']:<38} Clear={p.get('clear','DEFAULT: Whole Sheet')}  keepFirstRow={p.get('keepFirstRow','DEFAULT: false')}  options={p.get('options','ABSENT')}")

print("\n== FAN-IN (parents > 1) ==")
for nm, ps in parents.items():
    if len(ps) > 1:
        print(f"  {nm}: {len(ps)} parents -> {ps}")

print("\n== ITEMS FEEDING EACH CLEAR (n8n loops clear per item) ==")
for n in gs:
    if op(n) == "clear":
        src = parents[n["name"]][0]
        print(f"  {n['name']:<38} <- {src:<36} rows={nodes[src].get('_out')}")

print("\n== CROSS-BRANCH $() LOOKUPS ==")
pat = re.compile(r"\$\('([^']+)'\)")
for n in w["nodes"]:
    code = n["parameters"].get("jsCode") or ""
    refs = pat.findall(code)
    if refs:
        upstream = set()
        seen, stack = set(), list(parents[n["name"]])
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); stack += parents[x]
        for r in set(refs):
            flag = "OK(in ancestors)" if r in seen else "!! NOT an ancestor (cross-branch)"
            print(f"  {n['name']:<30} -> $('{r}') {flag}")

print("\n== READ ERROR HANDLING ==")
for n in w["nodes"]:
    if "alwaysOutputData" in n:
        print(f"  {n['name']}: onError={n.get('onError')} alwaysOutputData={n['alwaysOutputData']}")

print("\n== PLACEHOLDERS ==")
for n in w["nodes"]:
    s = json.dumps(n["parameters"])
    if "PASTE_" in s:
        print(f"  {n['name']}: {[v for v in n['parameters'].values() if isinstance(v, str) and 'PASTE_' in v]}")

print("\n== COUNTS ==")
print("nodes:", len(w["nodes"]), "| googleSheets:", len(gs), "| code:", sum(1 for n in w['nodes'] if n['type'].endswith('.code')), "| triggers:", sum(1 for n in w['nodes'] if 'Trigger' in n['type']))
print("clear nodes:", len(cleared), "| append nodes:", len(written))

print("\n== API CALL ESTIMATE (one write op = one API call, clears loop per item) ==")
per_exec = {"Meta Overview": 13, "TikTok Overview": 14, "Combined": 7, "Meta Weekly": 5, "Meta Ad Perf": 80, "Meta Creative": 30,
            "TikTok Weekly": 5, "TikTok Ad Perf": 60, "TikTok Creative": 25}
print("  e.g. if Ad Performance has 80 rows -> Clear Report_Meta_Ad_Performance issues 80 identical values.clear calls")
