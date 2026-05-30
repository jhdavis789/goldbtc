#!/usr/bin/env python3
"""
build_litreview.py — assemble the Bitcoin CMA literature review deliverables from the
workflow result + the scripted empirical anchor. BTC twin of the gold builder.

Reads:  workflow_result.json   (btc-cma-litreview workflow output: taxonomy/approaches/completeness)
        empirical_anchor.json   (scripted realized baseline)
Writes: NOTES.md                (master working doc — rich, retained)
        approaches_table.json    (clean per-approach records, incl. parsed representative numbers)
        dashboard.html           (single-file interactive deliverable — built LAST, from approaches_table.json)

Number parsing: representative values for charts/matrix are PARSED from the synthesized prose
(midpoint of the first range) and always shown alongside the full prose — never hand-entered.
Chart rules obeyed in the HTML: no black ink, no curves, dots on every data point.
"""
from __future__ import annotations
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
WF = json.load(open(HERE / "workflow_result.json"))
ANCHOR = json.load(open(HERE / "empirical_anchor.json"))

SRC_LABEL = {
    "academia": "Academia", "asset_manager": "Asset manager",
    "official_sector": "Official sector", "sell_side": "Sell-side",
    "practitioner": "Practitioner", "crypto_native": "Crypto-native",
}

# ---------- number parsing (representative midpoints, transparent) ----------
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
    cands = []
    for mm in _PCT_RANGE.finditer(t):
        cands.append(round((float(mm.group(1)) + float(mm.group(2))) / 2, 2))
    if not cands:
        for mm in _PCT_ONE.finditer(t):
            cands.append(float(mm.group(1)))
    if not cands:
        return None
    if prefer_band:
        lo, hi = prefer_band
        inband = [c for c in cands if lo <= c <= hi]
        if inband:
            return inband[0]
    if m:
        return float(m.group(1))
    return cands[0]


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


# ---------- build clean per-approach records ----------
records = []
for a in WF["approaches"]:
    syn = a.get("synthesized_outputs", {})
    cit = a.get("cited_outputs", {})
    rec = {
        "name": a["name"],
        "family": a.get("family", ""),
        "source_type": a.get("source_type", ""),
        "source_label": SRC_LABEL.get(a.get("source_type", ""), a.get("source_type", "")),
        "description": a.get("description", ""),
        "key_drivers": a.get("key_drivers", []),
        "pros": a.get("pros", []),
        "cons": a.get("cons", []),
        "representative_sources": a.get("representative_sources", []),
        "cited_outputs": cit,
        "synthesized_outputs": syn,
        "rich_notes": a.get("rich_notes", ""),
        "verdict": a.get("verdict", {}),
        "parsed": {
            "appr_real": parse_pct(syn.get("appreciation_real")),
            "appr_nom": parse_pct(syn.get("appreciation_nominal")),
            "vol": parse_pct(syn.get("volatility"), prefer_band=(20, 130)),
            "corr_growth": parse_corr(syn.get("corr_growth_eq")),
            "corr_value": parse_corr(syn.get("corr_value_eq")),
            "corr_fi": parse_corr(syn.get("corr_fi_nominal")),
            "corr_tips": parse_corr(syn.get("corr_tips")),
            "corr_gold": parse_corr(syn.get("corr_gold")),
        },
    }
    records.append(rec)

json.dump({"approaches": records, "anchor": ANCHOR, "completeness": WF.get("completeness", {})},
          open(HERE / "approaches_table.json", "w"), indent=2)

# ============================ NOTES.md ============================
fw = ANCHOR["full_window"]
t10 = ANCHOR["trailing_10y"]
t5 = ANCHOR["trailing_5y"]


def md_outputs_row(label, o):
    return (f"| {label} | {o.get('appreciation_nominal','')} | {o.get('appreciation_real','')} | "
            f"{o.get('volatility','')} | {o.get('corr_growth_eq','')} | {o.get('corr_value_eq','')} | "
            f"{o.get('corr_fi_nominal','')} | {o.get('corr_tips','')} | {o.get('corr_gold','')} |")


lines = []
lines.append("# Bitcoin CMA — Literature Review (10–15 year horizon)\n")
lines.append("**Master working document.** Rich, retained detail lives here; `dashboard.html` is the distilled "
             "interactive view. Regenerate both with `python3 build_litreview.py` after re-running the workflow.\n")
