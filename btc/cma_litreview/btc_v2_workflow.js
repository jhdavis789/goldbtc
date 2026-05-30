export const meta = {
  name: 'btc-cma-litreview-v2',
  description: 'Evaluate the existing 20 BTC-CMA approaches, expand to full breadth via divergent idea sweep, add medium explanations, score + rank every approach, map orthogonal signal',
  phases: [
    { title: 'Evaluate', detail: 'critique + correct each existing approach; write its medium explanation' },
    { title: 'Breadth', detail: '12 divergent disciplinary lenses + a tail-finding round surface NEW approaches' },
    { title: 'Dedupe', detail: 'consolidate new candidates into distinct approaches not already covered' },
    { title: 'Research', detail: 'deep-dive each NEW approach (incl. medium explanation)' },
    { title: 'Verify', detail: 'adversarial verifier refutes each new approach' },
    { title: 'Rank', detail: 'score every approach (old+new) on rigor/signal/robustness/data-ops' },
    { title: 'Adjudicate', detail: 'global ranking + tiers + orthogonality clusters + recommended ensemble' },
    { title: 'Completeness', detail: 'critic checks remaining breadth gaps' },
  ],
}

const DIGEST = "/Users/Jackson/.openclaw/workspace/research/GOLDBTC/btc/cma_litreview/existing_digest.json"
const ANCHOR = "Realized BTC baseline (Coinmetrics PriceUSD, monthly). FULL 2010-07..2026-05: nom 142%/yr, real 137%, vol 103%; corr growth +0.26, gold -0.01. 10Y: nom 65%, vol 69%; corr growth +0.36, gold +0.03. 5Y: nom 17%, real 11%, vol 57%; corr growth +0.56, gold +0.04, value +0.37, FI +0.19, TIPS +0.30. PATTERN: appreciation decays 142->65->17%/yr; vol floor ~57%; equity corr RISES; BTC-gold corr ~0. Honest cross-approach central: ~8-12% nominal / 5-9% real, vol ~50-60%, gold corr ~0-0.15."
const GROUND = `
First use the Read tool on ${DIGEST} — it contains the 20 BTC-CMA approaches ALREADY covered (name, family, source_type, description, key_drivers, pros, cons, cited & synthesized outputs).
Use WebSearch/WebFetch for primary sources; cite author/firm, title, year, URL. Do NOT fabricate citations.
CONTEXT: We set 10-15yr capital-market assumptions (appreciation, volatility, correlations) for BITCOIN, which has no cashflow so equity building blocks (CAPE, dilution, real GDP, div yield) don't apply. Correlation asset set: growth equities, value equities, nominal fixed income, TIPS, and GOLD (BTC-specific 'digital gold' axis).
EMPIRICAL ANCHOR (realized, scripted): ${ANCHOR}
A credible 10-15yr forward CMA must extrapolate BTC's appreciation DECAY, not its historical level. Be brutal about S2F/Metcalfe/power-law/gold-parity hype — the academic literature largely rejects naive versions.`
const SRC_ENUM = ["academia", "asset_manager", "official_sector", "sell_side", "practitioner", "crypto_native"]

