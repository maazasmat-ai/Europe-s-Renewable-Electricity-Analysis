# Europe's Renewable Electricity Transition (2000–2025)

Data analysis of how fast European countries are moving to renewable electricity, with a focus on
**Germany's 2030 target of 80 % renewables**.
**Python (pandas) → SQL (SQLite) → trend analysis → charts → Power BI tables.**

![Germany 2030 trend](outputs/figures/04_germany_2030_trend.png)

## Key findings

- Germany's renewable share of electricity generation rose from about 6 % (2000) to **59.1 % (2025)**.
- Since 2015 the share grew by about **3.2 percentage points per year**. At this pace Germany reaches about **74 % in 2030**, below the 80 % target. Reaching it needs about **4.2 pp per year**.
- Coal and nuclear generation fell sharply; wind is now Germany's largest single source in this comparison.
- Denmark leads in wind (about 58 % of electricity from wind in 2025).

Full tables: [`outputs/RESULTS.md`](outputs/RESULTS.md)

| | |
|---|---|
| ![Share](outputs/figures/01_renewable_share.png) | ![Mix](outputs/figures/02_germany_mix.png) |
| ![Change](outputs/figures/03_change_since_2010.png) | ![Trend](outputs/figures/04_germany_2030_trend.png) |

## Method

1. **Load and clean** a European subset (15 countries + EU-27) of the Our World in Data energy dataset: remove duplicates, check that shares lie between 0 and 100 %.
2. **SQL**: store the data in SQLite and calculate KPIs in [`sql/queries.sql`](sql/queries.sql): latest renewable share ranking, change since 2010 (self-join), Germany's mix, wind leaders.
3. **Trend analysis**: linear regression of Germany's renewable share since 2015, extrapolated to 2030 and compared with the target.
4. **Visualisation** with matplotlib; clean tables exported to `powerbi/` for a dashboard.

*Limitation:* the official German target refers to gross electricity consumption; this project uses the share of generation, so the 2030 comparison is an approximation. A linear trend is a simple baseline, not a forecast model.

## How to run

```bash
pip install -r requirements.txt
python src/analysis.py
```

## Data source

Our World in Data, *Energy dataset* (github.com/owid/energy-data), licensed CC BY 4.0. Based on Ember and the Energy Institute Statistical Review of World Energy.

---
Author: Muhammad Maaz Asmat · [LinkedIn](https://linkedin.com/in/maazasmat)
