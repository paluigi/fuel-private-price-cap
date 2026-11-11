# Final quality check — Step 16

Date: 11 November 2026. Paper: `adoption/paper.pdf` (18 pp).

## Build

- pdflatex + biber, three passes: 0 errors, 0 undefined references,
  0 undefined citations, no overfull boxes on figure/table pages.
- Clean-room source list: paper.tex + 5 generated table files
  (paper_v2_tables, paper_v2_appendix, paper_tables, paper_tables_s6,
  paper_appendix_lpm) + 6 figure files, every one regenerated from code.

## Numeric consistency (revision/check_numbers.py)

53 automated checks, all passing: gaps (17.4/21.1/22.2/20.4), backtests
(0.45/0.85 vs RW 3.69/5.07), orders (2,8)/(1,8), 261 obs, MoM actual/no-cap,
CPI -0.38 with all three sensitivities, all six reference-day gaps,
adoption shares (day-0, final-day, ever), bunching 17.9%, dispersion
(8.1->14.0 / 9.5->15.9, adopter gaps 11.5/11.7), 28-Oct episode numbers,
policy dates and thresholds, NIC weight.

## Dates and framing verified

25/28 September, 6/28 October, no post-event petrol step, three diesel
ceiling levels with strict inequality, "16--17 October" gap disclosed,
"thirty days" duration framing, no rival-invitation claim.

## Visual gate

18 pages rendered at 90 dpi and inspected. 16 PASS; 2 initial FAILs
(legend/title collisions in Figures 3 and 4) fixed by moving the legends
below the panels; re-inspection PASS. No unresolved references, no missing
glyphs, tables and maps render cleanly.

## Honest-limitations read (final economic review)

- The counterfactual is model-conditional; assumption stated in
  introduction, methods and conclusion; uncertainty layered (three
  bootstrap schemes + specification range) with coverage of each stated.
- Near-unit-root persistence disclosed; diesel main-spec long-run
  elasticity explicitly not interpreted as structural.
- Aggregation assumptions labelled as approximations; premises
  (regularity-based selection, preliminary-release completeness)
  attributed to author institutional knowledge, not to public sources.
- Micro gradients labelled conditional associations; PH rejection noted
  with time-averaged reading.
- No welfare, margin or causal-chain claims anywhere in the text.

## Remaining items deliberately NOT done (with reasons)

- November 2026 data: outside the fixed analysis window; post-window
  commitments unclear (author D5).
- Discrete-time hazard re-estimation of the Cox model: PH violation is
  disclosed and coefficients are read as time-averaged associations;
  a full discrete-time model is a candidate referee response, not a
  precondition (reviewer's own proportionality principle).
- Refined-product price indicator: not available without proprietary data
  (pack Step 08 allows skipping).