// ===================== PHASE 1: EVALUATE EXISTING =====================
phase('Evaluate')
const EVAL_SCHEMA = {
  type: 'object',
  required: ['index', 'name', 'quality_score', 'is_distinct', 'issues', 'corrections', 'medium_explanation'],
  properties: {
    index: { type: 'integer' },
    name: { type: 'string' },
    quality_score: { type: 'integer', minimum: 1, maximum: 5, description: 'overall quality of the existing entry as it stands' },
    is_distinct: { type: 'boolean', description: 'is this a genuinely distinct approach or redundant with another existing one?' },
    redundant_with: { type: 'array', items: { type: 'string' }, description: 'names of existing approaches this overlaps (empty if distinct)' },
    issues: { type: 'array', items: { type: 'string' }, description: 'factual/logic problems, weak numbers, missing nuance' },
    corrections: { type: 'string', description: 'specific fixes to apply; "none" if clean' },
    medium_explanation: { type: 'string', description: 'a 120-180 word MEDIUM explanation of how this approach models BTC and produces a CMA — fuller than a one-liner, more digestible than the long notes. Self-contained prose.' },
  },
}
const N_EXISTING = 20
const evals = await pipeline(
  Array.from({ length: N_EXISTING }, (_, i) => i),
  (i) => agent(
    `Read ${DIGEST}, then EVALUATE approach at index ${i} (the ${i}-th element of its "approaches" array). ${GROUND}\n\n` +
    `Critically assess: is it correct, are its numbers defensible, are pros/cons right, is it genuinely distinct or redundant? List issues and concrete corrections. THEN write its 120-180 word MEDIUM explanation (a new column we're adding) — fuller than the one-line description, plainer than deep notes; explain the mechanism, the key inputs, and what it implies for a 10-15yr BTC CMA.`,
    { label: `eval:${i}`, phase: 'Evaluate', schema: EVAL_SCHEMA }
  )
)
const evalsOk = evals.filter(Boolean)
log(`Evaluated ${evalsOk.length}/${N_EXISTING} existing approaches`)

