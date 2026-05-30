# BRIEF — Bitcoin CMA Literature Review (10–15 yr)

**Paste this entire file as the opening prompt to a fresh Claude Code agent working under `research/`.**
This is the BTC twin of a gold CMA literature review running in parallel. Keep your work fully separate
from the gold effort — do NOT touch `GOLDBTC/gold/`.

---

## 0. Setup (do this first)

- You are working in `research/`. Read `research/CLAUDE.md` and `research/SKILLS/INDEX.md` per the protocol,
  and call `mcp__brain__brain_principles` once. Honor the always-on rules: scripted numbers only (LLM narrates
  qualitative meaning), no black ink / no curves in any chart, terse responses, register any new data source in
  `research/DATA_SOURCES.md`, never commit as Claude.
- Your working directory and all outputs live in **`research/GOLDBTC/btc/cma_litreview/`**.
- This is explicitly a **workflow** task — you have the user's opt-in to use the `Workflow` tool and fan out
  many subagents. Mirror the gold design (below) for BTC.

## 1. Goal

Produce a **literature review of approaches to setting a 10–15-year Bitcoin Capital Market Assumption (CMA)** —
expected appreciation, volatility, and correlations. The point is that BTC (like gold) does NOT fit the standard
equity building-block CMA (CAPE + net dilution + real GDP + dividend yield + 10y yield). We need to catalog the
*alternative* frameworks people actually use, weigh them, and extract their numeric outputs.

## 2. Deliverable shape (match the gold deliverable exactly)

**Work in a master `NOTES.md` first** (rich, retained detail — quotes, citations, methodology, caveats, your
reasoning). The `.md` is the source of truth so in-depth follow-up questions can be answered instantly. **Only at
the very end** translate the distilled version into a **single-file interactive HTML dashboard** (`dashboard.html`).

The centerpiece is a **comparison table** of approaches with these columns:

| Approach | Pros (bullets) | Cons (bullets) | Key drivers (how it models the asset) |

- Each **row** is a distinct approach. Source each to **academia / industry / official-sector / sell-side**.
- Then, for **each approach**, the full CMA outputs: **expected appreciation** (nominal + real, 10–15 yr horizon),
  **volatility**, and **correlation** vs: **growth equities, value equities, fixed income (nominal IG/Treasury),
  inflation-linked (TIPS)** — and vs **gold** (BTC-specific addition; the "digital gold / gold-parity" thesis makes
  the BTC–gold relationship central). 
- For outputs, provide **BOTH**: (a) the figures the source literature actually publishes (cited, with blanks where
  silent), AND (b) **your own synthesized 10–15 yr estimate** under each approach's logic, clearly labeled as
  synthesis. Anchor synthesized numbers to a **scripted empirical baseline** (compute realized BTC return/vol and
  rolling correlations vs the asset classes from a real price series — don't eyeball them).

## 3. BTC-specific approaches to cover (seed list — expand via research, dedupe into a canonical taxonomy)

Make sure your scouts surface at least these families, then add what they find:

- **Stock-to-flow (S2F / S2FX)** — PlanB; scarcity/halving supply ratio. (Cover the heavy academic critiques:
  spurious cointegration, non-stationarity, the post-2021 break.)
- **Metcalfe's law / network-value (NVT, NVM, active addresses)** — value ∝ users². Peterson; Woo.
- **Production / marginal cost-of-mining floor** — Hayes; electricity + hashrate + difficulty.
- **Store-of-value / gold-parity (TAM substitution)** — "X% of gold's market cap"; Fidelity/ARK/CathieWood,
  Wood "$1–3.8M" bands, Pompliano. Total-addressable-market share of gold/bonds/M2/offshore wealth.
- **Monetary base / M2 substitution & debasement** — BTC as % of global money supply.
- **Power-law / log-log time regression** — Giovanni Santostasi power-law; Burger; rainbow charts.
- **Adoption S-curve / Metcalfe-adoption hybrid** — user-growth logistic → price.
- **On-chain valuation (MVRV, realized cap, thermocap, SOPR, RHODL)** — Glassnode/Coinmetrics framings.
- **Discounted-utility / monetary premium DCF** — fundamental "moneyness" cashflow analogues.
- **Options / vol-surface implied** — risk-neutral forward + implied vol term structure (Deribit).
- **Factor / risk-premium regression** — BTC vs liquidity, real rates, risk appetite, DXY (academic asset-pricing).
- **Portfolio-optimization / risk-budget demand** — "1–5% allocation" institutional sizing studies.
- **Asset-manager LTCMA treatment** — how (if at all) BlackRock / JPM / Invesco / VanEck / Fidelity / Grayscale /
  ARK / Galaxy actually publish a BTC capital-market assumption, and the method behind it.

## 4. Suggested workflow architecture (mirror the gold run)

1. **Scout (parallel barrier):** ~4 agents enumerate approaches by domain (academia, asset-manager/industry,
   on-chain/crypto-native analysts, sell-side/strategists). Each returns candidate approaches + seed sources.
2. **Taxonomy synthesizer (1 agent):** dedupe scout output into a canonical list of ~12–16 distinct approaches
   with family + source-type tags.
3. **Deep-dive → verify (pipeline, no barrier):** one researcher agent per approach (description, key drivers,
   pros, cons, cited outputs with citations, rich notes), each immediately followed by an adversarial verifier
   that tries to refute the numbers and the pro/con framing.
4. **Empirical anchor (scripted):** a script that pulls a BTC price series (e.g. via a free source — register it
   in `DATA_SOURCES.md`) and computes realized appreciation, annualized vol, and rolling correlations vs growth
   equities / value equities / nominal FI / TIPS / gold, so synthesized numbers are grounded.
5. **Synthesis + completeness critic:** assemble the comparison table + outputs; a final critic asks "what family
   of approach is missing, what number is unverified."
6. **Render:** main loop writes `NOTES.md`, then builds `dashboard.html` (sortable approach table, expandable
   pro/con, an outputs matrix). Charts obey: no black, no curves, dots on every point.

## 5. Output files (in `research/GOLDBTC/btc/cma_litreview/`)

- `NOTES.md` — master working doc (rich, retained).
- `approaches/` — optional per-approach long-form notes.
- `empirical_anchor.py` + its JSON output — the scripted baseline.
- `dashboard.html` — final single-file interactive deliverable (built LAST).

## 6. Guardrails

- Numbers come from scripts or are cited to a source; your synthesized estimates are reasoned judgments clearly
  labeled as such, not presented as computed statistics.
- Be brutal about S2F and Metcalfe — the academic literature largely rejects naive versions; the review must
  represent that, not launder hype.
- Cite everything (author/firm, title, year, link). Distinguish peer-reviewed academia from marketing.
- Local-only unless the user says to deploy.
