#!/usr/bin/env python3
"""
empirical_anchor.py — scripted empirical baseline for the Bitcoin CMA literature review.

BTC twin of GOLDBTC/gold/cma_litreview/empirical_anchor.py. Computes, from real price
history (no eyeballing), the realized figures that ground the "synthesized" appreciation /
volatility / correlation column of the lit review:

  * annualized price appreciation of BTC (nominal and CPI-real)
  * annualized volatility of BTC (realized, from monthly log returns)
  * correlation of BTC monthly returns vs:
        - growth equities       (IWF, Russell 1000 Growth, total return)
        - value equities        (IWD, Russell 1000 Value, total return)
        - fixed income nominal  (AGG, US Aggregate, total return)
        - inflation-linked TIPS  (TIP, US TIPS, total return)
        - GOLD                   (LBMA PM fix)   <-- BTC-specific addition ("digital gold")
    plus broad USD (DTWEXBGS) as context.

Three windows: full common window, trailing ~10y, trailing ~5y (BTC's character changes
hard over its life — early window is a different asset than the institutional-ETF era).

Data
----
* BTC       : Coinmetrics community API PriceUSD (cached btc/data/raw/btc_coinmetrics.csv).
              Coinmetrics is the calc agent for the CME CF Bitcoin Reference Rate (BRRNY);
              registered in research/DATA_SOURCES.md.
* Gold      : LBMA Gold Price PM (gold/factor_model/data/raw/gold_pm.csv).
* USD, CPI  : FRED DTWEXBGS / CPIAUCSL (gold/factor_model/data/raw/usd.csv, cpi_full.csv).
* AGG       : gold/factor_model/data/raw/agg.csv (Yahoo total-return).
* IWF/IWD/TIP: fetched fresh via Yahoo v8 chart (adjusted close = total return), the SAME
              source already registered for the factor model in DATA_SOURCES.md.

Output: empirical_anchor.json in this directory.
"""
from __future__ import annotations
import csv
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLD_RAW = HERE.parent.parent / "gold" / "factor_model" / "data" / "raw"
BTC_CSV = HERE.parent / "data" / "raw" / "btc_coinmetrics.csv"

# Tickers we still need (total return via adjusted close). Same Yahoo source already
# registered for the gold factor model — no new data source. urllib hits SSL cert errors
# on this Mac, so fetch via curl (system cert store), per DATA_SOURCES.md note.
YAHOO_TR = {
    "IWF": ("growth_eq", "Russell 1000 Growth, total return (iShares IWF)"),
    "IWD": ("value_eq",  "Russell 1000 Value, total return (iShares IWD)"),
    "TIP": ("tips",      "US TIPS, total return (iShares TIP)"),
}
YAHOO_URL = ("https://query1.finance.yahoo.com/v8/finance/chart/{t}"
             "?period1=504921600&period2=9999999999&interval=1d")


def fetch_yahoo_tr(ticker: str) -> dict[str, float]:
    """Return {YYYY-MM-DD: adjclose} daily for a ticker, via curl (SSL on this Mac)."""
    url = YAHOO_URL.format(t=ticker)
    out = subprocess.run(
        ["curl", "-s", "-A", "Mozilla/5.0 (research; btc cma litreview)", url],
        capture_output=True, text=True, timeout=90,
    )
    res = json.loads(out.stdout)["chart"]["result"][0]
    ts = res["timestamp"]
    adj = res["indicators"]["adjclose"][0]["adjclose"]
    series = {}
    for t, v in zip(ts, adj):
        if v is None:
            continue
        d = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")
        series[d] = float(v)
    return series


def read_csv_series(path: Path, date_col=0, val_col=1) -> dict[str, float]:
    """Read a 2-col CSV (date,value); skip header + non-numeric."""
    out = {}
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) <= max(date_col, val_col):
                continue
            d, v = row[date_col].strip(), row[val_col].strip()
            if not d or d.lower().startswith("date"):
                continue
            try:
                out[d] = float(v)
            except ValueError:
                continue
    return out


def read_btc_priceusd(path: Path) -> dict[str, float]:
    """Coinmetrics CSV -> {YYYY-MM-DD: PriceUSD}, skipping empty PriceUSD rows."""
    out = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            d, v = row.get("time", "").strip(), row.get("PriceUSD", "").strip()
            if not d or not v:
                continue
            try:
                out[d] = float(v)
            except ValueError:
                continue
    return out


def to_month_end(daily: dict[str, float]) -> dict[str, float]:
    by_month: dict[str, tuple[str, float]] = {}
    for d, v in daily.items():
        ym = d[:7]
        if ym not in by_month or d > by_month[ym][0]:
            by_month[ym] = (d, v)
    return {ym: v for ym, (_, v) in by_month.items()}


def monthly_log_returns(month_level: dict[str, float]) -> dict[str, float]:
    months = sorted(month_level)
    rets = {}
    for i in range(1, len(months)):
        a, b = month_level[months[i - 1]], month_level[months[i]]
        if a > 0 and b > 0:
            rets[months[i]] = math.log(b / a)
    return rets


def mean(xs): return sum(xs) / len(xs)


