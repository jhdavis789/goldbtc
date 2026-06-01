"""Rolling R^2 (60-month window), 1996-2025.
Dependent = RAW GOLD PRICE.  Three explanatory option sets:

   A. REAL          : real 10Y yield
   B. REAL + CPIexp : real 10Y yield + expected inflation ("CPI expectation")
   C. CPI only      : expected inflation
   (bonus) CPI level: the CPI index itself ("gold tracks the price level")

real 10Y = nominal 10Y - expected inflation;  expected inflation = EWMA(halflife
24m) of YoY CPI.  Reported for raw price and for log price (the pricing-model
form, P ~ service/real_rate => ln P ~ -Duration*real_rate).
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

W=60
g=pd.read_csv("gold_monthly.csv"); c=pd.read_csv("cpi.csv"); b=pd.read_csv("bond10y.csv")
g["m"]=pd.PeriodIndex(g["Date"],freq="M")
c["m"]=pd.to_datetime(c["Date"]).dt.to_period("M")
b["m"]=pd.to_datetime(b["Date"]).dt.to_period("M")
df=(g[["m","Price"]].rename(columns={"Price":"gold"})
    .merge(c[["m","Index"]].rename(columns={"Index":"cpi"}),on="m")
    .merge(b[["m","Rate"]].rename(columns={"Rate":"y10"}),on="m")
    .sort_values("m").reset_index(drop=True))
df["lg"]=np.log(df["gold"])
infl_yoy=np.log(df["cpi"]).diff(12)*100
df["pexp"]=infl_yoy.ewm(halflife=24).mean()        # expected inflation, %
df["real10"]=df["y10"]-df["pexp"]                  # real 10Y, %
df["t"]=df["m"].dt.to_timestamp()

def roll_r2(ycol,Xcols):
    y=df[ycol].values
    X=np.column_stack([df[cc].values for cc in Xcols])
    out=np.full(len(df),np.nan)
    for i in range(W-1,len(df)):
        sl=slice(i-W+1,i+1); yy=y[sl]; XX=X[sl]
        m=~(np.isnan(yy)|np.isnan(XX).any(axis=1))
        if m.sum()<W*0.8: continue
        yy=yy[m]; A=np.column_stack([np.ones(m.sum()),XX[m]])
        beta,_,_,_=np.linalg.lstsq(A,yy,rcond=None)
        yh=A@beta; ss=np.sum((yy-yy.mean())**2)
        out[i]=1-np.sum((yy-yh)**2)/ss if ss>0 else np.nan
    return out

specs=[("A real","real",["real10"]),
       ("B real+CPIexp","real_cpi",["real10","pexp"]),
       ("C CPI only","cpi",["pexp"]),
       ("D CPI level","lvl",["cpi"])]

def block_table(ycol,title):
    for lab,key,X in specs: df[f"{ycol}_{key}"]=roll_r2(ycol,X)
    w=df[df["m"]>="1996-01"]
    print(f"\n=== {title} :  rolling 60m R^2  ===")
    print(f"{'period':10s}"+"".join(f"{lab:>15s}" for lab,_,_ in specs))
    for lo in range(1996,2026,5):
        s=w[(w['m']>=f'{lo}-01')&(w['m']<=f'{lo+4}-12')]
        print(f"{lo}-{lo+4:<5d}"+"".join(f"{s[f'{ycol}_{k}'].mean():>15.3f}" for _,k,_ in specs))
    print(f"{'1996-2025':10s}"+"".join(f"{w[f'{ycol}_{k}'].mean():>15.3f}" for _,k,_ in specs))
    print(f"{'latest':10s}"+"".join(f"{w[f'{ycol}_{k}'].iloc[-1]:>15.3f}" for _,k,_ in specs)
          +f"   (end {w['m'].iloc[-1]})")
    return w

w=block_table("gold","RAW GOLD PRICE")        # primary: what you asked for
block_table("lg","LOG GOLD PRICE (robustness)")

plt.figure(figsize=(11,5.2))
plt.plot(w["t"],w["gold_real"],color="#2c7fb8",lw=1.9,label="A. real rates only")
plt.plot(w["t"],w["gold_real_cpi"],color="#111",lw=2.1,label="B. real rates + CPI expectation")
plt.plot(w["t"],w["gold_cpi"],color="#c0392b",lw=1.9,label="C. just CPI (expected inflation)")
plt.plot(w["t"],w["gold_lvl"],color="#999",lw=1.3,ls="--",label="(bonus) CPI index level")
plt.title("Rolling 60-month R²: RAW gold price vs the three options, 1996–2025")
plt.ylabel("R²"); plt.ylim(0,1); plt.grid(alpha=.25); plt.legend(loc="lower left",fontsize=9)
plt.tight_layout(); plt.savefig("rolling_r2.png",dpi=130); print("\nwrote rolling_r2.png")
