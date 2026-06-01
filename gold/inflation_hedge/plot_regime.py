"""Visualise the gold/rates regime shift and the duration-hedge effect.
Panel 1: rolling 60m correlation of gold returns vs 10Y-futures returns
         (>0 => gold trades like a long-duration asset).
Panel 2: rolling 60m CPI-inflation beta of gold, RAW vs duration-HEDGED.
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FUT_DURATION = 7.0
g = pd.read_csv("gold_monthly.csv"); c = pd.read_csv("cpi.csv"); b = pd.read_csv("bond10y.csv")
g["m"]=pd.PeriodIndex(g["Date"],freq="M")
c["m"]=pd.to_datetime(c["Date"]).dt.to_period("M")
b["m"]=pd.to_datetime(b["Date"]).dt.to_period("M")
df=(g[["m","Price"]].rename(columns={"Price":"gold"})
    .merge(c[["m","Index"]].rename(columns={"Index":"cpi"}),on="m")
    .merge(b[["m","Rate"]].rename(columns={"Rate":"y10"}),on="m")
    .sort_values("m").reset_index(drop=True))
df["t"]=df["m"].dt.to_timestamp()
df["g_ret"]=np.log(df["gold"]).diff()
df["infl_m"]=np.log(df["cpi"]).diff()
df["dy"]=df["y10"].diff()/100.0
df["fut"]=-FUT_DURATION*df["dy"]
df=df[(df["m"]>="1975-01")&(df["m"]<="2025-12")].reset_index(drop=True)

W=60
df["corr_gf"]=df["g_ret"].rolling(W).corr(df["fut"])

def roll_beta(y,x,w):
    out=np.full(len(y),np.nan)
    for i in range(w-1,len(y)):
        Y=y[i-w+1:i+1]; X=x[i-w+1:i+1]
        m=~(np.isnan(Y)|np.isnan(X))
        if m.sum()>w*0.8:
            out[i]=np.polyfit(X[m],Y[m],1)[0]
    return out
# in-sample-per-window hedge: h from same window, then beta vs inflation
gret=df["g_ret"].values; fut=df["fut"].values; infl=df["infl_m"].values
raw_b=roll_beta(gret,infl,W)
hed=np.full(len(df),np.nan)
hedged_series=np.full(len(df),np.nan)
hbeta=np.full(len(df),np.nan)
for i in range(W-1,len(df)):
    G=gret[i-W+1:i+1]; F=fut[i-W+1:i+1]; I=infl[i-W+1:i+1]
    m=~(np.isnan(G)|np.isnan(F)|np.isnan(I))
    if m.sum()>W*0.8:
        h=np.cov(G[m],F[m])[0,1]/np.var(F[m])
        Gh=G-h*F
        hbeta[i]=np.polyfit(I[m],Gh[m],1)[0]
df["raw_b"]=raw_b; df["hed_b"]=hbeta

fig,ax=plt.subplots(2,1,figsize=(11,8),sharex=True)
ax[0].axhline(0,color="0.6",lw=.8)
ax[0].plot(df["t"],df["corr_gf"],color="#b8860b",lw=1.8)
ax[0].fill_between(df["t"],0,df["corr_gf"],where=df["corr_gf"]>0,color="#b8860b",alpha=.18)
ax[0].set_title("Gold develops 'duration' only after ~2000\n"
                "rolling 60-month corr( gold returns , 10Y-Treasury-futures returns )",fontsize=11)
ax[0].set_ylabel("correlation")
ax[0].annotate("1970s-80s: gold & rates rise together\n(no duration to hedge)",
               xy=(pd.Timestamp("1982-01-01"),-0.25),fontsize=8,color="0.3")
ax[0].annotate("2000s+: gold trades as a\nlong-duration real asset",
               xy=(pd.Timestamp("2010-01-01"),0.35),fontsize=8,color="0.3")

ax[1].axhline(1,color="0.7",lw=.8,ls="--")
ax[1].plot(df["t"],df["raw_b"],color="#888",lw=1.6,label="RAW gold")
ax[1].plot(df["t"],df["hed_b"],color="#c0392b",lw=1.8,label="duration-HEDGED gold")
ax[1].set_title("Rolling 60-month CPI-inflation beta of gold (monthly): "
                "hedging duration lifts the inflation beta post-2000",fontsize=11)
ax[1].set_ylabel("inflation beta"); ax[1].legend(loc="upper left",fontsize=9)
ax[1].set_ylim(-6,10)
for a in ax: a.axvspan(pd.Timestamp("2000-01-01"),pd.Timestamp("2025-12-01"),color="#3498db",alpha=.05)
fig.tight_layout()
fig.savefig("regime_shift.png",dpi=130)
print("wrote regime_shift.png")
