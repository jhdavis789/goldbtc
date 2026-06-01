# Gold as an inflation hedge — before and after hedging its duration

**Experiment (monthly, Jan 1975 – Dec 2025, ~50y).** Does gold look like a
better inflation hedge once you strip out its interest-rate *duration*?

## The pricing approach (the paper)

The framing comes from the Chicago Fed Letter No. 464, **"What Drives Gold
Prices?"** (2021), formalized in **Jermann, "Gold's Value as an Investment"**
(NBER w31386, 2023): gold is a **long real-duration asset**. Its price is the
present value of a perpetual real "service flow,"

```
P_gold  ≈  service_flow / real_rate
```

so `d ln(P_gold) / d(real yield) = −Duration`, and the paper backs out a real
duration of roughly **18 years**. The mechanism that matters for inflation
hedging: when inflation rises, *real-rate expectations* tend to rise too (the
Fed tightens), and gold's long duration then pushes its price **down** —
mechanically cancelling part of the inflation-hedge channel.

## How the duration is "backed out" here

- **Level (paper-style)** — `ln(P_gold)` on the real-yield *level*:
  full-sample slope ⇒ **≈ 28y** duration (t = −6.4); **2000–2025 ⇒ ≈ 51y**
  (t = −10); but **1975–1999 ⇒ −16y** — in the inflationary era gold *rose*
  as real yields rose.
- **Return beta** — monthly gold returns on monthly yield *changes* (the
  tradeable, hedgeable sensitivity): full-sample ≈ **0y / insignificant**;
  **2000–2025 ⇒ ≈ 4y, t ≈ −4**.

The single most important fact: **gold only developed measurable "duration"
after ~2000.** Its rolling correlation with 10Y-Treasury-futures returns is
~0/negative through the 1970s–90s and **+0.2 to +0.5 since 2000** (see
`regime_shift.png`). So over the *full* 50 years there is, on average, almost
no duration to hedge.

## Gold's CPI beta, RAW vs DURATION-HEDGED

Hedge = overlay a **short 10Y-Treasury-futures** position sized to neutralize
gold's exposure to Treasury-futures returns. Beta = gold return per 1.0 of
realized CPI inflation (β = 1 ⇒ keeps pace 1-for-1). Newey–West t-stats.

| Sample | Horizon | RAW β (t) | HEDGED β (t) |
|---|---|---|---|
| **Full 1975–2025** | monthly | 1.43 (1.8) | 1.55 (2.0) |
| | 12-month | 1.82 (1.0) | 1.96 (1.1) |
| **1975–1999** | monthly | 2.30 (1.3) | 2.13 (1.2) |
| | 12-month | 3.75 (1.8) | 3.57 (1.7) |
| **2000–2025** | monthly | 1.43 (2.8) | **2.05 (3.9)** |
| | 12-month | 0.80 (0.5) | **1.71 (1.1)** |

Duration-matched short (size short futures to gold's ~4y real duration),
2000–2025: hedged monthly β = **2.01 (t = 3.9)** vs raw 1.43; hedged 12-month
β = **1.65** vs raw 0.71.

## Conclusion

1. **Over the full 50 years**, gold's CPI beta is positive but statistically
   weak (~1.4 monthly, ~1.8 over 12m), and **duration-hedging barely changes
   it** — because across the whole sample gold has had ~zero average duration.
   So at the headline level, the duration story does *not* rescue gold.

2. **Your hypothesis is correct, but it is a post-2000 phenomenon.** Since 2000
   gold genuinely trades as a long-duration real asset (significant negative
   real-yield beta; +0.2–0.5 correlation with Treasuries). In that regime the
   raw inflation beta is weak/insignificant — **0.8 (t≈0.5) over 12 months** —
   and **hedging gold's duration with short Treasury futures roughly doubles
   it to ~1.7–2.0 and sharply improves significance** (monthly t 2.8 → 3.9).
   That is exactly the effect you described.

3. **In 1975–1999 there was nothing to hedge** — gold and rates rose together
   in the high-inflation era (negative measured duration), so the hedge
   slightly *hurts*. This is why the full-sample average washes out.

**Bottom line:** gold's duration *is* a drag on its inflation-hedge quality,
and removing it with Treasury futures materially improves the inflation beta —
but only in the modern (real-rate-driven) regime since ~2000. Caveats: the
real yield is a constructed ex-ante proxy (TIPS start only in 2003); hedge
ratios are in-sample; monthly CPI is NSA (hence the 12-month/YoY cross-checks).

## Files
- `analysis.py` — full regressions (duration back-out + raw/hedged betas by era)
- `plot_regime.py` — generates `regime_shift.png`
- `results.txt` — captured regression output
- `*.csv` — input data (gold, CPI, 10Y yield)
