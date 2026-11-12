# Estimands (Step 06)

| id | object | definition | units | source series |
|---|---|---|---|---|
| E1a | observed national price path | eff mean gross & net, per fuel, Jan-Oct | EUR/l, c/l | fuel_daily_prices.csv |
| E1b | observed adoption | share of station-fuel units priced < ceiling, by day; ever/final-day; brand groups | % | adoption_panel |
| E2a | conditional no-cap path | recursive ARDL(BIC, q>=7) forecast of log net price on actual Brent, re-taxified with statutory excise | EUR/l | counterfactual_daily.csv |
| E2b | price gap | actual - no-cap, post-cap window & reference days | c/l | counterfactual_daily.csv |
| E2c | forecast uncertainty | re-estimation + moving-block bootstrap bands; specification range across admissible models | c/l | uncertainty_ardl.R (new) |
| E3a | reference-day inflation | MoM % change at 1/11/21 Sep vs Oct, actual & no-cap, per fuel | % | inflation_days.csv |
| E3b | NIC contribution | 4.5219% x [50/50 weighted no-cap minus actual Oct change]; sensitivities 45/55, 55/45; regularity-filtered vs universe | pp | inflation_summary.csv |
| M1 | mechanism: bunching | exact-decimal masses at ceiling-0.001 | % of obs | definitions_daily_series.csv |
| M2 | mechanism: 28-Oct pass-through | diesel mean gross change 28->31 Oct vs -4.88 c/l mechanical | c/l, % | definitions_daily_series.csv |
| M3 | mechanism: adoption gradient | Cox/LPM associations (per-10-c/l gap, per-km distance), time-varying | hazard/points | revision_samples.R |

Not estimands (explicitly disclaimed): firm-level causal effects, retail
margins, motorist welfare, ISTAT's proprietary index replication.
