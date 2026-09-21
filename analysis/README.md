# Analysis scratch

- `workflow.graph.json` — reduced copy of the user's n8n export: all nodes, connections, sheet names,
  operations and `$()` references kept; long `jsCode` bodies replaced with the cross-node lookups only.
  `_out` fields are hand-annotated expected item counts used by the quota finding.
- `analyze.py` — graph checks (cleared vs appended vs read tabs, fan-in, cross-branch `$()`, default params).
- `findings.txt` — captured output that WORKFLOW.md cites.