def std(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def corr(xs, ys):
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else float("nan")


def ann_return_from_levels(month_level: dict[str, float]) -> float:
    months = sorted(month_level)
    n_years = (len(months) - 1) / 12.0
    if n_years <= 0:
        return float("nan")
    return (month_level[months[-1]] / month_level[months[0]]) ** (1 / n_years) - 1


def window(series: dict[str, float], start_ym: str | None) -> dict[str, float]:
    if start_ym is None:
        return series
    return {k: v for k, v in series.items() if k >= start_ym}


def main():
    btc_daily = read_btc_priceusd(BTC_CSV)
    gold_daily = read_csv_series(GOLD_RAW / "gold_pm.csv")
    usd_daily = read_csv_series(GOLD_RAW / "usd.csv")
    agg_daily = read_csv_series(GOLD_RAW / "agg.csv")
    cpi_path = GOLD_RAW / "cpi_full.csv" if (GOLD_RAW / "cpi_full.csv").exists() else GOLD_RAW / "cpi.csv"
    cpi_m = {k[:7]: v for k, v in read_csv_series(cpi_path).items()}

    fetched = {}
    for tkr, (name, _desc) in YAHOO_TR.items():
        print(f"fetching {tkr} ...", flush=True)
        fetched[name] = fetch_yahoo_tr(tkr)

    levels = {
        "btc":       to_month_end(btc_daily),
        "gold":      to_month_end(gold_daily),
        "usd":       to_month_end(usd_daily),
        "fi_nom":    to_month_end(agg_daily),
        "growth_eq": to_month_end(fetched["growth_eq"]),
        "value_eq":  to_month_end(fetched["value_eq"]),
        "tips":      to_month_end(fetched["tips"]),
    }
    rets = {k: monthly_log_returns(v) for k, v in levels.items()}

    asset_labels = {
        "growth_eq": "Growth equities (IWF)",
        "value_eq":  "Value equities (IWD)",
        "fi_nom":    "Fixed income, nominal (AGG)",
        "tips":      "Inflation-linked / TIPS (TIP)",
        "gold":      "Gold (LBMA PM)",
        "usd":       "Broad USD (DTWEXBGS) [context]",
    }

    def block(start_ym):
        b_lvl = window(levels["btc"], start_ym)
        b_ret = window(rets["btc"], start_ym)
        out = {
            "n_months_btc": len(b_ret),
            "btc_first_month": min(b_lvl) if b_lvl else None,
            "btc_last_month": max(b_lvl) if b_lvl else None,
            "btc_appreciation_nominal_annual": round(ann_return_from_levels(b_lvl), 4),
            "btc_vol_annual": round(std(list(b_ret.values())) * math.sqrt(12), 4),
            "correlations": {},
        }
        cpi_w = window(cpi_m, start_ym)
        if cpi_w and b_lvl:
            common = sorted(set(b_lvl) & set(cpi_w))
            if len(common) > 12:
                nom = ann_return_from_levels({m: b_lvl[m] for m in common})
                infl = ann_return_from_levels({m: cpi_w[m] for m in common})
                out["btc_appreciation_real_annual"] = round((1 + nom) / (1 + infl) - 1, 4)
                out["cpi_inflation_annual"] = round(infl, 4)
        for key, label in asset_labels.items():
            a = window(rets[key], start_ym)
            common = sorted(set(b_ret) & set(a))
            if len(common) > 12:
                bv = [b_ret[m] for m in common]
                av = [a[m] for m in common]
                out["correlations"][key] = {
                    "label": label,
                    "corr": round(corr(bv, av), 3),
                    "n_months": len(common),
                    "asset_appreciation_annual": round(ann_return_from_levels(window(levels[key], common[0])), 4),
                    "asset_vol_annual": round(std(av) * math.sqrt(12), 4),
                }
        return out

    last_ym = max(rets["btc"])
    y10, mm = int(last_ym[:4]) - 10, last_ym[5:7]
    y5 = int(last_ym[:4]) - 5
    ten_y_start = f"{y10}-{mm}"
    five_y_start = f"{y5}-{mm}"

    result = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "month-end levels; monthly log returns; vol = stdev(monthly)·sqrt(12); "
                  "appreciation = geometric annualized from month-end levels; real via CPIAUCSL.",
        "note": "Empirical realized BTC baseline only — anchors the synthesized CMA column; not a forecast. "
                "BTC history is short and regime-shifting; the trailing-5y/10y windows matter more for a "
                "10-15yr forward CMA than the full window (which is dominated by the 2010-2013 micro-cap era).",
        "data_sources": {
            "btc": "Coinmetrics community API PriceUSD (BRRNY calc-agent series)",
            "gold": "LBMA Gold Price PM",
            "equities_fi_tips": "Yahoo v8 adjusted close (IWF/IWD/AGG/TIP, total return)",
            "usd_cpi": "FRED DTWEXBGS / CPIAUCSL",
        },
        "full_window": block(None),
        "trailing_10y": block(ten_y_start),
        "trailing_10y_start": ten_y_start,
        "trailing_5y": block(five_y_start),
        "trailing_5y_start": five_y_start,
    }
    out_path = HERE / "empirical_anchor.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")
    for wname in ("full_window", "trailing_10y", "trailing_5y"):
        w = result[wname]
        print(f"\n{wname.upper()} {w['btc_first_month']}..{w['btc_last_month']}  (n={w['n_months_btc']} mo)")
        print(f"  btc nominal {w['btc_appreciation_nominal_annual']:+.2%}/yr  "
              f"real {w.get('btc_appreciation_real_annual', float('nan')):+.2%}/yr  "
              f"vol {w['btc_vol_annual']:.1%}")
        for k, c in w["correlations"].items():
            print(f"    corr vs {c['label']:<32} {c['corr']:+.2f}  (n={c['n_months']})")


if __name__ == "__main__":
    main()
