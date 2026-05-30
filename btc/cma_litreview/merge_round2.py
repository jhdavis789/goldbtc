#!/usr/bin/env python3
"""
merge_round2.py — fold the round-2 workflow output (4 added families + correction pass)
into workflow_result.json, in place. Idempotent-ish: appends only families not already
present by name; applies corrections by exact name match.

Usage: python3 merge_round2.py <round2_task_output.json>
The task output file is the {summary,agentCount,logs,result} wrapper; we read .result.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WF_PATH = HERE / "workflow_result.json"

r2_path = Path(sys.argv[1])
wrapper = json.load(open(r2_path))
r2 = wrapper["result"] if "result" in wrapper else wrapper

wf = json.load(open(WF_PATH))
existing_names = {a["name"] for a in wf["approaches"]}

# 1. append added families (verdict-kept)
added = r2.get("added", [])
n_added = 0
for a in added:
    if a["name"] in existing_names:
        continue
    wf["approaches"].append(a)
    existing_names.add(a["name"])
    n_added += 1

# 2. apply corrections to synthesized gold-corr / volatility
corr = r2.get("correction", {})
by_name = {a["name"]: a for a in wf["approaches"]}
n_corr = 0
for c in corr.get("corrected_rows", []):
    a = by_name.get(c["name"])
    if not a:
        print(f"  WARN: corrected row name not matched: {c['name']!r}")
        continue
    changed = []
    if c.get("corr_gold", "").strip():
        a["synthesized_outputs"]["corr_gold"] = c["corr_gold"]
        changed.append("corr_gold")
    if c.get("volatility", "").strip():
        a["synthesized_outputs"]["volatility"] = c["volatility"]
        changed.append("vol")
    if changed:
        n_corr += 1
        a.setdefault("verdict", {})
        notes = a["verdict"].get("issues", [])
        notes.append(f"Round-2 correction ({'/'.join(changed)}): {c.get('reason','')}")
        a["verdict"]["issues"] = notes

# 3. house view + citation corrections into completeness
comp = wf.setdefault("completeness", {})
if corr.get("house_view"):
    comp["house_view"] = corr["house_view"]
if corr.get("citation_fixes"):
    comp["citation_corrections"] = corr["citation_fixes"]

json.dump(wf, open(WF_PATH, "w"), indent=2, ensure_ascii=False)
print(f"merged: +{n_added} families (now {len(wf['approaches'])} total), "
      f"{n_corr} rows corrected, {len(corr.get('citation_fixes',[]))} citation fixes, "
      f"house_view={'set' if comp.get('house_view') else 'none'}")
