# Oil model specification (Step 07 deliverable)

Target: log national mean NET-of-tax price (gross/1.22 - statutory excise),
Stradale self-service, effective-day reconstruction. Regressors: own lags
(p) and contemporaneous + lagged log Brent-in-EUR (q). Netting the excise
removes every 2026 tax step from both sides by construction (spring -20 c/l
cut 19 Mar, phased reinstatement 2 May/23 May/7 Jun/4 Jul, diesel discount
28 Jul, steps 18/26 Sep, post-event 6/28 Oct); the counterfactual re-applies
the actual statutory calendar to the projected net path, so both observed
and no-cap gross paths carry identical taxes.

Estimation window: 2026-01-02..2026-09-27 (261 daily obs after lags).
Selection: exhaustive BIC grid p in [0,21], q in [7,21] (revision D6 max
lag 21 on the extended window; oil-lag floor 7 = one week of Brent
dynamics; floors 2/5 and DL/AR extremes in spec_robustness.csv).

Selected: petrol ARDL(2,8), diesel ARDL(1,8).

Validation: placebo 14-27 Sep (petrol 0.447 c/l RMSE vs RW 3.687; diesel
0.852 vs 5.075); expanding-origin backtests 11/16 wins vs random walk with
losses at short horizons from mid-summer drift origins; HAC block-exclusion
of Brent rejected for both fuels.

Known fragility: both selected specs carry near-unit-root persistence
(sum phi 0.987 petrol, 0.995 diesel). The implied long-run elasticity of the
diesel main spec (0.09) is therefore a small-denominator artifact and is
NOT reportable as a structural estimate; the admissible range across floors
is 0.76-0.94 (petrol 0.72-0.77). The paper reports the range and leans on
forecast validation for credibility, per the reviewed design.
