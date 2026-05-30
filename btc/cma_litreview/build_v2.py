#!/usr/bin/env python3
"""
build_v2.py — merge the BTC v2 workflow (evaluate + breadth + medium explanations + scoring +
ranking + signal map) into the v1 20-approach base, then regenerate NOTES.md + dashboard.html.

BTC twin of gold/cma_litreview/build_v2.py.

Reads:  approaches_table_v1_backup.json  (v1: the 20 existing full records)
        v2_result.json                   (v2 workflow output)
        empirical_anchor.json
Writes: approaches_table.json   (merged records + ranking/scores/clusters/signal)
        NOTES.md
        dashboard.html

Reproducible. Numbers parsed from synthesized prose (transparent), never hand-typed.
Charts obey: no black ink, no curves, dots on every data point.
"""
from __future__ import annotations
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = json.load(open(HERE / "approaches_table_v1_backup.json"))
V2 = json.load(open(HERE / "v2_result.json"))
ANCHOR = json.load(open(HERE / "empirical_anchor.json"))

SRC_LABEL = {"academia": "Academia", "asset_manager": "Asset manager", "official_sector": "Official sector",
             "sell_side": "Sell-side", "practitioner": "Practitioner", "crypto_native": "Crypto-native"}

# ---------- number parsing (transparent representative midpoints) ----------
_PCT_RANGE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:to|–|-|—|~)\s*(-?\d+(?:\.\d+)?)\s*%")
_PCT_ONE = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")
_POINT = re.compile(r"point\s*~?\s*(-?\d+(?:\.\d+)?)\s*%")
_CORR_RANGE = re.compile(r"([+-]?[01]?\.\d+)\s*(?:to|–|-|—)\s*([+-]?[01]?\.\d+)")
_CORR_ONE = re.compile(r"([+-]?[01]?\.\d+)")


def parse_pct(text, prefer_band=None):
    if not text:
        return None
    t = text.replace("−", "-")
    m = _POINT.search(t)
    if m and prefer_band is None:
        return float(m.group(1))
    cands = [round((float(a) + float(b)) / 2, 2) for a, b in (mm.groups() for mm in _PCT_RANGE.finditer(t))]
    if not cands:
        cands = [float(mm.group(1)) for mm in _PCT_ONE.finditer(t)]
    if not cands:
        return None
    if prefer_band:
        lo, hi = prefer_band
        inband = [c for c in cands if lo <= c <= hi]
        if inband:
            return inband[0]
    return float(m.group(1)) if m else cands[0]


def parse_corr(text):
    if not text:
        return None
    t = text.replace("−", "-")
    if re.search(r"\bn/?a\b", t, re.I) and not _CORR_ONE.search(t):
        return None
    m = _CORR_RANGE.search(t)
    if m:
        return round((float(m.group(1)) + float(m.group(2))) / 2, 2)
    m = _CORR_ONE.search(t)
    if m:
        v = float(m.group(1))
        if -1.0 <= v <= 1.0:
            return v
    if re.search(r"\bzero\b|\bflat\b|~?\s*0\b", t):
        return 0.0
    tl = t.lower()
    sign = -1 if "negative" in tl else (1 if "positive" in tl else None)
    if sign is not None:
        if "low-to-mod" in tl or "low to mod" in tl or "modest" in tl:
            mag = 0.30
        elif "strong" in tl or "high" in tl:
            mag = 0.55
        elif "moderate" in tl:
            mag = 0.40
        elif "low" in tl or "weak" in tl or "slight" in tl:
            mag = 0.15
        else:
            mag = 0.25
        return round(sign * mag, 2)
    return None


def parsed_of(syn):
    return {
        "appr_real": parse_pct(syn.get("appreciation_real")),
        "appr_nom": parse_pct(syn.get("appreciation_nominal")),
        "vol": parse_pct(syn.get("volatility"), prefer_band=(20, 130)),
        "corr_growth": parse_corr(syn.get("corr_growth_eq")),
        "corr_value": parse_corr(syn.get("corr_value_eq")),
        "corr_fi": parse_corr(syn.get("corr_fi_nominal")),
        "corr_tips": parse_corr(syn.get("corr_tips")),
        "corr_gold": parse_corr(syn.get("corr_gold")),
    }


def norm(s):
    return " ".join((s or "").lower().split())[:60]


# ---------- merge into a single records list ----------
evalByIdx = {e["index"]: e for e in V2["existing_evals"]}
rankByName = {norm(x["name"]): x for x in V2["ranking"]}
scoreByName = {norm(x["name"]): x for x in V2["scores"]}

records = []

# existing 20 (full v1 records + v2 medium + v2 review)
for i, a in enumerate(V1["approaches"]):
    rec = dict(a)
    ev = evalByIdx.get(i, {})
    rec["medium_explanation"] = ev.get("medium_explanation") or a.get("description", "")
    rec["v2_review"] = {"quality_score": ev.get("quality_score"), "is_distinct": ev.get("is_distinct"),
                        "issues": ev.get("issues", []), "corrections": ev.get("corrections", "")}
    rec["origin"] = "existing"
    records.append(rec)

