-- KPI queries on the SQLite table `energy` (one row per country and year).
-- Each query starts with "-- name: <query_name>".

-- name: renewable_share_latest
-- Renewable share of electricity in the latest year, ranked
SELECT country,
       year,
       ROUND(renewables_share_elec, 1) AS renewables_share_pct,
       ROUND(wind_share_elec, 1)       AS wind_share_pct,
       ROUND(solar_share_elec, 1)      AS solar_share_pct,
       ROUND(carbon_intensity_elec, 0) AS carbon_g_per_kwh
FROM energy
WHERE year = (SELECT MAX(year) FROM energy WHERE renewables_share_elec IS NOT NULL)
  AND country <> 'European Union (27)'
ORDER BY renewables_share_pct DESC;

-- name: change_since_2010
-- Percentage-point change in renewable share between 2010 and the latest year
SELECT a.country,
       ROUND(a.renewables_share_elec, 1)                          AS share_2010_pct,
       ROUND(b.renewables_share_elec, 1)                          AS share_latest_pct,
       ROUND(b.renewables_share_elec - a.renewables_share_elec, 1) AS change_pp
FROM energy a
JOIN energy b ON a.country = b.country
WHERE a.year = 2010
  AND b.year = (SELECT MAX(year) FROM energy WHERE renewables_share_elec IS NOT NULL)
ORDER BY change_pp DESC;

-- name: germany_mix
-- Germany's electricity mix over time (TWh)
SELECT year,
       ROUND(wind_electricity, 1)    AS wind_twh,
       ROUND(solar_electricity, 1)   AS solar_twh,
       ROUND(hydro_electricity, 1)   AS hydro_twh,
       ROUND(coal_electricity, 1)    AS coal_twh,
       ROUND(gas_electricity, 1)     AS gas_twh,
       ROUND(nuclear_electricity, 1) AS nuclear_twh,
       ROUND(renewables_share_elec, 1) AS renewables_share_pct
FROM energy
WHERE country = 'Germany'
ORDER BY year;

-- name: wind_leaders
-- Countries with the highest wind share of electricity in the latest year
SELECT country, ROUND(wind_share_elec, 1) AS wind_share_pct, ROUND(wind_electricity, 1) AS wind_twh
FROM energy
WHERE year = (SELECT MAX(year) FROM energy WHERE wind_share_elec IS NOT NULL)
  AND country <> 'European Union (27)'
ORDER BY wind_share_pct DESC
LIMIT 5;
