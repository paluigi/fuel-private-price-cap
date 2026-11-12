# Discrete-time hazard model for ceiling adoption (author next step).
#
# The Cox proportional-hazards model is rejected by cox.zph, so the paper
# reads its coefficients as time-averaged associations. A discrete-time
# logit hazard with day fixed effects is non-parametric in duration and
# gives directly interpretable log-odds: one row per unit-day at risk,
# event = first day below the ceiling. Day fixed effects absorb the
# baseline hazard; brand and region fixed effects as in the LPM; gestore-
# clustered standard errors. Three samples mirror revision_samples.R:
# universe / excluding the two leader brands / white pumps only.
#
# Run from adoption/: Rscript R/analysis_hazard_discrete.R
# Outputs: output/hazard_discrete.txt, output/tables/hazard_discrete.csv,
#          output/tables/hazard_baseline.csv (day-specific average hazard)

.libPaths(c("~/Rlibs", .libPaths()))
suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

OUT_TXT <- "output/hazard_discrete.txt"
COEF_CSV <- "output/tables/hazard_discrete.csv"
BASE_CSV <- "output/tables/hazard_baseline.csv"

SAMPLES <- list(
  S1_universe = function(d) d,
  S2_excl_leaders = function(d) d[!bandiera %in% c("Agip Eni", "Q8")],
  S3_white_pumps = function(d) d[bandiera == "Pompe Bianche"]
)

main_hazard <- function() {
  sink(OUT_TXT, split = TRUE)
  d <- fread("output/tables/adoption_person_period.csv")
  d[, day := as.integer(day)]
  d[, fuel := factor(fuel)]
  cat("person-period rows:", nrow(d), " events:", sum(d$event),
      " units:", uniqueN(paste(d$id_impianto, d$fuel)), "\n\n")

  rows <- list()
  baselines <- list()
  for (nm in names(SAMPLES)) {
    dd <- SAMPLES[[nm]](d)
    cat("=====", nm, ": ", nrow(dd), "rows,", sum(dd$event), "events =====\n")
    # day FE absorb the baseline hazard; brand FE only where >=3 levels
    n_brands <- uniqueN(dd$bandiera)
    fml_cov <- "event ~ pre_gap_10c + nn_dist_km + cap_dist_km_d0 + pop_1000 + chain_10 + fuel"
    m <- if (n_brands >= 3) {
      feglm(as.formula(paste(fml_cov, "| day + bandiera + regione")),
            data = dd, family = binomial("logit"), cluster = ~gestore)
    } else {
      feglm(as.formula(paste(fml_cov, "| day + regione")),
            data = dd, family = binomial("logit"), cluster = ~gestore)
    }
    print(summary(m))  # cluster = ~gestore set at estimation
    # baseline hazard: empirical share of at-risk units adopting each day
    # (with day FEs, this is the saturated day-only baseline the model fits)
    bl <- dd[, .(hazard = mean(event), n_at_risk = .N, events = sum(event)),
             by = day]
    baselines[[nm]] <- data.table(sample = nm, bl)
    co <- coeftable(m)
    for (v in rownames(co)) {
      rows[[paste(nm, v)]] <- data.table(
        sample = nm, variable = v, coef = co[v, 1], se = co[v, 2],
        p = co[v, 4]
      )
    }
    cat("\n")
  }
  out <- rbindlist(rows)
  fwrite(out, COEF_CSV)
  fwrite(rbindlist(baselines), BASE_CSV)
  cat("baseline hazard (universe, first 10 days):\n")
  print(baselines$S1_universe[1:10])
  cat("\nDone.\n")
  sink()
}

main_hazard()
