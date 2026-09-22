# Analysis scratch

- `workflow.graph.json` — reduced copy of the user's n8n export: all nodes, connections, sheet names,
  operations and `$()` references kept; long `jsCode` bodies replaced with the cross-node lookups only.
  `_out` fields are hand-annotated expected item counts used by the quota finding.
- `analyze.py` — graph checks (cleared vs appended vs read tabs, fan-in, cross-branch `$()`, default params).
- `findings.txt` — captured output that WORKFLOW.md cites.

## Running the checks

```bash
python3 analysis/validate.py     # static graph/param checks, no deps
cd analysis && npm install       # one-time: installs luxon (git-ignored)
node analysis/run_nodes.js       # 43 runtime checks via the mini n8n emulator
python3 analysis/build_fixed.py  # regenerate workflow.fixed.json from the fix table
```

`analysis/node_modules/` is intentionally git-ignored (it was committed once by mistake and
removed in a later commit); `npm install` in `analysis/` recreates it.
