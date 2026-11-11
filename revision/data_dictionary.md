# Data dictionary — variable names and translations (Step 03)

The rewritten paper keeps raw identifiers out of the narrative; this table is
the single mapping between prose terms, code names and definitions.

## Price panel (station × fuel × day)

| Code name | Paper term | Definition |
|---|---|---|
| `id_impianto` | station | MIMIT plant identifier |
| `fuel` (`Benzina`/`Gasolio`) | petrol / diesel | self-service (`isSelf=1`) prices only |
| `prezzo` | pump (gross) price | EUR/l, three decimals, VAT included |
| `dt_comu` / `dtComu` | communication timestamp | when the operator last set the price (`%d/%m/%Y %H:%M:%S`) |
| `date` | extract date | publication day of the MIMIT file (refers to 08:00 of the previous day) |
| effective price | price in force on day D | last communication with communication date ≤ D |
| `net_price` | net-of-tax pump price | `prezzo / 1.22 − excise(fuel, day)`; strips VAT and excise — **not** a retail margin |
| `cap_threshold` | operational ceiling | petrol 2.000; diesel 2.200 → 2.261 (6 Oct) → 2.212 (28 Oct) |
| `compliance_at_cap` / `at_cap` | priced below the ceiling | `prezzo < cap_threshold` (strict, D3), defined from 28 Sep |
| naive mean | snapshot mean | mean of the raw extract rows (what an 8am-cut collector records) |

## Station covariates (from anagrafica + ISTAT grid)

| Code name | Paper term | Definition |
|---|---|---|
| `nn_dist_km` | distance to the nearest competitor | km to the nearest other priced station (same fuel, same day), EPSG:3035 |
| `cap_dist_km` | distance to the nearest station below the ceiling | same-day distance to the closest station priced below the (date-aware) ceiling; `cap_dist_km_d0` = value on 28 Sep |
| `pre_gap_vs_cap` | pre-cap price gap | mean price over 21–27 Sep minus the nominal ceiling (2.000/2.200) |
| `pop_density_cell` (pop_cell) | local population density | ISTAT 2021 1-km grid cell population at the station's location |
| `n_stations_gestore` | chain size | number of stations under the same operator (gestore) |
| `bandiera` | brand | MIMIT brand flag ("Agip Eni" = the cap initiator); "Pompe Bianche" = unbranded independents |
| `tipo_impianto` | station type | Stradale (roadside) vs Autostradale (motorway); analysis uses Stradale only |

## Aggregate series and model objects

| Code/output | Paper term | Definition |
|---|---|---|
| `fuel_daily_prices.csv` (`eff_mean_gross/net`) | national daily price | equal-weighted mean over Stradale station-fuel observations (effective prices) |
| `bal_*` | balanced-panel variant | stations present ≥95% of days (composition robustness) |
| `oil_fx_daily_ffill.csv` (`brent_eur`) | Brent in euro | FRED Brent USD/bbl ÷ USD/EUR, forward-filled to calendar days |
| ARDL(p, q) | oil pass-through model | log net price on own lags (p) and Brent lags (q), pre-cap window, BIC-selected, q ≥ 7 |
| `counterfactual_daily.csv` (`cf_gross`) | conditional no-cap price | recursive ARDL forecast re-taxified with the statutory calendar |
| `gap_cpl` | estimated price gap | actual minus counterfactual, cents per litre |
| `inflation_days.csv` | reference-day prices | 1/11/21 Sep vs Oct effective means |
| `cpi_effect_pp` | estimated NIC contribution | 4.5219% (ECOICOP 07.2.x weight, xlsx-verified) × fuel-weighted actual-vs-no-cap October change |