# new approaches
for a in V2["new_approaches"]:
    rec = {
        "name": a["name"], "family": a.get("family", ""), "source_type": a.get("source_type", ""),
        "source_label": SRC_LABEL.get(a.get("source_type", ""), a.get("source_type", "")),
        "description": a.get("description", ""), "medium_explanation": a.get("medium_explanation", ""),
        "key_drivers": a.get("key_drivers", []), "pros": a.get("pros", []), "cons": a.get("cons", []),
        "representative_sources": a.get("representative_sources", []),
        "cited_outputs": a.get("cited_outputs", {}), "synthesized_outputs": a.get("synthesized_outputs", {}),
        "rich_notes": a.get("rich_notes", ""), "verdict": a.get("verdict", {}),
        "parsed": parsed_of(a.get("synthesized_outputs", {})), "origin": "new",
    }
    records.append(rec)

# attach ranking + scores
for rec in records:
    rk = rankByName.get(norm(rec["name"]))
    rec["rank"] = rk["rank"] if rk else None
    rec["tier"] = rk["tier"] if rk else "Unranked"
    rec["overall"] = rk["overall"] if rk else None
    rec["orthogonality"] = rk["orthogonality"] if rk else None
    rec["rank_verdict"] = rk["verdict"] if rk else ""
    sc = scoreByName.get(norm(rec["name"]))
    rec["scores"] = {k: sc[k] for k in ("rigor", "signal", "robustness", "data_ops", "rationale")} if sc else None

# Guard: the adjudicator must rank every record by verbatim name. If any record is
# unmatched (renamed/dropped/placeholder injected upstream), fail loudly rather than
# silently shipping a broken leaderboard — closes the detection gap.
unmatched = [r["name"] for r in records if r["rank"] is None]
orphan_ranks = [x["name"] for x in V2["ranking"] if norm(x["name"]) not in {norm(r["name"]) for r in records}]
if unmatched:
    print(f"  ⚠ {len(unmatched)} record(s) not matched by the ranking: {unmatched}")
    if orphan_ranks:
        print(f"  ⚠ ranking entries matching no record (likely upstream rename/placeholder): {orphan_ranks}")
    raise SystemExit("Refusing to build: ranking is incomplete. Re-run the adjudicator with verbatim names.")

records.sort(key=lambda r: (r["rank"] is None, r["rank"] if r["rank"] is not None else 9999, r["name"]))

HOUSE_VIEW = V1.get("completeness", {}).get("house_view", "")
COMBINED = {
    "approaches": records, "anchor": ANCHOR, "house_view": HOUSE_VIEW,
    "clusters": V2.get("clusters", []), "ensemble_recommendation": V2.get("ensemble_recommendation", ""),
    "signal_notes": V2.get("signal_notes", ""), "still_missing": V2.get("still_missing", []),
    "breadth_assessment": V2.get("breadth_assessment", ""),
    "completeness_v1": V1.get("completeness", {}),
    "total": len(records),
}
json.dump(COMBINED, open(HERE / "approaches_table.json", "w"), indent=2, ensure_ascii=False)
print(f"merged {len(records)} approaches ({len(V1['approaches'])} existing + {len(V2['new_approaches'])} new)")

# ============================ NOTES.md ============================
fw = ANCHOR["full_window"]
t10 = ANCHOR["trailing_10y"]
t5 = ANCHOR["trailing_5y"]
TIER_ORDER = ["Core driver", "Conditioning overlay", "Context / cross-check", "Reject as engine", "Unranked"]


def fmtp(v, d=1):
    return "—" if v is None else f"{v:+.{d}f}%"


def fmtc(v):
    return "—" if v is None else f"{v:+.2f}"


def mo(o):
    return (f"{o.get('appreciation_nominal','')} | {o.get('appreciation_real','')} | {o.get('volatility','')} | "
            f"{o.get('corr_growth_eq','')} | {o.get('corr_value_eq','')} | {o.get('corr_fi_nominal','')} | "
            f"{o.get('corr_tips','')} | {o.get('corr_gold','')}")


L = []
L.append("# Bitcoin CMA — Literature Review v2 (10–15 year horizon)\n")
L.append("**Master working document.** Rich, retained detail lives here; `dashboard.html` is the distilled interactive "
         "view. Regenerate both with `python3 build_v2.py`.\n")
L.append(f"- **Coverage:** {len(records)} distinct approaches ({len(V1['approaches'])} from v1 + "
         f"{len(V2['new_approaches'])} added by a 12-lens divergent-breadth sweep), each scored on rigor / signal / "
         "robustness / data-ops and ranked into a tiered leaderboard, with a driver-cluster signal map exposing redundancy.\n")
L.append("- **Outputs per approach:** appreciation (nominal + real), volatility, and correlation vs growth equities, "
         "value equities, nominal fixed income, TIPS, and GOLD — cited vs synthesized, anchored to the scripted baseline.\n")
L.append("- **Gold twin:** `../../gold/cma_litreview/NOTES.md`.\n")
L.append("\n---\n")

# empirical baseline
L.append("## Empirical baseline (scripted — `empirical_anchor.py`)\n")


def wrow(w):
    return (f"BTC **{w['btc_appreciation_nominal_annual']*100:+.0f}%/yr nom**, "
            f"**{w.get('btc_appreciation_real_annual',0)*100:+.0f}%/yr real**, vol **{w['btc_vol_annual']*100:.0f}%**")


L.append(f"- Full ({fw['btc_first_month']}…{fw['btc_last_month']}): {wrow(fw)}")
L.append(f"- Trailing 10y: {wrow(t10)}")
L.append(f"- Trailing 5y: {wrow(t5)}\n")
L.append("\n> The appreciation DECAY (142→65→17%/yr) dominates every forward CMA; a method's value is mostly the "
         "conditioning it adds (tails, regime, correlation), not its level forecast. BTC–gold correlation is ~0.\n")
L.append("\n---\n")