// ===================== PHASE 2: BREADTH (divergent lenses) =====================
phase('Breadth')
const SCOUT_SCHEMA = {
  type: 'object', required: ['candidates'],
  properties: {
    candidates: {
      type: 'array',
      items: {
        type: 'object', required: ['name', 'family', 'source_type', 'one_line', 'why_new', 'seed_sources'],
        properties: {
          name: { type: 'string' },
          family: { type: 'string' },
          source_type: { type: 'string', enum: SRC_ENUM },
          one_line: { type: 'string' },
          why_new: { type: 'string', description: 'why this is NOT already one of the 20 existing approaches' },
          seed_sources: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  },
}
const LENSES = [
  { k: 'econophysics', p: 'ECONOPHYSICS / complex-systems beyond the basic power-law/LPPLS already covered: fractal/multifractal & Hurst-exponent persistence, generalized-Metcalfe+LPPLS hybrids, scaling-law / log-log corridor VARIANTS (Weibull, dispersion), agent-based & percolation market models, entropy/complexity valuation, self-organized criticality.' },
  { k: 'monetary-macro', p: 'MONETARY MACRO beyond simple M2/QTM coverage: global-liquidity barometer (Lyn Alden / Sam Callahan), fiscal theory of the price level & fiscal-dominance applied to BTC, Triffin/dedollarization reserve-rotation, real-money-balances demand, BTC-as-collateral / eurodollar-shadow-money framings, debasement-CAGR / "fiat half-life" models.' },
  { k: 'behavioral-text', p: 'BEHAVIORAL & ATTENTION / TEXT: Google-Trends & search-attention valuation, social-media / X / Reddit sentiment & NLP, Wikipedia-pageview models, Fear & Greed index, narrative economics (Shiller), reflexivity/Soros, prospect-theory & lottery-demand framings for BTC.' },
  { k: 'mining-energy', p: 'MINING & ENERGY (distinct from a single marginal-cost floor): energy-value / joule-per-coin "thermoeconomics", hashrate-as-value & difficulty-ribbon, miner production-cost CURVE & capitulation, electricity-price elasticity of supply, hash-price / miner-revenue models, Cambridge CBECI-based floors.' },
  { k: 'quant-derivatives', p: 'QUANT / DERIVATIVES microstructure (distinct from a single DVOL/RND point or the futures-basis row): variance/volatility risk premium harvesting, options skew & convexity signals, perp-funding term-structure factor, CME vs offshore basis curve factor, carry/momentum/value cross-crypto factor zoo, lead-lag spot-futures price discovery.' },
  { k: 'ml-regime', p: 'MACHINE-LEARNING & forecasting (distinct from the academic regime/jump return-process row): random-forest/gradient-boosting & LSTM/transformer BTC price forecasting, dynamic factor / nowcasting with macro, Bayesian model averaging, on-chain-feature ML, reinforcement-learning allocation.' },
  { k: 'onchain-microstructure', p: 'ON-CHAIN beyond the realized-cap/MVRV/SOPR cluster already covered: URPD / cost-basis distribution & realized-price bands, coin-days-destroyed & dormancy/liveliness, HODL-implied illiquid-supply-shock, exchange net-flow & reserve depletion, miner-position / Puell multiple, whale-cohort & entity-adjusted supply, Spent-Output-age (RHODL is covered — find the rest).' },
  { k: 'portfolio-implied', p: 'ADVANCED PORTFOLIO THEORY (return-IMPLIED, not just 1-5% sizing): Black-Litterman reverse-optimization implied BTC equilibrium return, risk-parity / max-diversification implied view, endowment / liability-driven hedging-demand return, CVaR/tail-insurance pricing of BTC, Kelly/fractional-Kelly growth-optimal sizing.' },
  { k: 'geopolitics-thematic', p: 'GEOPOLITICAL & THEMATIC SCENARIO: capital-flight / capital-control-evasion premium (Argentina, Nigeria, Turkey), sanctions-evasion & reserve-freezing hedge, nation-state adoption & strategic-bitcoin-reserve scenarios (US SBR, El Salvador), remittance-corridor demand, authoritarian-regime wealth-exit as a secular return driver.' },
  { k: 'adoption-diffusion', p: 'ADOPTION & DIFFUSION beyond the single S-curve row: Bass diffusion / Rogers innovation curve calibrated to wallets, country-level adoption S-curves, generational wealth-transfer demand, Metcalfe-adoption hybrid VARIANTS, network-effects / two-sided-market valuation, Lindy-effect survival-adoption.' },
  { k: 'relative-value', p: 'CROSS-ASSET RELATIVE-VALUE: BTC/gold ratio & gold-market-cap-share path, BTC/M2 & BTC/global-wealth, BTC vs Nasdaq/NDX beta-implied, MSTR/COIN/miner-equity-proxy implied BTC, BTC-dominance & ETH/BTC relative rotation, BTC vs offshore-USD-wealth TAM.' },
  { k: 'survey-market-implied', p: 'SURVEY / CONSENSUS / PREDICTION-MARKET aggregation: analyst price-target surveys & their track record, prediction markets (Polymarket / Kalshi) implied terminal-price distributions, Bloomberg/strategist consensus aggregation, betting-odds-implied, plus institutional treasury-company (MSTR/strategy) reflexive demand as its own valuation channel.' },
]
const round1 = (await parallel(LENSES.map(L => () =>
  agent(`Scout the "${L.k}" lens for BTC-CMA approaches NOT already among the existing 20. ${L.p}\n\n${GROUND}\n\nReturn every distinct approach/framework in this lens that is genuinely additive. For each, state why_new (how it differs from the existing 20). Be expansive — we want full breadth and more divergent ideas. Cite real seed sources; do not fabricate.`,
    { label: `scout:${L.k}`, phase: 'Breadth', schema: SCOUT_SCHEMA })
))).filter(Boolean)
const cand1 = round1.flatMap(r => r.candidates)
log(`Round 1: ${cand1.length} new candidate approaches across ${round1.length} lenses`)

// tail-finding round
const tailLenses = ['exotic/heterodox academic', 'practitioner/buy-side proprietary (Galaxy/ARK/Fidelity/Bitwise/VanEck models)', 'central-bank & multilateral (BIS/IMF/Fed/ECB crypto research)', 'data-vendor & index-provider methodologies (Coinmetrics/Glassnode/K33/CF Benchmarks)', 'corporate-treasury & ETF reflexive-demand (MSTR/strategy, spot-ETF flow-to-price)', 'insurance/actuarial, pension LDI & sovereign-wealth']
const round2 = (await parallel(tailLenses.map(t => () =>
  agent(`TAIL-FINDING scout. The existing 20 approaches are in ${DIGEST}. Round-1 scouts already proposed these new candidates: ${cand1.map(c => c.name).join(' | ')}.\n\nYour lens: ${t}. Find approaches to a 10-15yr BTC CMA that are STILL missing from BOTH lists — the long tail, exotic, heterodox, or proprietary. ${GROUND}\n\nReturn only genuinely additive approaches with why_new. Cite real sources.`,
    { label: `tail:${t}`.slice(0, 50), phase: 'Breadth', schema: SCOUT_SCHEMA })
))).filter(Boolean)
const cand2 = round2.flatMap(r => r.candidates)
log(`Round 2 (tail): ${cand2.length} additional candidates`)
const allCand = cand1.concat(cand2)

// ===================== PHASE 3: DEDUPE NEW =====================
phase('Dedupe')
const DEDUPE_SCHEMA = {
  type: 'object', required: ['approaches'],
  properties: {
    approaches: {
      type: 'array',
      items: {
        type: 'object', required: ['name', 'family', 'source_type', 'why_distinct', 'seed_sources'],
        properties: {
          name: { type: 'string' },
          family: { type: 'string' },
          source_type: { type: 'string', enum: SRC_ENUM },
          why_distinct: { type: 'string', description: 'why distinct from BOTH the existing 20 AND the other new approaches' },
          seed_sources: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  },
}
const newTax = await agent(
  `Read ${DIGEST} (the 20 existing approaches). Here are ${allCand.length} NEW candidate approaches proposed by divergent-lens scouts:\n\n${JSON.stringify(allCand, null, 2)}\n\n` +
  `Consolidate these into a canonical list of genuinely DISTINCT NEW approaches that are NOT already among the existing 20 and NOT duplicates of each other. Merge synonyms. Keep an approach only if it models BTC via a meaningfully different mechanism/driver than anything already covered. We want FULL BREADTH, so retain every truly additive idea (target 16-26), but drop anything that is just a restatement of an existing approach. For each, give why_distinct. ${GROUND}`,
  { label: 'dedupe:new', phase: 'Dedupe', schema: DEDUPE_SCHEMA }
)
log(`Deduped to ${newTax.approaches.length} distinct NEW approaches`)

// ===================== PHASE 4+5: DEEPDIVE NEW -> VERIFY =====================
const OUTPUTS = {
  type: 'object',
  required: ['appreciation_nominal', 'appreciation_real', 'volatility', 'corr_growth_eq', 'corr_value_eq', 'corr_fi_nominal', 'corr_tips', 'corr_gold', 'notes'],
  properties: {
    appreciation_nominal: { type: 'string' }, appreciation_real: { type: 'string' }, volatility: { type: 'string' },
    corr_growth_eq: { type: 'string' }, corr_value_eq: { type: 'string' }, corr_fi_nominal: { type: 'string' },
    corr_tips: { type: 'string' }, corr_gold: { type: 'string' }, horizon: { type: 'string' }, notes: { type: 'string' },
  },
}
const DEEPDIVE_SCHEMA = {
  type: 'object',
  required: ['name', 'family', 'source_type', 'description', 'medium_explanation', 'key_drivers', 'pros', 'cons', 'representative_sources', 'cited_outputs', 'synthesized_outputs', 'rich_notes'],
  properties: {
    name: { type: 'string' }, family: { type: 'string' }, source_type: { type: 'string', enum: SRC_ENUM },
    description: { type: 'string', description: '2-4 sentence summary' },
    medium_explanation: { type: 'string', description: '120-180 word MEDIUM explanation: mechanism, key inputs, what it implies for a 10-15yr BTC CMA' },
    key_drivers: { type: 'array', items: { type: 'string' } },
    pros: { type: 'array', items: { type: 'string' }, minItems: 2 },
    cons: { type: 'array', items: { type: 'string' }, minItems: 2 },
    representative_sources: {
      type: 'array', minItems: 1,
      items: { type: 'object', required: ['author_firm', 'title', 'year', 'link'],
        properties: { author_firm: { type: 'string' }, title: { type: 'string' }, year: { type: 'string' }, link: { type: 'string' } } },
    },
    cited_outputs: { ...OUTPUTS }, synthesized_outputs: { ...OUTPUTS },
    rich_notes: { type: 'string', description: '400-900 word retained brief: methodology, key relationships, quotes, historical fit, failure modes, on-record multi-year forecasts produced this way' },
  },
}
const VERDICT_SCHEMA = {
  type: 'object', required: ['numbers_credible', 'issues', 'corrections'],
  properties: {
    numbers_credible: { type: 'boolean' }, issues: { type: 'array', items: { type: 'string' } },
    missing_cons: { type: 'array', items: { type: 'string' } }, overstated_pros: { type: 'array', items: { type: 'string' } },
    corrections: { type: 'string' },
  },
}
function ddPrompt(a) {
  return `Deep-dive ONE NEW BTC-CMA approach. APPROACH: "${a.name}"\nFamily: ${a.family}\nSource type: ${a.source_type}\nWhy distinct: ${a.why_distinct}\nSeed sources: ${(a.seed_sources || []).join('; ')}\n\n` +
    `Research thoroughly. Produce: precise description; a 120-180 word MEDIUM explanation; key drivers; honest pros/cons (2+ each); real cited sources (author_firm, title, year, link — never fabricate); CITED outputs (appreciation nom & real, vol, correlations vs growth eq/value eq/nominal FI/TIPS/GOLD the literature publishes; "n/a (source silent)" where silent); SYNTHESIZED 10-15yr outputs (your reasoned estimate anchored to the realized decay baseline, correlations vs growth eq / value eq / nominal FI / TIPS / GOLD); and a 400-900 word rich_notes brief including any on-record multi-year forecasts produced this way. Be skeptical and represent critiques faithfully. ${GROUND}`
}
phase('Research')
const newResearched = await pipeline(
  newTax.approaches,
  (a) => agent(ddPrompt(a), { label: `dive:${a.name}`.slice(0, 55), phase: 'Research', schema: DEEPDIVE_SCHEMA }),
  (dive) => dive ? agent(
    `Adversarially VERIFY this new BTC-CMA deep-dive; try to refute its numbers and framing. Are cited numbers real & correctly attributed? Are synthesized 10-15yr figures defensible or hype given the realized decay (142->65->17%/yr), ~57% vol floor, and ~0 gold correlation? Missing cons? Overstated pros?\n\n${JSON.stringify(dive, null, 2)}`,
    { label: `verify:${dive.name}`.slice(0, 55), phase: 'Verify', schema: VERDICT_SCHEMA }
  ).then(v => ({ ...dive, verdict: v })) : null
)
const newApproaches = newResearched.filter(Boolean)
log(`Deep-dived + verified ${newApproaches.length} NEW approaches`)

// ===================== PHASE 6: RANK (score every approach) =====================
phase('Rank')
const EXISTING_META = [{"family":"scarcity-supply","source_type":"crypto_native"},{"family":"network-value","source_type":"academia"},{"family":"network-value","source_type":"crypto_native"},{"family":"cost-of-production","source_type":"academia"},{"family":"power-law","source_type":"crypto_native"},{"family":"store-of-value-TAM","source_type":"asset_manager"},{"family":"monetary-substitution","source_type":"academia"},{"family":"monetary-substitution","source_type":"academia"},{"family":"on-chain","source_type":"practitioner"},{"family":"factor-regression","source_type":"academia"},{"family":"options-implied","source_type":"practitioner"},{"family":"dcf-moneyness","source_type":"academia"},{"family":"dcf-moneyness","source_type":"academia"},{"family":"adoption-scurve","source_type":"asset_manager"},{"family":"portfolio-sizing","source_type":"asset_manager"},{"family":"asset-manager-LTCMA","source_type":"asset_manager"},{"family":"market-implied","source_type":"practitioner"},{"family":"bubble-hazard","source_type":"academia"},{"family":"return-process","source_type":"academia"},{"family":"survival-hazard","source_type":"academia"}]
const combined = evalsOk.map(e => ({
  name: e.name, index: e.index,
  family: (EXISTING_META[e.index] || {}).family || 'existing',
  source_type: (EXISTING_META[e.index] || {}).source_type || 'practitioner',
  blurb: e.medium_explanation, origin: 'existing',
})).concat(newApproaches.map(a => ({
  name: a.name, family: a.family, source_type: a.source_type,
  blurb: a.medium_explanation || a.description, pros: a.pros, cons: a.cons, syn: a.synthesized_outputs, origin: 'new',
})))
log(`Scoring ${combined.length} total approaches (${evalsOk.length} existing + ${newApproaches.length} new)`)

const SCORE_SCHEMA = {
  type: 'object',
  required: ['name', 'rigor', 'signal', 'robustness', 'data_ops', 'rationale'],
  properties: {
    name: { type: 'string', description: 'echo the approach name VERBATIM' },
    rigor: { type: 'integer', minimum: 1, maximum: 5, description: 'theoretical / methodological soundness' },
    signal: { type: 'integer', minimum: 1, maximum: 5, description: 'empirical explanatory / predictive power for 10-15yr BTC' },
    robustness: { type: 'integer', minimum: 1, maximum: 5, description: 'stability across regimes, esp. survives BTC regime breaks (halving-cycle breakdown, 2021 S2F break, ETF era)' },
    data_ops: { type: 'integer', minimum: 1, maximum: 5, description: 'data availability + operational ease of using it in a CMA process' },
    rationale: { type: 'string', description: '1-3 sentences justifying the scores' },
  },
}
const scores = (await pipeline(
  combined,
  (a) => agent(
    (a.origin === 'existing'
      ? `Read ${DIGEST} and find the approach at index ${a.index} (the ${a.index}-th element of its "approaches" array — pros/cons/synthesized_outputs are there). ` +
        `Approach: "${a.name}". Medium explanation: ${a.blurb}\n\n`
      : `APPROACH: ${a.name}\nFamily: ${a.family} | Source: ${a.source_type}\nWhat it is: ${a.blurb}\nPros: ${(a.pros || []).join('; ')}\nCons: ${(a.cons || []).join('; ')}\nSynthesized outputs: ${JSON.stringify(a.syn)}\n\n`) +
    `Score this BTC-CMA approach on four 1-5 dimensions for use in a 10-15yr CMA. Be discriminating — use the full 1-5 range, do not cluster at 3-4. ` +
    `rigor = theoretical/methodological soundness; signal = empirical explanatory/predictive power for BTC over 10-15yr; robustness = survives regime change incl. the halving-cycle breakdown, the 2021 S2F break, and the ETF-era correlation shift; data_ops = data availability + operational ease in a CMA process. Echo the name verbatim. ${GROUND}`,
    { label: `score:${a.name}`.slice(0, 55), phase: 'Rank', schema: SCORE_SCHEMA }
  )
)).filter(Boolean)
log(`Scored ${scores.length} approaches`)

// ===================== PHASE 7: ADJUDICATE =====================
phase('Adjudicate')
const ADJ_SCHEMA = {
  type: 'object',
  required: ['ranked', 'clusters', 'ensemble_recommendation', 'overall_notes'],
  properties: {
    ranked: {
      type: 'array',
      items: {
        type: 'object', required: ['name', 'overall', 'rank', 'tier', 'orthogonality', 'verdict'],
        properties: {
          name: { type: 'string', description: 'verbatim approach name' },
          overall: { type: 'integer', minimum: 0, maximum: 100, description: 'overall 0-100 score' },
          rank: { type: 'integer', description: 'global rank, 1 = best, unique' },
          tier: { type: 'string', enum: ['Core driver', 'Conditioning overlay', 'Context / cross-check', 'Reject as engine'] },
          orthogonality: { type: 'integer', minimum: 1, maximum: 5, description: 'how much INDEPENDENT signal it adds vs the rest of the field' },
          verdict: { type: 'string', description: 'one-line judgment' },
        },
      },
    },
    clusters: {
      type: 'array', description: 'group approaches by the underlying driver they ultimately rest on',
      items: { type: 'object', required: ['cluster_name', 'shared_driver', 'members'],
        properties: { cluster_name: { type: 'string' }, shared_driver: { type: 'string' }, members: { type: 'array', items: { type: 'string' } } } },
    },
    ensemble_recommendation: { type: 'string', description: 'which handful of orthogonal approaches to actually combine into the house BTC CMA, and how to weight/use them' },
    overall_notes: { type: 'string', description: 'cross-cutting signal map: where the field agrees/disagrees, what is redundant, what carries the marginal information' },
  },
}
const adj = await agent(
  `You are the adjudicator producing the analyst's OWN RANKING of every BTC-CMA approach. Here are the per-dimension scores (rigor/signal/robustness/data_ops, each 1-5) with rationales:\n\n${JSON.stringify(scores, null, 2)}\n\n` +
  `And the full field with families:\n${combined.map(a => `- [${a.family} / ${a.source_type}] ${a.name}`).join('\n')}\n\n` +
  `Produce: (1) a GLOBAL RANKING — every approach gets a unique integer rank (1=best for building a 10-15yr BTC CMA), an overall 0-100 score (use the dimension scores but weight signal & robustness most heavily for a long-horizon CMA), an orthogonality score (1-5: independent information vs the rest), a tier (Core driver / Conditioning overlay / Context / cross-check / Reject as engine), and a one-line verdict. Note that for BTC the decay-anchor dominates, so a method's value is mostly in the SHAPE/conditioning it adds (tails, regime, correlation) not its level forecast. (2) CLUSTERS grouping approaches by the underlying driver they ultimately rest on (e.g. several reduce to global liquidity, or to adoption/network, or to scarcity/supply, or to realized-vol carry-forward) — this exposes redundancy. (3) An ENSEMBLE recommendation: the small set of mutually-orthogonal approaches to actually combine into the house BTC CMA and how to use each. (4) overall_notes: the signal map. Echo names verbatim. ${GROUND}`,
  { label: 'adjudicate', phase: 'Adjudicate', schema: ADJ_SCHEMA }
)
log(`Adjudicated: ${adj.ranked.length} ranked, ${adj.clusters.length} driver clusters`)

// ===================== PHASE 8: COMPLETENESS =====================
phase('Completeness')
const COMPLETE_SCHEMA = {
  type: 'object', required: ['still_missing', 'breadth_assessment'],
  properties: {
    still_missing: { type: 'array', items: { type: 'object', required: ['name', 'why'], properties: { name: { type: 'string' }, why: { type: 'string' } } } },
    breadth_assessment: { type: 'string' },
  },
}
const allNames = evalsOk.map(e => e.name).concat(newApproaches.map(a => a.name))
const finalCritic = await agent(
  `The full BTC-CMA approach field is now:\n${allNames.map(n => '- ' + n).join('\n')}\n\n` +
  `As a completeness critic: name any genuinely DISTINCT approach family STILL missing (different mechanism, not a restatement) — at most 5. Then give a one-paragraph breadth_assessment: is the field now comprehensive for a 10-15yr BTC CMA? ${GROUND}`,
  { label: 'completeness', phase: 'Completeness', schema: COMPLETE_SCHEMA }
)

return {
  existing_evals: evalsOk,
  new_approaches: newApproaches,
  scores,
  ranking: adj.ranked,
  clusters: adj.clusters,
  ensemble_recommendation: adj.ensemble_recommendation,
  signal_notes: adj.overall_notes,
  still_missing: finalCritic.still_missing,
  breadth_assessment: finalCritic.breadth_assessment,
}
