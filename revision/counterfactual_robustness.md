# Counterfactual robustness and uncertainty (Step 08 deliverable)

## What each band covers
- iid residual bootstrap (analysis_ardl.R, 2000 draws): shock uncertainty
  only, conditional on estimated coefficients.
- moving-block bootstrap (block=7, 1000 draws): shock uncertainty allowing
  serial dependence of weekly length.
- re-estimation bootstrap (400 draws: resampled residuals -> rebuilt y ->
  re-estimated lm -> re-projected with iid shocks): coefficient + shock
  uncertainty (fixed regressor design; no model-selection uncertainty).
- Specification uncertainty is NOT in any band; it is shown as the range
  across admissible models (floors/DL/fit windows/samples/Brent paths).

## Backtests (all pre-cap evaluation windows; none crosses 28 Sep)
backtest_origins.csv: 5 origins (31 May..13 Sep) x horizons 14/28d.
Oil ARDL wins 11/16 vs random walk; June-July 14-day origins favour the RW
(drift, little oil news); Aug/Sep origins favour the oil model decisively.

## Specification range (October mean gap, c/l; CPI effect, pp)
| variant | petrol | diesel | CPI |
|---|---|---|---|
| baseline (Jan, q>=7) | -17.4 | -21.1 | -0.383 |
| fit from Jul (v1 window) | -16.3 | -24.3 | ~-0.40 |
| fit to 24 Sep (announcement) | -16.2 | -23.1 | ~-0.39 |
| balanced panel | -17.5 | -21.2 | -0.383 |
| regularity sample | -18.7 | -23.5 | -0.417 |
| Brent +5% / -5% post-cap | -19.6 / -15.1 | -24.2 / -17.9 | -0.43 / -0.32 |
| floors 2/5 (spec_robustness) | -17.3 | -21.9..-22.4 | -0.379..-0.381 |
| DL only | -11.6 | -26.3 | -0.336 |
| AR only (benchmark, inadmissible) | -14.1 | -15.1 | -0.298 |

Reported range in the paper: October gaps petrol ~15-19 c/l, diesel ~21-24
c/l (DL-only diesel shown separately); NIC contribution -0.38 to -0.45 pp
across admissible oil models, -0.30 under the inadmissible AR benchmark.
