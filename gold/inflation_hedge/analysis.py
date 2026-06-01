"""
Gold as an inflation hedge, before and after hedging its duration.
========================================================================

Motivation
----------
Gold is frequently described as an inflation hedge, yet its empirical
inflation beta is famously weak. A leading explanation (Chicago Fed Letter
No. 464, "What Drives Gold Prices?", 2021; Jermann, NBER w31386, 2023) is
that gold behaves like a very long *real-duration* asset: its price is the
present value of a perpetual real "service flow,"

        P_gold  ~  service_flow / real_rate ,

so gold's price is inversely sensitive to long-term REAL yields with an
empirical duration on the order of ~18 years. When inflation rises, real-rate
expectations often rise too (the Fed tightens), and gold's long duration then
drives its price DOWN -- mechanically offsetting the inflation-hedge channel.

Experiment (monthly, 1975-2025, ~50y)
-------------------------------------
  (A) Back out gold's empirical duration: regress gold returns on changes in
      (i) the NOMINAL 10Y yield and (ii) a constructed REAL 10Y yield.
  (B) Regress gold returns on realized CPI inflation            -> RAW beta.
  (C) Overlay a SHORT 10Y-Treasury-futures position sized to neutralise gold's
      yield exposure, then regress on inflation                 -> HEDGED beta.
  Done for the full sample and split 1975-1999 / 2000-2025, because the
  gold<->rates relationship changed sign around 2000.

Data (public, GitHub-mirrored):
  gold_monthly.csv  London PM gold fix, USD/oz   (datasets/gold-prices)
  cpi.csv           US CPI index (NSA)           (datasets/cpi-us)
  bond10y.csv       10Y constant-maturity yield  (datasets/bond-yields-us-10y)
Real yield is constructed as nominal 10Y minus an EWMA (halflife 24m) of YoY
CPI inflation, used as an ex-ante expected-inflation proxy (TIPS only exist
from 2003, too short for a 50y study).
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

START, END   = "1975-01", "2025-12"     # US private gold ownership legal 1/1/1975
FUT_DURATION = 7.0                       # modified duration of a 10Y note future

# ---------------------------------------------------------------- load + merge
g = pd.read_csv("gold_monthly.csv");  c = pd.read_csv("cpi.csv");  b = pd.read_csv("bond10y.csv")
g["m"] = pd.PeriodIndex(g["Date"], freq="M")
c["m"] = pd.to_datetime(c["Date"]).dt.to_period("M")
b["m"] = pd.to_datetime(b["Date"]).dt.to_period("M")
df = (g[["m", "Price"]].rename(columns={"Price": "gold"})
      .merge(c[["m", "Index"]].rename(columns={"Index": "cpi"}), on="m")
      .merge(b[["m", "Rate"]].rename(columns={"Rate": "y10"}), on="m")
      .sort_values("m").reset_index(drop=True))

# ---------------------------------------------------------------- transforms
df["g_ret"]   = np.log(df["gold"]).diff()
df["infl_m"]  = np.log(df["cpi"]).diff()
df["infl_yoy"] = np.log(df["cpi"]).diff(12) * 100          # %, YoY
exp_infl       = df["infl_yoy"].ewm(halflife=24).mean()    # smooth expected inflation, %
df["real10"]   = df["y10"] - exp_infl                      # ex-ante real 10Y, %
df["dy"]       = df["y10"].diff()   / 100.0                # change nominal yield (dec)
df["dreal"]    = df["real10"].diff() / 100.0              # change real yield (dec)
df["g_ret12"]  = np.log(df["gold"]).diff(12)
df["infl_12"]  = np.log(df["cpi"]).diff(12)

df = df[(df["m"] >= START) & (df["m"] <= END)].reset_index(drop=True)
reg = df.dropna(subset=["g_ret", "infl_m", "dy", "dreal"]).copy()

# ---------------------------------------------------------------- helpers
def fit(y, X, lags):
    X = sm.add_constant(X)
    return sm.OLS(y, X, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": lags})

def line(label, res, key):
    print(f"    {label:30s} beta={res.params[key]:+7.3f}  t={res.tvalues[key]:+5.2f}"
          f"   R2={res.rsquared:5.3f}  n={int(res.nobs)}")

def mask(frame, lo, hi):
    return frame[(frame["m"] >= lo) & (frame["m"] <= hi)]

SUBS = [("FULL 1975-2025", "1975-01", "2025-12"),
        ("1975-1999     ", "1975-01", "1999-12"),
        ("2000-2025     ", "2000-01", "2025-12")]

print("=" * 78)
print(f"GOLD INFLATION-HEDGE EXPERIMENT   {reg['m'].min()}..{reg['m'].max()}  ({len(reg)} months)")
print("=" * 78)

# ====================================================================
# (A) Back out gold's empirical duration
# ====================================================================
print("\n[A0] DURATION BACK-OUT, PAPER STYLE  (log price LEVEL on real-yield LEVEL)")
print("     d ln(P_gold)/d(real yield) = -Duration  (Chicago Fed get ~18y)")
for tag, lo, hi in SUBS:
    s = mask(reg, lo, hi)
    r = fit(np.log(s["gold"]), s[["real10"]], 12)      # real10 in %, slope per 1%-pt
    print(f"     {tag}: level duration = {-r.params['real10']*100:6.1f}y"
          f"   t={r.tvalues['real10']:+5.2f}   R2={r.rsquared:5.3f}")

print("\n[A] DURATION BACK-OUT  (monthly gold return on yield change; duration = -beta)")
print("    --- vs NOMINAL 10Y yield ---")
for tag, lo, hi in SUBS:
    s = mask(reg, lo, hi); r = fit(s["g_ret"], s[["dy"]], 6)
    print(f"    {tag}: dur(nom) ={-r.params['dy']:6.1f}y   t={r.tvalues['dy']:+5.2f}   R2={r.rsquared:5.3f}")
print("    --- vs REAL 10Y yield (constructed) ---")
for tag, lo, hi in SUBS:
    s = mask(reg, lo, hi); r = fit(s["g_ret"], s[["dreal"]], 6)
    print(f"    {tag}: dur(real)={-r.params['dreal']:6.1f}y   t={r.tvalues['dreal']:+5.2f}   R2={r.rsquared:5.3f}")

# gold's contemporaneous tie to a long-Treasury-futures return, by era
print("\n    --- gold vs 10Y-futures return (corr; >0 => gold acts long-duration) ---")
reg["fut_ret"] = -FUT_DURATION * reg["dy"]
for tag, lo, hi in SUBS:
    s = mask(reg, lo, hi)
    print(f"    {tag}: corr(gold, futures) = {s['g_ret'].corr(s['fut_ret']):+5.2f}")

# ====================================================================
# (B)/(C) RAW vs DURATION-HEDGED inflation beta, per era
#   Hedge = beta-hedge gold to the futures return (the tradeable instrument):
#     h = cov(gold,fut)/var(fut)  (sign tells you long/short futures)
#     g_hedged = g_ret - h * fut_ret      [estimated within each sample]
# ====================================================================
print("\n[B/C] INFLATION BETA  (gold return per 1.0 of realized CPI inflation)")
print("      hedge = neutralise gold's exposure to 10Y-futures returns\n")
print(f"      {'sample':16s} {'horizon':10s} {'RAW beta':>10s} {'(t)':>6s} {'HEDGED':>9s} {'(t)':>6s} {'hedge_h':>8s}")

def betas_for(s):
    h = np.cov(s["g_ret"], s["fut_ret"])[0, 1] / np.var(s["fut_ret"])
    s = s.copy()
    s["g_hedged"]   = s["g_ret"] - h * s["fut_ret"]
    s["g_hedged12"] = s["g_hedged"].rolling(12).sum()
    return s, h

for tag, lo, hi in SUBS:
    s, h = betas_for(mask(reg, lo, hi))
    rr  = fit(s["g_ret"],    s[["infl_m"]], 6)
    rh  = fit(s["g_hedged"], s[["infl_m"]], 6)
    print(f"      {tag:16s} {'monthly':10s} {rr.params['infl_m']:>10.2f} {rr.tvalues['infl_m']:>6.2f}"
          f" {rh.params['infl_m']:>9.2f} {rh.tvalues['infl_m']:>6.2f} {h:>8.2f}")
    s12 = s.dropna(subset=["g_ret12", "g_hedged12", "infl_12"])
    rr  = fit(s12["g_ret12"],    s12[["infl_12"]], 18)
    rh  = fit(s12["g_hedged12"], s12[["infl_12"]], 18)
    print(f"      {'':16s} {'12-month':10s} {rr.params['infl_12']:>10.2f} {rr.tvalues['infl_12']:>6.2f}"
          f" {rh.params['infl_12']:>9.2f} {rh.tvalues['infl_12']:>6.2f}")

# ====================================================================
# (D) Real-rate-DURATION-matched hedge (the literal "short 18y of duration")
#     Size the SHORT nominal-futures position to gold's REAL duration, post-2000
#     where that duration is large & significant, and see the inflation beta.
# ====================================================================
print("\n[D] DURATION-MATCHED SHORT (size short futures to gold's REAL duration), 2000-2025")
s = mask(reg, "2000-01", "2025-12").copy()
Dreal = -fit(s["g_ret"], s[["dreal"]], 6).params["dreal"]      # gold real duration (yrs)
w = Dreal / FUT_DURATION                                       # units of futures to SHORT
s["g_hedged"]   = s["g_ret"] - (-w) * s["fut_ret"]  # short w units => -(-w)=+w*fut? see note
# short w units of futures contributes  +w*FUT_DURATION*dy = -w*fut_ret to the portfolio:
s["g_hedged"]   = s["g_ret"] - w * s["fut_ret"]
s["g_hedged12"] = s["g_hedged"].rolling(12).sum()
print(f"    gold real duration = {Dreal:.1f}y  ->  short {w:.2f} units of 10Y futures per $1 gold")
for dep, ind, lg, tag in [("g_ret","infl_m",6,"RAW    monthly"),
                          ("g_hedged","infl_m",6,"HEDGED monthly"),
                          ("g_ret12","infl_12",18,"RAW    12-month"),
                          ("g_hedged12","infl_12",18,"HEDGED 12-month")]:
    ss = s.dropna(subset=[dep, ind]); r = fit(ss[dep], ss[[ind]], lg)
    line(tag, r, ind)