lines.append("- **Purpose:** catalog the frameworks academics and practitioners use to set a 10–15-year capital-market "
             "assumption (expected appreciation, volatility, correlations) for **Bitcoin**, which has no cashflow and "
             "therefore does not fit the equity building-block CMA (CAPE + net dilution + real GDP + dividend yield + 10y yield).\n")
lines.append(f"- **Coverage:** {len(records)} distinct approaches across academia, asset managers, crypto-native analysts, "
             "and sell-side — each deep-dived and **adversarially verified** (a skeptic agent tried to refute the numbers "
             "and the pro/con framing).\n")
lines.append("- **Outputs per approach:** appreciation (nominal + real), volatility, and correlation vs **growth equities, "
             "value equities, nominal fixed income, TIPS, and GOLD** (the BTC-specific 'digital gold / gold-parity' axis), "
             "reported **both** as the source publishes (cited) and as a synthesized 10–15yr judgment anchored to the "
             "empirical baseline below.\n")
lines.append("- **Gold twin:** parallel review at `../../gold/cma_litreview/NOTES.md`.\n")
lines.append("\n---\n")

# Empirical baseline
lines.append("## Empirical baseline (scripted — `empirical_anchor.py`)\n")
lines.append("Realized history only. Anchors the synthesized column; **not** a forecast. Method: month-end levels, "
             "monthly log returns, vol = stdev(monthly)·√12, geometric annualized appreciation, real via CPIAUCSL. "
             "BTC = Coinmetrics PriceUSD (BRRNY calc-agent series); gold = LBMA PM; equities/FI/TIPS = Yahoo total "
             "return (IWF/IWD/AGG/TIP); USD = FRED DTWEXBGS.\n")


def wrow(w):
    return (f"BTC **{w['btc_appreciation_nominal_annual']*100:+.0f}%/yr nominal**, "
            f"**{w.get('btc_appreciation_real_annual',0)*100:+.0f}%/yr real**, vol **{w['btc_vol_annual']*100:.0f}%**")


lines.append(f"\n- **Full window** ({fw['btc_first_month']} … {fw['btc_last_month']}, {fw['n_months_btc']} mo): {wrow(fw)}")
lines.append(f"- **Trailing 10y** ({t10['btc_first_month']} … {t10['btc_last_month']}): {wrow(t10)}")
lines.append(f"- **Trailing 5y** ({t5['btc_first_month']} … {t5['btc_last_month']}): {wrow(t5)}\n")
lines.append("\n| BTC corr vs | Full | 10y | 5y |")
lines.append("|---|---|---|---|")
for k in ["growth_eq", "value_eq", "fi_nom", "tips", "gold", "usd"]:
    cf, ct, c5 = fw["correlations"].get(k, {}), t10["correlations"].get(k, {}), t5["correlations"].get(k, {})
    if cf:
        lines.append(f"| {cf['label']} | {cf['corr']:+.2f} | "
                     f"{ct.get('corr', float('nan')):+.2f} | {c5.get('corr', float('nan')):+.2f} |")
lines.append("\n> **The decay is the story.** Realized appreciation collapses as BTC matures "
             f"({fw['btc_appreciation_nominal_annual']*100:.0f}% → {t10['btc_appreciation_nominal_annual']*100:.0f}% → "
             f"{t5['btc_appreciation_nominal_annual']*100:.0f}%/yr); vol falls but stays enormous (~{t5['btc_vol_annual']*100:.0f}%); "
             "equity correlation RISES over time; and the BTC–gold correlation is ~0 in realized monthly data — a problem "
             "for any gold-parity thesis that assumes co-movement. A 10–15yr forward CMA must extrapolate the decay, not "
             "the historical level.\n")
lines.append("\n---\n")

# Comparison table (the 4-column ask) + source column
lines.append("## Comparison table — approaches\n")
lines.append("Approach · Source · Pros · Cons · Key drivers (how it models the asset). Full detail per approach below.\n")
lines.append("\n| # | Approach | Source | Pros | Cons | Key drivers |")
lines.append("|---|---|---|---|---|---|")
for i, r in enumerate(records, 1):
    pros = "<br>".join("• " + p for p in r["pros"])
    cons = "<br>".join("• " + c for c in r["cons"])
    drv = "<br>".join("• " + d for d in r["key_drivers"])
    flag = " ⚠" if r["verdict"].get("numbers_credible") is False else ""
    nm = r["name"].replace("|", "/")
    lines.append(f"| {i}{flag} | {nm} | {r['source_label']} | {pros} | {cons} | {drv} |")