# leaderboard
L.append("## My ranking (analyst) — full leaderboard\n")
L.append("Scored on rigor / signal / robustness / data-ops (1–5 each); **overall** weights signal & robustness most "
         "for a long-horizon CMA; **orth** = independent signal added vs the rest of the field.\n")
L.append("\n| Rank | Approach | Tier | Overall | Orth | Rig | Sig | Rob | Ops | Verdict |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for r in records:
    s = r.get("scores") or {}
    L.append(f"| {r['rank'] if r['rank'] else '—'} | {r['name'].replace('|','/')} | {r['tier']} | "
             f"{r['overall'] if r['overall'] is not None else '—'} | {r['orthogonality'] if r['orthogonality'] is not None else '—'} | "
             f"{s.get('rigor','—')} | {s.get('signal','—')} | {s.get('robustness','—')} | {s.get('data_ops','—')} | "
             f"{(r.get('rank_verdict','') or '').replace('|','/')} |")
L.append("\n---\n")

# signal map
L.append("## Signal map — driver clusters (exposes redundancy)\n")
L.append("Approaches grouped by the underlying variable they ultimately rest on. Many 'distinct' approaches reduce to "
         "the same driver — the marginal information is in spanning clusters, not counting approaches.\n")
for c in V2.get("clusters", []):
    L.append(f"\n**{c.get('cluster_name','')}** — _{c.get('shared_driver','')}_")
    for m in c.get("members", []):
        L.append(f"  - {m}")
L.append("\n### Recommended orthogonal ensemble\n")
L.append(V2.get("ensemble_recommendation", "") + "\n")
L.append("\n### Signal notes\n")
L.append(V2.get("signal_notes", "") + "\n")
L.append("\n---\n")

# comparison table with medium explanation
L.append("## Comparison table — approaches (with medium Explanation)\n")
L.append("\n| Rank | Approach | Source | Explanation (medium) | Pros | Cons | Key drivers |")
L.append("|---|---|---|---|---|---|---|")
for r in records:
    pros = "<br>".join("• " + p for p in r["pros"])
    cons = "<br>".join("• " + c for c in r["cons"])
    drv = "<br>".join("• " + d for d in r["key_drivers"])
    expl = (r.get("medium_explanation", "") or "").replace("|", "/").replace("\n", " ")
    flag = " ⚠" if r.get("verdict", {}).get("numbers_credible") is False else ""
    L.append(f"| {r['rank'] if r['rank'] else '—'}{flag} | {r['name'].replace('|','/')} | {r['source_label']} | "
             f"{expl} | {pros} | {cons} | {drv} |")
L.append("\n---\n")

# outputs matrix
L.append("## Outputs matrix — synthesized 10–15yr (representative midpoints)\n")
L.append("\n| Rank | Approach | Appr real | Appr nom | Vol | ρ GrEq | ρ VaEq | ρ FI | ρ TIPS | ρ Gold |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for r in records:
    p = r["parsed"]
    L.append(f"| {r['rank'] if r['rank'] else '—'} | {r['name'][:46].replace('|','/')} | {fmtp(p['appr_real'])} | "
             f"{fmtp(p['appr_nom'])} | {('%.0f%%'%p['vol']) if p['vol'] is not None else '—'} | {fmtc(p['corr_growth'])} | "
             f"{fmtc(p['corr_value'])} | {fmtc(p['corr_fi'])} | {fmtc(p['corr_tips'])} | {fmtc(p['corr_gold'])} |")
L.append("\n---\n")

# per-approach detail
L.append("## Approach detail\n")
for r in records:
    L.append(f"\n### {('#'+str(r['rank'])+' · ') if r['rank'] else ''}{r['name']}\n")
    L.append(f"*Family: {r['family']} · Source: {r['source_label']} · Tier: {r['tier']}"
             f"{' · Overall '+str(r['overall']) if r['overall'] is not None else ''}*\n")
    L.append(f"\n**Explanation:** {r.get('medium_explanation','')}\n")
    s = r.get("scores")
    if s:
        L.append(f"\n*Scores — rigor {s['rigor']}, signal {s['signal']}, robustness {s['robustness']}, "
                 f"data-ops {s['data_ops']}, orthogonality {r['orthogonality']}. {s.get('rationale','')}*\n")
    L.append("\n**Key drivers:** " + "; ".join(r["key_drivers"]))
    L.append("\n\n**Pros:** " + "; ".join(r["pros"]))
    L.append("\n\n**Cons:** " + "; ".join(r["cons"]))
    v = r.get("verdict", {})
    if v.get("numbers_credible") is False:
        L.append(f"\n\n> **⚠ Adversarial verifier — numbers unreliable.** {v.get('corrections','')}")
    vr = r.get("v2_review", {})
    if vr.get("corrections") and str(vr["corrections"]).strip().lower() not in ("none", "[]", ""):
        L.append(f"\n\n> **v2 evaluation (quality {vr.get('quality_score','?')}/5):** {str(vr['corrections'])[:600]}")
    L.append("\n\n**Outputs (cited vs synthesized):**\n")
    L.append("\n| | Appr nom | Appr real | Vol | ρ GrEq | ρ VaEq | ρ FI | ρ TIPS | ρ Gold |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    L.append("| Cited | " + mo(r["cited_outputs"]) + " |")
    L.append("| Synthesized | " + mo(r["synthesized_outputs"]) + " |")
    if r.get("representative_sources"):
        L.append("\n**Sources:** " + "; ".join(
            f"{s.get('author_firm','')} ({s.get('year','')})" + (f" {s.get('link')}" if s.get('link') else "")
            for s in r["representative_sources"][:6]))
    if r.get("rich_notes"):
        L.append(f"\n\n<details><summary>Full notes</summary>\n\n{r['rich_notes']}\n\n</details>\n")
    L.append("\n---")

# synthesis
L.append("\n## Cross-approach synthesis\n")
L.append("### House view (analyst)\n" + HOUSE_VIEW + "\n")
L.append("\n### Breadth assessment (completeness critic)\n" + V2.get("breadth_assessment", "") + "\n")
if V2.get("still_missing"):
    L.append("\n### Known remaining families (identified, not yet deep-dived)\n")
    for m in V2["still_missing"]:
        L.append(f"- **{m.get('name','')}** — {m.get('why','')}")

(HERE / "NOTES.md").write_text("\n".join(L))
print("wrote NOTES.md")

# ============================ dashboard.html ============================
PALETTE = {"academia": "#2b6cb0", "asset_manager": "#2f855a", "official_sector": "#6b46c1",
           "sell_side": "#c05621", "practitioner": "#b7791f", "crypto_native": "#b83280"}
TIER_COLOR = {"Core driver": "#2f855a", "Conditioning overlay": "#2b6cb0",
              "Context / cross-check": "#b7791f", "Reject as engine": "#c05621", "Unranked": "#8a97a3"}

rows_json = json.dumps([{
    "rank": r["rank"], "name": r["name"], "family": r["family"], "source_type": r["source_type"],
    "source_label": r["source_label"], "tier": r["tier"], "overall": r["overall"],
    "orthogonality": r["orthogonality"], "rank_verdict": r.get("rank_verdict", ""),
    "scores": r.get("scores"), "origin": r["origin"], "medium": r.get("medium_explanation", ""),
    "description": r["description"], "key_drivers": r["key_drivers"], "pros": r["pros"], "cons": r["cons"],
    "cited": r["cited_outputs"], "syn": r["synthesized_outputs"], "sources": r["representative_sources"],
    "parsed": r["parsed"], "verdict": r.get("verdict", {}), "v2_review": r.get("v2_review", {}),
    "rich": r["rich_notes"],
} for r in records], ensure_ascii=False)

scatter_pts = json.dumps([{"x": r["parsed"]["vol"], "y": r["parsed"]["appr_nom"], "label": r["name"],
                           "src": r["source_type"], "tier": r["tier"]}
                          for r in records if r["parsed"]["vol"] is not None and r["parsed"]["appr_nom"] is not None],
                         ensure_ascii=False)
anchor_pts = json.dumps([{"x": round(ANCHOR[w]["btc_vol_annual"] * 100, 1),
                          "y": round(ANCHOR[w]["btc_appreciation_nominal_annual"] * 100, 1), "label": lab}
                         for w, lab in [("full_window", "Realized full"), ("trailing_10y", "Realized 10y"),
                                        ("trailing_5y", "Realized 5y")]], ensure_ascii=False)
clusters_json = json.dumps(V2.get("clusters", []), ensure_ascii=False)
meta_json = json.dumps({
    "anchor": ANCHOR, "ensemble": V2.get("ensemble_recommendation", ""), "signal_notes": V2.get("signal_notes", ""),
    "house_view": HOUSE_VIEW, "breadth": V2.get("breadth_assessment", ""), "still_missing": V2.get("still_missing", []),
    "n_existing": len(V1["approaches"]), "n_new": len(V2["new_approaches"]), "total": len(records),
}, ensure_ascii=False)
pal_json = json.dumps(PALETTE, ensure_ascii=False)
tiercol_json = json.dumps(TIER_COLOR, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bitcoin CMA — Literature Review v2</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--ink:#1a2733;--bg:#f7f9fb;--card:#fff;--line:#dde5ec;--muted:#5a6b7a;--btc:#f7931a;}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{background:linear-gradient(120deg,#11212e,#1f3a4d);color:#fff;padding:24px 28px}
header h1{margin:0 0 6px;font-size:23px}
header p{margin:3px 0;color:#c8d6e0;font-size:13.5px;max-width:1050px}
.wrap{max-width:1320px;margin:0 auto;padding:20px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0 12px}
.tab{padding:8px 15px;border:1px solid var(--line);background:var(--card);border-radius:7px;cursor:pointer;font-weight:600;font-size:13.5px}
.tab.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.panel{display:none}.panel.active{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin:14px 0}
.kpis{display:flex;gap:12px;flex-wrap:wrap}
.kpi{flex:1;min-width:140px;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:12px}
.kpi .v{font-size:20px;font-weight:700}.kpi .l{font-size:12px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:#eef3f7;cursor:pointer;position:sticky;top:0;z-index:1}
th.s-asc::after{content:" ▲"}th.s-desc::after{content:" ▼"}
tr.approw{cursor:pointer}tr.approw:hover{background:#f0f6fb}
.chip{display:inline-block;padding:2px 7px;border-radius:11px;color:#fff;font-size:10.5px;font-weight:600;white-space:nowrap}
.tierchip{display:inline-block;padding:2px 8px;border-radius:6px;color:#fff;font-size:11px;font-weight:600}
.detail{background:#fbfdff;border-left:3px solid var(--btc)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.cols h4{margin:6px 0 4px;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
ul{margin:4px 0 10px;padding-left:18px}li{margin:2px 0}
.flag{color:#c05621;font-weight:700}
.muted{color:var(--muted);font-size:12.5px}
details{margin-top:8px}summary{cursor:pointer;font-weight:600;color:var(--muted)}
.outtab td:first-child{font-weight:600;background:#f2f7fb}
.bar{height:8px;border-radius:4px;background:#e6edf3;display:inline-block;vertical-align:middle;width:60px;position:relative;overflow:hidden}
.bar>i{position:absolute;left:0;top:0;bottom:0;background:var(--btc);display:block}
.note{background:#fff8ec;border:1px solid #f0dcb8;border-radius:8px;padding:12px;font-size:13px;margin:10px 0}
.clcard{border:1px solid var(--line);border-radius:9px;padding:12px;margin:8px 0;background:#fff}
.clcard h4{margin:0 0 4px}
canvas{max-width:100%}
a{color:#2b6cb0}
@media(max-width:820px){.cols{grid-template-columns:1fr}}
</style></head>
<body>
<header>
<h1>Bitcoin Capital-Market Assumption — Literature Review v2</h1>
<p>__TOTAL__ approaches (__NEXIST__ from v1 + __NNEW__ via a 12-lens divergent-breadth sweep) for setting a <b>10–15 year</b> BTC CMA — each scored on rigor / signal / robustness / data-ops, ranked into a tiered leaderboard, and mapped into driver clusters that expose redundancy. Bitcoin has no cashflow, so it does not fit the equity building-block CMA.</p>
<p class="muted" style="color:#9fb4c2">Synthesized figures are reasoned judgments under each approach's logic, anchored to a scripted realized baseline — not computed forecasts. Source-published figures are cited where they exist.</p>
</header>
<div class="wrap">
<div class="tabs" id="tabs"></div>
<div id="p-overview" class="panel active"></div>
<div id="p-leaderboard" class="panel"></div>
<div id="p-signal" class="panel"></div>
<div id="p-approaches" class="panel"></div>
<div id="p-outputs" class="panel"></div>
<div id="p-baseline" class="panel"></div>
<div id="p-synth" class="panel"></div>
</div>
<script>
const ROWS=__ROWS__, SCATTER=__SCATTER__, ANCHORPTS=__ANCHORPTS__, CLUSTERS=__CLUSTERS__, M=__META__, PAL=__PAL__, TC=__TIERCOL__;
const A=M.anchor;
function esc(s){return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function chip(st,l){return `<span class="chip" style="background:${PAL[st]||'#789'}">${esc(l)}</span>`;}
function tchip(t){return `<span class="tierchip" style="background:${TC[t]||'#789'}">${esc(t)}</span>`;}
function pct(v,d=0){return v==null?'—':(v>=0?'+':'')+v.toFixed(d)+'%';}
function cor(v){return v==null?'—':(v>=0?'+':'')+v.toFixed(2);}
function bar(v){return `<span class="bar"><i style="width:${(v/5*100)||0}%"></i></span> ${v??'—'}`;}

const TABS=[['overview','Overview'],['leaderboard','Leaderboard'],['signal','Signal map'],['approaches','Approaches'],['outputs','Outputs'],['baseline','Empirical baseline'],['synth','Synthesis']];
const tabsEl=document.getElementById('tabs');
TABS.forEach(([k,l],idx)=>{const b=document.createElement('div');b.className='tab'+(idx===0?' active':'');b.textContent=l;b.onclick=()=>{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));b.classList.add('active');
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.getElementById('p-'+k).classList.add('active');
  if(k==='overview')drawScatter();if(k==='baseline')drawBaseline();if(k==='leaderboard')drawTierChart();
};tabsEl.appendChild(b);});

/* ---------- overview ---------- */
function w(x){return A[x];}
const tierCounts={};ROWS.forEach(r=>tierCounts[r.tier]=(tierCounts[r.tier]||0)+1);
document.getElementById('p-overview').innerHTML=`
<div class="card"><h2 style="margin-top:0">The decay is the story</h2>
<div class="kpis">
 <div class="kpi"><div class="v">${M.total}</div><div class="l">approaches scored &amp; ranked</div></div>
 <div class="kpi"><div class="v">${pct(w('full_window').btc_appreciation_nominal_annual*100)}</div><div class="l">realized nom — full</div></div>
 <div class="kpi"><div class="v">${pct(w('trailing_10y').btc_appreciation_nominal_annual*100)}</div><div class="l">realized — 10y</div></div>
 <div class="kpi"><div class="v">${pct(w('trailing_5y').btc_appreciation_nominal_annual*100)}</div><div class="l">realized — 5y</div></div>
 <div class="kpi"><div class="v">${(w('trailing_5y').btc_vol_annual*100).toFixed(0)}%</div><div class="l">realized vol — 5y</div></div>
 <div class="kpi"><div class="v">${tierCounts['Core driver']||0}</div><div class="l">Core-driver tier</div></div>
</div>
<div class="note">Realized BTC appreciation collapses as the asset matures (${(w('full_window').btc_appreciation_nominal_annual*100).toFixed(0)}% → ${(w('trailing_10y').btc_appreciation_nominal_annual*100).toFixed(0)}% → ${(w('trailing_5y').btc_appreciation_nominal_annual*100).toFixed(0)}%/yr). The decay anchor — not any single model — drives every forward number; a method's value is mostly the conditioning it adds (tails, regime, correlation). BTC–gold correlation is ~0.</div></div>
<div class="card"><h3 style="margin-top:0">Synthesized 10–15yr appreciation vs volatility</h3>
<p class="muted">Each dot = one approach. Squares = scripted realized BTC (full / 10y / 5y). Color = source type.</p>
<canvas id="scatter" height="150"></canvas></div>`;

let scatterChart;
function drawScatter(){if(scatterChart)return;
  const bySrc={};SCATTER.forEach(p=>{(bySrc[p.src]=bySrc[p.src]||[]).push(p);});
  const ds=Object.entries(bySrc).map(([st,pts])=>({label:st,data:pts,backgroundColor:PAL[st]||'#789',pointRadius:5,pointHoverRadius:8,showLine:false}));
  ds.push({label:'Realized BTC',data:ANCHORPTS,backgroundColor:'#f7931a',pointStyle:'rectRot',pointRadius:9,pointHoverRadius:12,showLine:false});
  scatterChart=new Chart(document.getElementById('scatter'),{type:'scatter',data:{datasets:ds},options:{plugins:{legend:{position:'bottom'},tooltip:{callbacks:{label:c=>`${c.raw.label}: ${c.raw.y>=0?'+':''}${c.raw.y.toFixed(0)}% appr, ${c.raw.x.toFixed(0)}% vol`}}},scales:{x:{title:{display:true,text:'Annualized volatility (%)'},grid:{color:'#eef'}},y:{title:{display:true,text:'Nominal appreciation (%/yr)'},grid:{color:'#eef'}}}}});
}
setTimeout(drawScatter,60);

/* ---------- leaderboard ---------- */
let lsort='rank',ldir=1;
function drawTierChart(){if(document.getElementById('tierc').dataset.done)return;document.getElementById('tierc').dataset.done=1;
  const order=['Core driver','Conditioning overlay','Context / cross-check','Reject as engine','Unranked'];
  const counts=order.map(t=>ROWS.filter(r=>r.tier===t).length);
  new Chart(document.getElementById('tierc'),{type:'bar',data:{labels:order,datasets:[{label:'approaches',data:counts,backgroundColor:order.map(t=>TC[t]||'#789')}]},options:{plugins:{legend:{display:false}},scales:{y:{grid:{color:'#eef'},ticks:{precision:0}},x:{grid:{display:false}}}}});
}
function renderLeader(){
  const cols=[['rank','#'],['name','Approach'],['tier','Tier'],['overall','Overall'],['orthogonality','Orth'],['rigor','Rig'],['signal','Sig'],['robustness','Rob'],['data_ops','Ops']];
  let h='<div class="card"><h3 style="margin-top:0">Analyst leaderboard</h3><p class="muted">Scored 1–5 per dimension; overall (0–100) weights signal &amp; robustness most for a long-horizon CMA. Click a header to sort, a row to expand.</p><canvas id="tierc" height="60" style="margin-bottom:14px"></canvas><table id="lt"><thead><tr>';
  cols.forEach(([k,l])=>{h+=`<th data-k="${k}" class="${lsort===k?(ldir>0?'s-asc':'s-desc'):''}">${l}</th>`;});
  h+='<th>Verdict</th></tr></thead><tbody>';
  const sv=k=>r=>{if(['rigor','signal','robustness','data_ops'].includes(k))return (r.scores||{})[k]??-1;const v=r[k];return v==null?(k==='name'?'zzz':-1):v;};
  const sorted=[...ROWS].sort((a,b)=>{const va=sv(lsort)(a),vb=sv(lsort)(b);return(va>vb?1:va<vb?-1:0)*ldir;});
  sorted.forEach(r=>{const s=r.scores||{};const flag=r.verdict&&r.verdict.numbers_credible===false?' <span class="flag">⚠</span>':'';
    h+=`<tr class="approw" data-n="${esc(r.name)}"><td>${r.rank??'—'}</td><td>${esc(r.name)}${flag} ${r.origin==='new'?'<span class="chip" style="background:#b83280">new</span>':''}</td><td>${tchip(r.tier)}</td><td><b>${r.overall??'—'}</b></td><td>${r.orthogonality??'—'}</td><td>${bar(s.rigor)}</td><td>${bar(s.signal)}</td><td>${bar(s.robustness)}</td><td>${bar(s.data_ops)}</td><td class="muted">${esc(r.rank_verdict)}</td></tr>`;
    h+=`<tr data-d="${esc(r.name)}" style="display:none"><td colspan="10" class="detail">${detail(r)}</td></tr>`;});
  h+='</tbody></table></div>';
  document.getElementById('p-leaderboard').innerHTML=h;
  document.querySelectorAll('#lt th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(k===lsort)ldir*=-1;else{lsort=k;ldir=k==='name'?1:-1;}renderLeader();drawTierChart();});
  bindRows('#lt');document.getElementById('tierc').dataset.done='';drawTierChart();
}
function bindRows(scope){document.querySelectorAll(scope+' tr.approw').forEach(tr=>tr.onclick=()=>{const d=document.querySelector(scope+` tr[data-d="${CSS.escape(tr.dataset.n)}"]`);if(d)d.style.display=d.style.display==='none'?'':'none';});}

/* ---------- approaches (by source) ---------- */
let asort='rank',adir=1;
function renderApproaches(){
  const cols=[['rank','#'],['name','Approach'],['family','Family'],['source_type','Source'],['tier','Tier'],['appr_nom','Appr'],['vol','Vol'],['corr_gold','ρGold']];
  let h='<div class="card"><p class="muted">All __TOTAL__ approaches with the medium explanation on expand. Click a row for the full deep-dive.</p><table id="at"><thead><tr>';
  cols.forEach(([k,l])=>{h+=`<th data-k="${k}" class="${asort===k?(adir>0?'s-asc':'s-desc'):''}">${l}</th>`;});
  h+='</tr></thead><tbody>';
  const sv=k=>r=>{if(['appr_nom','vol','corr_gold'].includes(k))return r.parsed[k]??-1e9;const v=r[k];return v==null?(k==='name'||k==='family'?'zzz':-1):v;};
  const sorted=[...ROWS].sort((a,b)=>{const va=sv(asort)(a),vb=sv(asort)(b);return(va>vb?1:va<vb?-1:0)*adir;});
  sorted.forEach(r=>{const flag=r.verdict&&r.verdict.numbers_credible===false?' <span class="flag">⚠</span>':'';
    h+=`<tr class="approw" data-n="${esc(r.name)}"><td>${r.rank??'—'}</td><td>${esc(r.name)}${flag} ${r.origin==='new'?'<span class="chip" style="background:#b83280">new</span>':''}</td><td>${esc(r.family)}</td><td>${chip(r.source_type,r.source_label)}</td><td>${tchip(r.tier)}</td><td>${pct(r.parsed.appr_nom)}</td><td>${r.parsed.vol==null?'—':r.parsed.vol.toFixed(0)+'%'}</td><td>${cor(r.parsed.corr_gold)}</td></tr>`;
    h+=`<tr data-d="${esc(r.name)}" style="display:none"><td colspan="8" class="detail">${detail(r)}</td></tr>`;});
  h+='</tbody></table></div>';
  document.getElementById('p-approaches').innerHTML=h;
  document.querySelectorAll('#at th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(k===asort)adir*=-1;else{asort=k;adir=k==='name'||k==='family'?1:-1;}renderApproaches();});
  bindRows('#at');
}
function outRow(lab,o){return `<tr><td>${lab}</td><td>${esc(o.appreciation_nominal)||'—'}</td><td>${esc(o.appreciation_real)||'—'}</td><td>${esc(o.volatility)||'—'}</td><td>${esc(o.corr_growth_eq)||'—'}</td><td>${esc(o.corr_value_eq)||'—'}</td><td>${esc(o.corr_fi_nominal)||'—'}</td><td>${esc(o.corr_tips)||'—'}</td><td>${esc(o.corr_gold)||'—'}</td></tr>`;}
function detail(r){const v=r.verdict||{},s=r.scores||{},vr=r.v2_review||{};
  let vbox=v.numbers_credible===false?`<div class="note"><b class="flag">⚠ Adversarial verifier.</b> ${esc(v.corrections)}<ul>${(v.issues||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`:'';
  let v2box=(vr.corrections&&String(vr.corrections).toLowerCase()!=='none'&&String(vr.corrections)!=='')?`<div class="muted">v2 eval (quality ${vr.quality_score??'?'}/5): ${esc(vr.corrections)}</div>`:'';
  let scoreline=s.rigor?`<p class="muted">Scores — rigor ${s.rigor}, signal ${s.signal}, robustness ${s.robustness}, data-ops ${s.data_ops}, orthogonality ${r.orthogonality}. ${esc(s.rationale)}</p>`:'';
  return `<h3>${r.rank?('#'+r.rank+' · '):''}${esc(r.name)}</h3>
   <p class="muted">${esc(r.family)} · ${esc(r.source_label)} · ${tchip(r.tier)} ${r.overall!=null?'· Overall <b>'+r.overall+'</b>':''}</p>
   <p><b>Explanation.</b> ${esc(r.medium||r.description)}</p>${scoreline}
   <div class="cols"><div><h4>Pros</h4><ul>${r.pros.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div><div><h4>Cons</h4><ul>${r.cons.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div></div>
   <h4 class="muted">Key drivers</h4><ul>${r.key_drivers.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>${vbox}${v2box}
   <h4 class="muted">Outputs — cited vs synthesized</h4>
   <table class="outtab"><thead><tr><th></th><th>Appr nom</th><th>Appr real</th><th>Vol</th><th>ρ GrEq</th><th>ρ VaEq</th><th>ρ FI</th><th>ρ TIPS</th><th>ρ Gold</th></tr></thead><tbody>${outRow('Cited',r.cited)}${outRow('Synthesized',r.syn)}</tbody></table>
   <h4 class="muted">Sources</h4><ul>${(r.sources||[]).map(x=>`<li>${esc(x.author_firm)}, <i>${esc(x.title)}</i> (${esc(x.year)})${x.link?` — <a href="${esc(x.link)}" target="_blank" rel="noopener">link</a>`:''}</li>`).join('')}</ul>
   ${r.rich?`<details><summary>Full notes</summary><p class="muted" style="white-space:pre-wrap">${esc(r.rich)}</p></details>`:''}`;
}

/* ---------- signal map ---------- */
(function(){let h='<div class="card"><h3 style="margin-top:0">Driver clusters — where the redundancy is</h3><p class="muted">Approaches grouped by the underlying variable they ultimately rest on. The marginal information is in spanning clusters, not counting approaches.</p>';
  CLUSTERS.forEach(c=>{h+=`<div class="clcard"><h4>${esc(c.cluster_name)} <span class="muted">(${(c.members||[]).length})</span></h4><p class="muted">${esc(c.shared_driver)}</p><ul>${(c.members||[]).map(m=>`<li>${esc(m)}</li>`).join('')}</ul></div>`;});
  h+='</div>';
  if(M.ensemble)h+=`<div class="card" style="border-left:4px solid var(--btc)"><h3 style="margin-top:0">Recommended orthogonal ensemble</h3><p>${esc(M.ensemble)}</p></div>`;
  if(M.signal_notes)h+=`<div class="card"><h3 style="margin-top:0">Signal notes</h3><p>${esc(M.signal_notes)}</p></div>`;
  document.getElementById('p-signal').innerHTML=h;
})();

/* ---------- outputs matrix ---------- */
(function(){let h='<div class="card"><h3 style="margin-top:0">Synthesized 10–15yr outputs matrix</h3><p class="muted">Representative midpoints parsed from the synthesized prose. Correlations vs growth eq / value eq / nominal FI / TIPS / gold.</p><table><thead><tr><th>#</th><th>Approach</th><th>Appr real</th><th>Appr nom</th><th>Vol</th><th>ρ GrEq</th><th>ρ VaEq</th><th>ρ FI</th><th>ρ TIPS</th><th>ρ Gold</th></tr></thead><tbody>';
  ROWS.forEach(r=>{const p=r.parsed;h+=`<tr><td>${r.rank??'—'}</td><td>${esc(r.name)}</td><td>${pct(p.appr_real)}</td><td>${pct(p.appr_nom)}</td><td>${p.vol==null?'—':p.vol.toFixed(0)+'%'}</td><td>${cor(p.corr_growth)}</td><td>${cor(p.corr_value)}</td><td>${cor(p.corr_fi)}</td><td>${cor(p.corr_tips)}</td><td>${cor(p.corr_gold)}</td></tr>`;});
  h+='</tbody></table></div>';document.getElementById('p-outputs').innerHTML=h;})();

/* ---------- baseline ---------- */
function drawBaseline(){if(document.getElementById('p-baseline').dataset.done)return;document.getElementById('p-baseline').dataset.done=1;
  const W=[['full_window','Full'],['trailing_10y','10y'],['trailing_5y','5y']];
  let h='<div class="card"><h3 style="margin-top:0">Scripted realized BTC baseline</h3>'+`<p class="muted">${esc(A.method)} ${esc(A.note)}</p>`+'<table><thead><tr><th>Window</th><th>Span</th><th>Appr nom</th><th>Appr real</th><th>Vol</th></tr></thead><tbody>';
  W.forEach(([k,l])=>{const x=A[k];h+=`<tr><td>${l}</td><td>${x.btc_first_month}…${x.btc_last_month}</td><td>${pct(x.btc_appreciation_nominal_annual*100)}</td><td>${pct((x.btc_appreciation_real_annual||0)*100)}</td><td>${(x.btc_vol_annual*100).toFixed(0)}%</td></tr>`;});
  h+='</tbody></table><h4 class="muted">Correlation of monthly BTC returns</h4><table><thead><tr><th>vs</th><th>Full</th><th>10y</th><th>5y</th></tr></thead><tbody>';
  ['growth_eq','value_eq','fi_nom','tips','gold','usd'].forEach(key=>{const f=A.full_window.correlations[key],t=A.trailing_10y.correlations[key],c=A.trailing_5y.correlations[key];if(f)h+=`<tr><td>${esc(f.label)}</td><td>${cor(f.corr)}</td><td>${t?cor(t.corr):'—'}</td><td>${c?cor(c.corr):'—'}</td></tr>`;});
  h+='</tbody></table><canvas id="declc" height="120" style="margin-top:14px"></canvas></div>';
  document.getElementById('p-baseline').innerHTML=h;
  new Chart(document.getElementById('declc'),{type:'line',data:{labels:W.map(x=>x[1]),datasets:[{label:'Nominal appr (%/yr)',data:W.map(x=>+(A[x[0]].btc_appreciation_nominal_annual*100).toFixed(1)),borderColor:'#f7931a',backgroundColor:'#f7931a',tension:0,pointRadius:6},{label:'Volatility (%)',data:W.map(x=>+(A[x[0]].btc_vol_annual*100).toFixed(1)),borderColor:'#2b6cb0',backgroundColor:'#2b6cb0',tension:0,pointRadius:6}]},options:{plugins:{legend:{position:'bottom'}},scales:{y:{grid:{color:'#eef'}},x:{grid:{color:'#eef'}}}}});
}

/* ---------- synthesis ---------- */
(function(){let h='';
  if(M.house_view)h+=`<div class="card" style="border-left:4px solid var(--btc)"><h3 style="margin-top:0">House view — honest cross-approach 10–15yr BTC CMA</h3><p>${esc(M.house_view)}</p></div>`;
  if(M.breadth)h+=`<div class="card"><h3 style="margin-top:0">Breadth assessment (completeness critic)</h3><p>${esc(M.breadth)}</p></div>`;
  if((M.still_missing||[]).length)h+=`<div class="card"><h3 style="margin-top:0">Known remaining families (identified, not yet deep-dived)</h3><ul>${M.still_missing.map(m=>`<li><b>${esc(m.name)}</b> — ${esc(m.why)}</li>`).join('')}</ul></div>`;
  document.getElementById('p-synth').innerHTML=h;})();

renderLeader();renderApproaches();
</script>
</body></html>"""

HTML = (HTML.replace("__ROWS__", rows_json).replace("__SCATTER__", scatter_pts).replace("__ANCHORPTS__", anchor_pts)
        .replace("__CLUSTERS__", clusters_json).replace("__META__", meta_json).replace("__PAL__", pal_json)
        .replace("__TIERCOL__", tiercol_json).replace("__TOTAL__", str(len(records)))
        .replace("__NEXIST__", str(len(V1["approaches"]))).replace("__NNEW__", str(len(V2["new_approaches"]))))
(HERE / "dashboard.html").write_text(HTML)
print("wrote dashboard.html")
