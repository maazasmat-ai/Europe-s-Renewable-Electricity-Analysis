"""Europe's renewable electricity transition, 2000 to latest year (Our World in Data).

Run:  python analysis.py
Steps: load + clean -> SQLite + SQL KPIs -> figures -> 2030 trend check for Germany -> Power BI export -> RESULTS.md
"""
import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent          # all files sit in the repository root
DATA = ROOT / "owid_energy_europe_2000_2025.csv"
OUT = FIG = PBI = ROOT
DB = OUT / "energy.db"
GERMANY_TARGET_2030 = 80  # % renewable share of gross electricity consumption (EEG 2023 target)

NAVY, TEAL, ORANGE, GREY = "#1B3A57", "#2A7F8E", "#E07B39", "#9AA3AE"
plt.rcParams.update({"figure.dpi": 120, "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})


# ---------------------------------------------------------------- 1. load & clean
def load() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df = df.drop_duplicates(["country", "year"]).sort_values(["country", "year"])
    # Shares must be between 0 and 100 %; anything else is a data error
    for c in [c for c in df.columns if c.endswith("_share_elec")]:
        df.loc[~df[c].between(0, 100), c] = np.nan
    # Keep only years where the main indicator exists
    return df.dropna(subset=["renewables_share_elec"]).reset_index(drop=True)


# ---------------------------------------------------------------- 2. SQL
def run_sql(df: pd.DataFrame) -> dict:
    OUT.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as con:
        df.to_sql("energy", con, if_exists="replace", index=False)
        text = (ROOT / "queries.sql").read_text(encoding="utf-8")
        parts = re.split(r"^--\s*name:\s*(\w+)\s*$", text, flags=re.MULTILINE)
        return {n: pd.read_sql_query(q, con) for n, q in zip(parts[1::2], parts[2::2])}


# ---------------------------------------------------------------- 3. Germany 2030 trend check
def germany_trend(df: pd.DataFrame, start=2015):
    """Fit a linear trend to Germany's renewable share and extrapolate to 2030."""
    g = df[(df.country == "Germany") & (df.year >= start)]
    slope, intercept = np.polyfit(g.year, g.renewables_share_elec, 1)
    years = np.arange(g.year.max(), 2031)
    forecast = pd.DataFrame({"year": years, "trend_share_pct": slope * years + intercept})
    latest = g.iloc[-1]
    needed = (GERMANY_TARGET_2030 - latest.renewables_share_elec) / (2030 - latest.year)
    return forecast, {"trend_pp_per_year": round(slope, 2),
                      "trend_2030_pct": round(float(forecast.trend_share_pct.iloc[-1]), 1),
                      "needed_pp_per_year": round(needed, 2),
                      "latest_year": int(latest.year),
                      "latest_share_pct": round(latest.renewables_share_elec, 1)}


# ---------------------------------------------------------------- 4. figures
def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True); fig.tight_layout(); fig.savefig(FIG / name); plt.close(fig)


def figures(df, sql, forecast, trend):
    # 1 renewable share over time
    fig, ax = plt.subplots(figsize=(9, 5))
    focus = {"Germany": NAVY, "Denmark": TEAL, "Spain": ORANGE, "European Union (27)": "#C0392B"}
    for c, d in df.groupby("country"):
        if c not in focus:
            ax.plot(d.year, d.renewables_share_elec, color=GREY, lw=0.8, alpha=0.6)
    for c, col in focus.items():
        d = df[df.country == c]
        ax.plot(d.year, d.renewables_share_elec, color=col, lw=2.3, label=c)
    ax.set(ylabel="Renewable share of electricity [%]", title="Renewable share of electricity generation, 2000 to today")
    ax.legend(fontsize=8); save(fig, "01_renewable_share.png")

    # 2 Germany mix (stacked)
    m = sql["germany_mix"].fillna(0)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.stackplot(m.year, m.coal_twh, m.gas_twh, m.nuclear_twh, m.hydro_twh, m.wind_twh, m.solar_twh,
                 labels=["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar"],
                 colors=["#5D6D7E", "#AAB7B8", "#C39BD3", "#5DADE2", TEAL, "#F4D03F"], alpha=0.9)
    ax.set(ylabel="Electricity [TWh]", title="Germany: electricity generation by source (selected sources)")
    ax.legend(loc="upper left", fontsize=8, ncol=3); save(fig, "02_germany_mix.png")

    # 3 change since 2010
    c = sql["change_since_2010"].sort_values("change_pp")
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(c.country, c.change_pp, color=[NAVY if x == "Germany" else TEAL for x in c.country])
    ax.set(xlabel="Change in renewable share since 2010 [percentage points]", title="Who moved fastest since 2010?")
    save(fig, "03_change_since_2010.png")

    # 4 Germany trend vs 2030 target
    g = df[df.country == "Germany"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(g.year, g.renewables_share_elec, color=NAVY, lw=2.3, marker="o", ms=3, label="Germany (actual)")
    ax.plot(forecast.year, forecast.trend_share_pct, color=TEAL, ls="--", lw=2, label="linear trend since 2015")
    ax.axhline(GERMANY_TARGET_2030, color=ORANGE, lw=1.5, label="2030 target (80 %)")
    ax.set(ylabel="Renewable share [%]", xlim=(2000, 2031),
           title=f"Germany: trend reaches {trend['trend_2030_pct']} % by 2030 vs. 80 % target")
    ax.legend(fontsize=8); save(fig, "04_germany_2030_trend.png")


# ---------------------------------------------------------------- 5. outputs
def results_md(sql, trend, df):
    t = trend
    lines = ["# Results", "", f"Data: Our World in Data energy dataset, {df.year.min()}–{df.year.max()}, "
             f"{df.country.nunique()} European countries/regions.", "",
             "## Germany and the 2030 target", "",
             f"- Renewable share in {t['latest_year']}: **{t['latest_share_pct']} %**",
             f"- Trend since 2015: **+{t['trend_pp_per_year']} percentage points per year** → about **{t['trend_2030_pct']} % in 2030**",
             f"- Needed to reach 80 % by 2030: **+{t['needed_pp_per_year']} pp per year**",
             "- Note: the official target refers to gross electricity *consumption*; this analysis uses the share of *generation*, so it is an approximation.",
             "", "## Renewable share, latest year (SQL)", "", sql["renewable_share_latest"].to_markdown(index=False),
             "", "## Change since 2010 (SQL)", "", sql["change_since_2010"].to_markdown(index=False),
             "", "## Wind leaders (SQL)", "", sql["wind_leaders"].to_markdown(index=False)]
    (OUT / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    df = load()
    print(f"Loaded {len(df)} rows, {df.country.nunique()} countries, {df.year.min()}–{df.year.max()}")
    sql = run_sql(df)
    forecast, trend = germany_trend(df)
    figures(df, sql, forecast, trend)
    PBI.mkdir(exist_ok=True)
    df.to_csv(PBI / "energy_europe.csv", index=False)
    sql["germany_mix"].to_csv(PBI / "germany_mix.csv", index=False)
    results_md(sql, trend, df)
    print("Germany:", trend)
    print(sql["renewable_share_latest"].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