lines.append("\n⚠ = adversarial verifier flagged the source's published numbers as unreliable; see the approach "
             "detail for the corrected figures.\n")
lines.append("\n---\n")

# Outputs matrix (synthesized)
lines.append("## Outputs matrix — synthesized 10–15yr (appreciation / vol / correlations)\n")
lines.append("Representative midpoints parsed from the synthesized prose (full prose in each approach below). "
             "Correlations vs: GrEq=growth equities, VaEq=value equities, FI=nominal fixed income, TIPS, Gold.\n")
lines.append("\n| # | Approach | Appr. real | Appr. nom | Vol | ρ GrEq | ρ VaEq | ρ FI | ρ TIPS | ρ Gold |")
lines.append("|---|---|---|---|---|---|---|---|---|---|")


def fmt(v, pct=False):
    if v is None:
        return "—"
    return f"{v:+.0f}%" if pct else f"{v:+.2f}"


for i, r in enumerate(records, 1):
    p = r["parsed"]
    lines.append(f"| {i} | {r['name'][:48].replace('|','/')} | {fmt(p['appr_real'],1)} | {fmt(p['appr_nom'],1)} | "
                 f"{('%.0f%%'%p['vol']) if p['vol'] is not None else '—'} | {fmt(p['corr_growth'])} | "
                 f"{fmt(p['corr_value'])} | {fmt(p['corr_fi'])} | {fmt(p['corr_tips'])} | {fmt(p['corr_gold'])} |")
lines.append("\n---\n")

