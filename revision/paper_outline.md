# Paper outline (Step 12) — paragraph-level

Target: *Energy Economics*-style article, 8 sections, 4 main figures, 4 main
tables, ordered technical appendix. Title (kept, order adjusted):
*"Counterfactual Prices, Inflation, and Adoption: A Voluntary Price Cap in
the Italian Retail Fuel Market"* — final call at Step 13 (Gate 3 input).

## 1. Introduction (~8 paragraphs, 750-950 words)
1. Hook: Sept-Oct 2026 oil surge (Brent €53→€108) meets a voluntary cap by
   Italy's largest network. 2. The policy: 25 Sep announcement, 28 Sep
   implementation, 1.99/2.19 nominal, excise-linked framing, 30 days
   extended through 31 Oct. 3. The question (one sentence, memo E1-E3).
   4. Why it is answerable here: complete station panel + communication
   timestamps. 5. Approach: observed path / conditional no-cap ARDL /
   reference-day accounting — in narrative, no model list. 6. Headline
   results (numbers from claim hierarchy): gaps 17.4/21.1 c/l; NIC −0.38 pp
   (range); adoption ~84%/83% ever, median day 4. 7. Mechanism in one
   paragraph: leader cut most, rivals followed, bunching one decimal below
   the ceiling; 28-Oct incomplete pass-through. 8. Contribution vs 4
   literatures (pass-through; price leadership/vertical constraints; retail
   price adjustment frictions; price-index measurement) + roadmap sentence.

## 2. Institutional setting (~4 paragraphs)
1. Italian fuel retail structure (brands, white pumps, MIMIT price
   publication). 2. The 2026 excise roller-coaster (spring −20 c/l cut,
   phased reinstatement, pre-cap diesel steps) + VAT 22% — sets up why
   net-of-tax modelling is needed. 3. The cap: announcement vs
   implementation; operational gross cutoffs 2.00/2.20 and their mechanical
   tax translations 2.261 (6 Oct), 2.212 (28 Oct); strict inequality;
   duration framing (30 days; hard level through 31 Oct). 4. ISTAT NIC
   collection: MIMIT source, 1/11/21 reference days, station selection
   (author premises flagged).

## 3. Data and measurement (~5 paragraphs + Table 1)
1. Sources: MIMIT daily archives Jan-Oct (12.4M rows), weekly anagrafica,
   excise calendar, FRED Brent/FX. 2. Communication-time reconstruction:
   8am snapshot problem, effective-day definition, worked example
   (cap-week table inline or footnote), Oct-1 4.2/4.9 c/l correction.
   3. National series construction: Stradale self-service means, net-of-tax
   (formula in words + one display equation), tax steps stripped.
   4. Compliance definitions: strict ceiling, 3-step diesel path, boundary
   masses negligible (one sentence + appendix table). 5. Sample summary
   (Table 1: windows, units, reference days, thresholds).

## 4. Observed market response (~4 paragraphs + Figure 1 + Figure 4a)
1. National price paths: petrol 2.16→2.04, diesel flat 2.24→2.24 (masking
   the +6.1 c tax step) — oil doubled under the cap. 2. Adoption: shares by
   day (21% day 0, 51% by day 4, ~84% ever; final-day 81.8/50.2 with the
   2.212 ceiling — denominators explicit). 3. Brand groups: Eni/Q8/Api-Ip
   near-universal, Tamoil/Esso rapid, white pumps partial; group
   decomposition of the mean move (Eni 27% of diesel move at 19% share).
   4. The 6 Oct episode: jump decomposition (43/48 pp behavioural);
   anticipation check 25-27 Sep (nothing: flat leads).

## 5. The no-cap counterfactual (~6 paragraphs + Figure 2, Figure 3, Table 2)
1. Strategy: pre-cap oil pass-through estimated on Jan-Sep (261 obs),
   actual Brent path, actual taxes reapplied. Maintained assumption stated.
   2. Model selection: BIC grid to 21 lags, oil floor (one week dynamics);
   selected (2,8)/(1,8). 3. Why credible: backtests (placebo 0.45/0.85 vs
   RW 3.69/5.07; expanding origins 11/16 with honest losses), HAC block
   tests, near-unit-root caveat and elasticity RANGE (0.72-0.77 petrol;
   0.81-0.94 diesel across floors; main-spec diesel LR not interpretable).
   4. Projection results: Figure 3; mean gaps 17.4/21.1, endpoint 22.2/20.4,
   reference-day gaps. 5. Uncertainty: three bootstraps (what each covers),
   endpoint bands ≈ ±7-9 c/l; specification range table (fit windows,
   samples, Brent ±5%). 6. AR-only benchmark reported fairly (loses on the
   extended window) but inadmissible as a no-oil economy.

## 6. Inflation implications (~4 paragraphs + Table 3)
1. Reference-day method, equal station weights, 50/50 split, 4.5219% weight
   (xlsx-verified; lubricants residual). 2. Results: MoM actual vs no-cap;
   **−0.38 pp** (petrol −0.17, diesel −0.21). 3. Sensitivities: splits
   (±0.004), regularity sample −0.42, model range −0.38..−0.45; scenario
   range dominated by the no-cap path, not the split. 4. Measurement note:
   snapshot bias correction is about OUR estimator; no ISTAT accusation;
   preliminary-vs-final premise flagged.

## 7. How the response propagated (~4 paragraphs + Figure 4b + Table 4)
1. Diffusion descriptives: adoption hazard by day, brand order, distances.
   2. Cox/LPM associations (compact Table 4, units per 10 c/l and km;
   PH violated → time-interacted reading; association language).
   3. Bunching and dispersion: 17.9% at exactly 1.999; diesel 2.259 mass
   post-6 Oct; p90−p10 +70%; adopters 11-12 c/l below non-adopters.
   4. The 28-Oct natural check: ceiling 2.212; pass-through ~40% in 3 days;
   zero mass at 2.211 — the ceiling stops focal pricing when the
   commitment weakens.

## 8. Conclusion (~3 paragraphs)
Size and conditions of the effect; what micro evidence adds; limits
(conditional counterfactual, window, no welfare claims) — no number dump.

## Exhibits
- F1 national gross prices with 25/28 Sep, 6/28 Oct markers + stepped
  diesel ceiling. F2 Brent EUR + net prices (indexed + level). F3 actual vs
  no-cap with re-estimation band + reference-day dots. F4 two-panel
  mechanism: (a) adoption share by brand group; (b) 28-Oct diesel zoom.
- T1 sample/data definitions. T2 ARDL + backtests (placebo + origins).
  T3 inflation results + sensitivities. T4 compact micro associations.
- Appendix: full Cox/LPM; event-study WITH leads; spec grid + block tests +
  bootstrap band table; boundary counts; price endings; maps (consolidated);
  data dictionary; chronology table.