# Per-approach detail
lines.append("## Approach detail\n")
for i, r in enumerate(records, 1):
    lines.append(f"\n### {i}. {r['name']}\n")
    lines.append(f"*Family: {r['family']} · Source: {r['source_label']}*\n")
    lines.append(f"\n{r['description']}\n")
    lines.append("\n**Key drivers:** " + "; ".join(r["key_drivers"]) + "\n")
    lines.append("\n**Pros:**")
    for p in r["pros"]:
        lines.append(f"- {p}")
    lines.append("\n**Cons:**")
    for c in r["cons"]:
        lines.append(f"- {c}")
    v = r["verdict"]
    if v.get("numbers_credible") is False or v.get("framing_fair") is False:
        lines.append(f"\n> **⚠ Adversarial verifier.** {v.get('corrections','')}")
        if v.get("issues"):
            lines.append("\n> Issues found:")
            for iss in v["issues"]:
                lines.append(f"> - {iss}")
    else:
        note = (" Corrections: " + v.get("corrections")) if v.get("corrections") else ""
        lines.append(f"\n> *Verifier: numbers credible, framing fair.*{note}")
        if v.get("issues"):
            for iss in v["issues"]:
                lines.append(f"> - {iss}")
    lines.append("\n\n**Outputs (cited vs synthesized):**\n")
    lines.append("\n| | Appr. nom | Appr. real | Vol | ρ GrEq | ρ VaEq | ρ FI | ρ TIPS | ρ Gold |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    lines.append(md_outputs_row("Cited", r["cited_outputs"]))
    lines.append(md_outputs_row("Synthesized", r["synthesized_outputs"]))
    lines.append("\n**Representative sources:**")
    for s in r["representative_sources"]:
        link = s.get("link", "")
        cite = f"{s.get('author_firm','')}, *{s.get('title','')}* ({s.get('year','')})"
        lines.append(f"- {cite}" + (f" — {link}" if link else ""))
    lines.append(f"\n<details><summary>Full notes</summary>\n\n{r['rich_notes']}\n\n</details>\n")
    lines.append("\n---")

# synthesis / completeness
comp = WF.get("completeness", {})
lines.append("\n## House view — the honest cross-approach 10–15yr BTC CMA\n")
if comp.get("house_view"):
    lines.append(comp["house_view"] + "\n")
lines.append("\n## Cross-approach synthesis (completeness critic)\n")
if comp.get("overall_assessment"):
    lines.append(comp["overall_assessment"] + "\n")
if comp.get("cross_cutting_observations"):
    lines.append("\n**Cross-cutting observations:**")
    for o in comp["cross_cutting_observations"]:
        lines.append(f"- {o}")
if comp.get("missing_families"):
    lines.append("\n**Families flagged as missing / thin:**")
    for o in comp["missing_families"]:
        lines.append(f"- {o}")
if comp.get("unverified_numbers"):
    lines.append("\n**Numbers still weakly sourced:**")
    for o in comp["unverified_numbers"]:
        lines.append(f"- {o}")
if WF.get("dropped"):
    lines.append("\n**Approaches dropped by the verifier (not distinct/defensible):**")
    for d in WF["dropped"]:
        lines.append(f"- {d.get('name','')}: {'; '.join(d.get('why') or [])}")
if comp.get("citation_corrections"):
    lines.append("\n**Citation corrections applied (round 2 reconciliation):**")
    for c in comp["citation_corrections"]:
        lines.append(f"- *{c.get('approach_name','')}*: {c.get('wrong','')} → {c.get('correct','')}")

(HERE / "NOTES.md").write_text("\n".join(lines))
print(f"wrote NOTES.md ({len(records)} approaches)")
print("wrote approaches_table.json")

# ============================ dashboard.html ============================
# Single-file interactive deliverable. Charts obey: no black ink, no curves, dots on every point.
PALETTE = {
    "academia": "#2b6cb0", "asset_manager": "#2f855a", "official_sector": "#6b46c1",
    "sell_side": "#c05621", "practitioner": "#b7791f", "crypto_native": "#b83280",
}
INK = "#1a2733"  # near-black ink, never #000


def esc(s):
    return html.escape(str(s if s is not None else ""))


def bullets(items):
    return "".join(f"<li>{esc(x)}</li>" for x in items)


# chart data: synthesized appreciation (nominal) vs vol scatter, + correlation bars
chart_pts = []
for r in records:
    p = r["parsed"]
    if p["appr_nom"] is not None and p["vol"] is not None:
        chart_pts.append({"x": p["vol"], "y": p["appr_nom"], "label": r["name"],
                          "src": r["source_type"]})

anchor_pts = []
for wname, wlabel in [("full_window", "Realized full"), ("trailing_10y", "Realized 10y"), ("trailing_5y", "Realized 5y")]:
    w = ANCHOR[wname]
    anchor_pts.append({"x": round(w["btc_vol_annual"] * 100, 1),
                       "y": round(w["btc_appreciation_nominal_annual"] * 100, 1),
                       "label": wlabel})

rows_json = json.dumps([{
    "i": i, "name": r["name"], "family": r["family"], "source_type": r["source_type"],
    "source_label": r["source_label"], "description": r["description"],
    "key_drivers": r["key_drivers"], "pros": r["pros"], "cons": r["cons"],
    "cited": r["cited_outputs"], "syn": r["synthesized_outputs"],
    "sources": r["representative_sources"], "parsed": r["parsed"],
    "verdict": r["verdict"], "rich": r["rich_notes"],
} for i, r in enumerate(records, 1)], ensure_ascii=False)

anchor_json = json.dumps(ANCHOR, ensure_ascii=False)
comp_json = json.dumps(comp, ensure_ascii=False)
scatter_json = json.dumps(chart_pts, ensure_ascii=False)
anchorpts_json = json.dumps(anchor_pts, ensure_ascii=False)
palette_json = json.dumps(PALETTE, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bitcoin CMA — Literature Review</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--ink:#1a2733;--bg:#f7f9fb;--card:#fff;--line:#dde5ec;--muted:#5a6b7a;--btc:#f7931a;}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{background:linear-gradient(120deg,#11212e,#1f3a4d);color:#fff;padding:26px 28px}
header h1{margin:0 0 6px;font-size:24px}
header p{margin:3px 0;color:#c8d6e0;font-size:13.5px;max-width:1000px}
.wrap{max-width:1280px;margin:0 auto;padding:22px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:18px 0 14px}
.tab{padding:8px 15px;border:1px solid var(--line);background:var(--card);border-radius:7px;cursor:pointer;font-weight:600;font-size:13.5px}
.tab.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.panel{display:none}.panel.active{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin:14px 0}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0}
.kpi{flex:1;min-width:150px;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:13px}
.kpi .v{font-size:21px;font-weight:700}.kpi .l{font-size:12px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#eef3f7;cursor:pointer;position:sticky;top:0}
th.sorted-asc::after{content:" ▲"}th.sorted-desc::after{content:" ▼"}
tr.approw{cursor:pointer}tr.approw:hover{background:#f0f6fb}
.src-chip{display:inline-block;padding:2px 8px;border-radius:11px;color:#fff;font-size:11px;font-weight:600}
.detail{background:#fbfdff;border-left:3px solid var(--btc)}
.detail h3{margin:2px 0 8px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.cols h4{margin:6px 0 4px;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
ul{margin:4px 0 10px;padding-left:18px}li{margin:2px 0}
.flag{color:#c05621;font-weight:700}
.muted{color:var(--muted);font-size:12.5px}
details{margin-top:8px}summary{cursor:pointer;font-weight:600;color:var(--muted)}
.outtab td:first-child{font-weight:600;background:#f2f7fb}
canvas{max-width:100%}
.note{background:#fff8ec;border:1px solid #f0dcb8;border-radius:8px;padding:12px;font-size:13px;margin:10px 0}
a{color:#2b6cb0}
@media(max-width:780px){.cols{grid-template-columns:1fr}}
</style></head>
<body>
<header>
<h1>Bitcoin Capital-Market Assumption — Literature Review</h1>
<p>How academics, asset managers, crypto-native analysts, and sell-side strategists set a <b>10–15 year</b> BTC CMA (expected appreciation, volatility, correlations). Bitcoin has no cashflow, so it does not fit the equity building-block CMA — these are the alternative frameworks, each deep-dived and adversarially verified.</p>
<p class="muted" style="color:#9fb4c2">Synthesized figures are reasoned judgments under each approach's logic, anchored to a scripted realized baseline — not computed forecasts. Source-published figures are cited where they exist.</p>
</header>
<div class="wrap">
<div class="tabs" id="tabs"></div>
<div id="p-overview" class="panel active"></div>
<div id="p-table" class="panel"></div>
<div id="p-outputs" class="panel"></div>
<div id="p-baseline" class="panel"></div>
<div id="p-synth" class="panel"></div>
</div>
<script>
const ROWS = __ROWS__;
const ANCHOR = __ANCHOR__;
const COMP = __COMP__;
const SCATTER = __SCATTER__;
const ANCHORPTS = __ANCHORPTS__;
const PAL = __PAL__;
const INK = "#1a2733";
function chip(st,label){return `<span class="src-chip" style="background:${PAL[st]||'#789'}">${label}</span>`;}
function pct(v,d=0){return v==null?'—':(v>=0?'+':'')+v.toFixed(d)+'%';}
function cor(v){return v==null?'—':(v>=0?'+':'')+v.toFixed(2);}

/* ---------- tabs ---------- */
const TABS=[['overview','Overview'],['table','Approaches'],['outputs','Outputs matrix'],['baseline','Empirical baseline'],['synth','Synthesis']];
const tabsEl=document.getElementById('tabs');
TABS.forEach(([k,l],idx)=>{const b=document.createElement('div');b.className='tab'+(idx===0?' active':'');b.textContent=l;b.onclick=()=>{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));b.classList.add('active');
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.getElementById('p-'+k).classList.add('active');
  if(k==='overview')drawScatter();if(k==='baseline')drawBaseline();
};tabsEl.appendChild(b);});

/* ---------- overview ---------- */
function fw(w){return ANCHOR[w];}
document.getElementById('p-overview').innerHTML=`
<div class="card">
<h2 style="margin-top:0">The decay is the story</h2>
<div class="kpis">
  <div class="kpi"><div class="v">${ROWS.length}</div><div class="l">approaches reviewed &amp; verified</div></div>
  <div class="kpi"><div class="v">${pct(fw('full_window').btc_appreciation_nominal_annual*100)}</div><div class="l">realized nom. appr. — full window</div></div>
  <div class="kpi"><div class="v">${pct(fw('trailing_10y').btc_appreciation_nominal_annual*100)}</div><div class="l">realized — trailing 10y</div></div>
  <div class="kpi"><div class="v">${pct(fw('trailing_5y').btc_appreciation_nominal_annual*100)}</div><div class="l">realized — trailing 5y</div></div>
  <div class="kpi"><div class="v">${(fw('trailing_5y').btc_vol_annual*100).toFixed(0)}%</div><div class="l">realized vol — trailing 5y</div></div>
</div>
<div class="note">Realized BTC appreciation collapses as the asset matures (${(fw('full_window').btc_appreciation_nominal_annual*100).toFixed(0)}% → ${(fw('trailing_10y').btc_appreciation_nominal_annual*100).toFixed(0)}% → ${(fw('trailing_5y').btc_appreciation_nominal_annual*100).toFixed(0)}%/yr). Volatility falls but stays enormous (~${(fw('trailing_5y').btc_vol_annual*100).toFixed(0)}%). Equity correlation <b>rises</b> over time; the BTC–gold correlation is ~0 in realized monthly data. A credible 10–15yr CMA must extrapolate the decay, not the historical level.</div>
</div>
<div class="card">
<h3 style="margin-top:0">Synthesized 10–15yr appreciation vs volatility, by approach</h3>
<p class="muted">Each dot = one approach's synthesized nominal appreciation and vol. Squares = scripted realized BTC (full / 10y / 5y windows) for reference. Color = source type.</p>
<canvas id="scatter" height="150"></canvas>
</div>`;

let scatterChart;
function drawScatter(){
  if(scatterChart)return;
  const bySrc={};
  SCATTER.forEach(p=>{(bySrc[p.src]=bySrc[p.src]||[]).push({x:p.x,y:p.y,label:p.label});});
  const ds=Object.entries(bySrc).map(([st,pts])=>({label:st,data:pts,backgroundColor:PAL[st]||'#789',
    pointRadius:6,pointHoverRadius:9,showLine:false}));
  ds.push({label:'Realized BTC',data:ANCHORPTS.map(p=>({x:p.x,y:p.y,label:p.label})),
    backgroundColor:'#f7931a',pointStyle:'rectRot',pointRadius:9,pointHoverRadius:12,showLine:false});
  scatterChart=new Chart(document.getElementById('scatter'),{type:'scatter',data:{datasets:ds},
    options:{plugins:{legend:{position:'bottom'},tooltip:{callbacks:{label:c=>`${c.raw.label}: ${c.raw.y>=0?'+':''}${c.raw.y.toFixed(0)}% appr, ${c.raw.x.toFixed(0)}% vol`}}},
    scales:{x:{title:{display:true,text:'Annualized volatility (%)'},grid:{color:'#eef'}},
            y:{title:{display:true,text:'Nominal appreciation (%/yr)'},grid:{color:'#eef'}}}}});
}
setTimeout(drawScatter,60);

/* ---------- approaches table + detail ---------- */
let sortKey='i',sortDir=1;
function srcRank(s){return ['academia','asset_manager','official_sector','sell_side','crypto_native','practitioner'].indexOf(s);}
function renderTable(){
  const cols=[['i','#'],['name','Approach'],['family','Family'],['source_type','Source'],
    ['appr_nom','Appr nom'],['appr_real','Appr real'],['vol','Vol'],['corr_gold','ρ Gold']];
  let h='<div class="card"><p class="muted">Click a column to sort; click a row to expand the full deep-dive (drivers, pros/cons, cited vs synthesized outputs, sources, verifier verdict).</p><table id="apptab"><thead><tr>';
  cols.forEach(([k,l])=>{h+=`<th data-k="${k}" class="${sortKey===k?(sortDir>0?'sorted-asc':'sorted-desc'):''}">${l}</th>`;});
  h+='</tr></thead><tbody>';
  const sorted=[...ROWS].sort((a,b)=>{
    let va,vb;
    if(sortKey==='source_type'){va=srcRank(a.source_type);vb=srcRank(b.source_type);}
    else if(['appr_nom','appr_real','vol','corr_gold'].includes(sortKey)){va=a.parsed[sortKey==='appr_nom'?'appr_nom':sortKey==='appr_real'?'appr_real':sortKey];vb=b.parsed[sortKey==='appr_nom'?'appr_nom':sortKey==='appr_real'?'appr_real':sortKey];va=va==null?-1e9:va;vb=vb==null?-1e9:vb;}
    else{va=a[sortKey];vb=b[sortKey];}
    return (va>vb?1:va<vb?-1:0)*sortDir;
  });
  sorted.forEach(r=>{
    const flag=r.verdict&&r.verdict.numbers_credible===false?' <span class="flag" title="verifier flagged numbers">⚠</span>':'';
    h+=`<tr class="approw" data-i="${r.i}"><td>${r.i}</td><td>${r.name}${flag}</td><td>${r.family}</td>
      <td>${chip(r.source_type,r.source_label)}</td><td>${pct(r.parsed.appr_nom)}</td>
      <td>${pct(r.parsed.appr_real)}</td><td>${r.parsed.vol==null?'—':r.parsed.vol.toFixed(0)+'%'}</td>
      <td>${cor(r.parsed.corr_gold)}</td></tr>`;
    h+=`<tr id="d-${r.i}" style="display:none"><td colspan="8" class="detail">${detail(r)}</td></tr>`;
  });
  h+='</tbody></table></div>';
  document.getElementById('p-table').innerHTML=h;
  document.querySelectorAll('#apptab th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(k===sortKey)sortDir*=-1;else{sortKey=k;sortDir=1;}renderTable();});
  document.querySelectorAll('tr.approw').forEach(tr=>tr.onclick=()=>{const d=document.getElementById('d-'+tr.dataset.i);d.style.display=d.style.display==='none'?'':'none';});
}
function outRow(lab,o){return `<tr><td>${lab}</td><td>${o.appreciation_nominal||'—'}</td><td>${o.appreciation_real||'—'}</td>
  <td>${o.volatility||'—'}</td><td>${o.corr_growth_eq||'—'}</td><td>${o.corr_value_eq||'—'}</td>
  <td>${o.corr_fi_nominal||'—'}</td><td>${o.corr_tips||'—'}</td><td>${o.corr_gold||'—'}</td></tr>`;}
function detail(r){
  const v=r.verdict||{};
  let vbox='';
  if(v.numbers_credible===false||v.framing_fair===false){
    vbox=`<div class="note"><b class="flag">⚠ Adversarial verifier.</b> ${v.corrections||''}<ul>${(v.issues||[]).map(x=>`<li>${x}</li>`).join('')}</ul></div>`;
  }else{
    vbox=`<div class="muted">✓ Verifier: numbers credible, framing fair.${v.corrections?' '+v.corrections:''}${(v.issues||[]).length?'<ul>'+(v.issues||[]).map(x=>'<li>'+x+'</li>').join('')+'</ul>':''}</div>`;
  }
  return `<h3>${r.i}. ${r.name}</h3><p class="muted">${r.family} · ${r.source_label}</p>
   <p>${r.description}</p>
   <h4>Key drivers</h4><ul>${r.key_drivers.map(x=>`<li>${x}</li>`).join('')}</ul>
   <div class="cols"><div><h4>Pros</h4><ul>${r.pros.map(x=>`<li>${x}</li>`).join('')}</ul></div>
   <div><h4>Cons</h4><ul>${r.cons.map(x=>`<li>${x}</li>`).join('')}</ul></div></div>
   ${vbox}
   <h4>Outputs — cited vs synthesized</h4>
   <table class="outtab"><thead><tr><th></th><th>Appr nom</th><th>Appr real</th><th>Vol</th><th>ρ GrEq</th><th>ρ VaEq</th><th>ρ FI</th><th>ρ TIPS</th><th>ρ Gold</th></tr></thead>
   <tbody>${outRow('Cited',r.cited)}${outRow('Synthesized',r.syn)}</tbody></table>
   <h4>Representative sources</h4><ul>${r.sources.map(s=>`<li>${s.author_firm}, <i>${s.title}</i> (${s.year})${s.link?` — <a href="${s.link}" target="_blank" rel="noopener">link</a>`:''}</li>`).join('')}</ul>
   <details><summary>Full notes</summary><p class="muted" style="white-space:pre-wrap">${r.rich}</p></details>`;
}
renderTable();

/* ---------- outputs matrix ---------- */
(function(){
  let h='<div class="card"><h3 style="margin-top:0">Synthesized 10–15yr outputs matrix</h3><p class="muted">Representative midpoints parsed from the synthesized prose. Correlations vs growth eq / value eq / nominal FI / TIPS / gold.</p>'
    +'<table><thead><tr><th>#</th><th>Approach</th><th>Appr real</th><th>Appr nom</th><th>Vol</th><th>ρ GrEq</th><th>ρ VaEq</th><th>ρ FI</th><th>ρ TIPS</th><th>ρ Gold</th></tr></thead><tbody>';
  ROWS.forEach(r=>{const p=r.parsed;h+=`<tr><td>${r.i}</td><td>${r.name}</td><td>${pct(p.appr_real)}</td><td>${pct(p.appr_nom)}</td>
    <td>${p.vol==null?'—':p.vol.toFixed(0)+'%'}</td><td>${cor(p.corr_growth)}</td><td>${cor(p.corr_value)}</td>
    <td>${cor(p.corr_fi)}</td><td>${cor(p.corr_tips)}</td><td>${cor(p.corr_gold)}</td></tr>`;});
  h+='</tbody></table></div>';
  document.getElementById('p-outputs').innerHTML=h;
})();

/* ---------- empirical baseline ---------- */
function drawBaseline(){
  if(document.getElementById('p-baseline').dataset.done)return;
  document.getElementById('p-baseline').dataset.done=1;
  const W=[['full_window','Full'],['trailing_10y','10y'],['trailing_5y','5y']];
  let h='<div class="card"><h3 style="margin-top:0">Scripted realized BTC baseline</h3>'
    +`<p class="muted">${ANCHOR.method} ${ANCHOR.note}</p>`
    +'<table><thead><tr><th>Window</th><th>Span</th><th>Appr nom</th><th>Appr real</th><th>Vol</th></tr></thead><tbody>';
  W.forEach(([k,l])=>{const w=ANCHOR[k];h+=`<tr><td>${l}</td><td>${w.btc_first_month}…${w.btc_last_month}</td>
    <td>${pct(w.btc_appreciation_nominal_annual*100)}</td><td>${pct((w.btc_appreciation_real_annual||0)*100)}</td>
    <td>${(w.btc_vol_annual*100).toFixed(0)}%</td></tr>`;});
  h+='</tbody></table>'
    +'<h4>Correlation of monthly BTC returns vs asset classes</h4>'
    +'<table><thead><tr><th>vs</th><th>Full</th><th>10y</th><th>5y</th></tr></thead><tbody>';
  ['growth_eq','value_eq','fi_nom','tips','gold','usd'].forEach(key=>{
    const f=ANCHOR.full_window.correlations[key],t=ANCHOR.trailing_10y.correlations[key],c=ANCHOR.trailing_5y.correlations[key];
    if(f)h+=`<tr><td>${f.label}</td><td>${cor(f.corr)}</td><td>${t?cor(t.corr):'—'}</td><td>${c?cor(c.corr):'—'}</td></tr>`;
  });
  h+='</tbody></table><canvas id="declc" height="120" style="margin-top:14px"></canvas></div>';
  document.getElementById('p-baseline').innerHTML=h;
  const lab=W.map(([k,l])=>l);
  new Chart(document.getElementById('declc'),{type:'line',data:{labels:lab,datasets:[
    {label:'Nominal appr (%/yr)',data:W.map(([k])=>+(ANCHOR[k].btc_appreciation_nominal_annual*100).toFixed(1)),borderColor:'#f7931a',backgroundColor:'#f7931a',tension:0,pointRadius:6,pointHoverRadius:9},
    {label:'Volatility (%)',data:W.map(([k])=>+(ANCHOR[k].btc_vol_annual*100).toFixed(1)),borderColor:'#2b6cb0',backgroundColor:'#2b6cb0',tension:0,pointRadius:6,pointHoverRadius:9}
  ]},options:{plugins:{legend:{position:'bottom'}},scales:{y:{grid:{color:'#eef'},title:{display:true,text:'% (annualized)'}},x:{grid:{color:'#eef'}}}}});
}

/* ---------- synthesis ---------- */
(function(){
  let h='';
  if(COMP.house_view)h+=`<div class="card" style="border-left:4px solid var(--btc)"><h3 style="margin-top:0">House view — honest cross-approach 10–15yr BTC CMA</h3><p>${COMP.house_view}</p></div>`;
  h+='<div class="card"><h3 style="margin-top:0">Cross-approach synthesis &amp; completeness critic</h3>';
  if(COMP.overall_assessment)h+=`<p>${COMP.overall_assessment}</p>`;
  const sec=(t,arr)=>arr&&arr.length?`<h4>${t}</h4><ul>${arr.map(x=>`<li>${x}</li>`).join('')}</ul>`:'';
  h+=sec('Cross-cutting observations',COMP.cross_cutting_observations);
  h+=sec('Families flagged missing / thin',COMP.missing_families);
  h+=sec('Numbers still weakly sourced',COMP.unverified_numbers);
  if(COMP.citation_corrections&&COMP.citation_corrections.length){
    h+='<h4>Citation corrections applied (round 2)</h4><ul>'+COMP.citation_corrections.map(c=>`<li><i>${c.approach_name}</i>: ${c.wrong} → ${c.correct}</li>`).join('')+'</ul>';
  }
  h+='</div>';
  document.getElementById('p-synth').innerHTML=h;
})();
</script>
</body></html>"""

HTML = (HTML.replace("__ROWS__", rows_json).replace("__ANCHOR__", anchor_json)
        .replace("__COMP__", comp_json).replace("__SCATTER__", scatter_json)
        .replace("__ANCHORPTS__", anchorpts_json).replace("__PAL__", palette_json))
(HERE / "dashboard.html").write_text(HTML)
print("wrote dashboard.html")
