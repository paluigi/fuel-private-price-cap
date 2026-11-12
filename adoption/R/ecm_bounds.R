# ECM / bounds-test treatment for the near-unit-root ARDL (D9 appendix).
#
# The diesel main specification carries sum(phi) = 0.995, so the implied
# long-run elasticity from the levels representation is a
# small-denominator artifact. This script formalises that caveat with the
# Pesaran-Shin-Smith bounds procedure on the SAME data and window:
#   - fit the selected ARDL(p, q) with ARDL::ardl()
#   - bounds F-test and t-test for the null of no level relationship
#     (case 3: unrestricted intercept, no trend), reporting the I(0)/I(1)
#     critical bounds and the p-value interval
#   - UECM representation: speed-of-adjustment coefficient (ECT) and the
#     implied long-run coefficient when a level relationship exists
# Petrol is reported for comparison.
#
# Run from adoption/: Rscript R/ecm_bounds.R
# Outputs: output/ecm_bounds.txt, output/tables/ecm_bounds.csv

Sys.setenv(ARDL_SKIP_MAIN = "1")
.libPaths(c("~/Rlibs", .libPaths()))
source("R/analysis_ardl.R")

OUT_TXT <- "output/ecm_bounds.txt"
OUT_CSV <- "output/tables/ecm_bounds.csv"

main_ecm <- function() {
  sink(OUT_TXT, split = TRUE)
  prices <- fread(FUEL_DAILY, select = c("date", "fuel", "eff_mean_net"))
  prices[, date := as.Date(date)]
  oil <- fread(OIL_FFILL, select = c("date", "brent_eur"))
  oil[, date := as.Date(date)]
  dall <- prices[oil, on = "date"][!is.na(eff_mean_net) & !is.na(brent_eur)]
  dall[, `:=`(y = log(eff_mean_net), x = log(brent_eur))]

  rows <- list()
  for (f in c("Benzina", "Gasolio")) {
    d <- dall[fuel == f & date >= FIT_FROM & date <= ANALYSIS_TO]
    d <- d[order(date)]
    fit <- d[date <= FIT_TO]
    sel <- select_order(fit)
    p <- sel$best_bic$p; q <- sel$best_bic$q
    cat("\n=====", f, ": ARDL(", p, ",", q, ") bounds tests =====\n")
    mod <- ardl(y ~ x, data = as.data.frame(fit), order = c(p, q))
    ft <- bounds_f_test(mod, case = 3, alpha = 0.05)
    tt <- bounds_t_test(mod, case = 3, alpha = 0.05)
    cat("bounds F-test (case 3):\n"); print(ft)
    cat("bounds t-test (case 3):\n"); print(tt)
    ue <- uecm(mod)
    co <- summary(ue)$coefficients
    cat("\nUECM speed-of-adjustment coefficient on L(y, 1):\n")
    print(co[grep("^L\\(y, 1\\)$|^L1\\.y$", rownames(co)), , drop = FALSE])
    # long-run multiplier from the levels model
    lr <- tryCatch(long_run(fit_ardl(fit, p, q)), error = function(e) NA)
    ect <- co[grep("^L\\(y, 1\\)$|^L1\\.y$", rownames(co)), "Estimate"]
    fstat <- ft$statistic
    crit <- ft$parameters  # c(I(0), I(1)) critical bounds at alpha
    cat("\nF statistic:", sprintf("%.2f", fstat),
        "| 5% critical bounds (I0, I1):",
        paste(sprintf("%.2f", crit), collapse = ", "),
        "| p-value:", sprintf("%.3f", ft$p.value), "\n")
    rows[[f]] <- data.table(
      fuel = f, p = p, q = q,
      F_stat = fstat,
      F_crit_I0 = crit[1], F_crit_I1 = crit[2],
      F_pvalue = ft$p.value,
      t_stat = tt$statistic,
      t_crit_I0 = tt$parameters[1], t_crit_I1 = tt$parameters[2],
      ect_coef = ect,
      half_life_days = if (!is.na(ect) && ect < 0)
        round(log(0.5) / log(1 + ect), 1) else NA_real_,
      lr_levels = lr
    )
  }
  out <- rbindlist(rows)
  fwrite(out, OUT_CSV)
  cat("\nsummary:\n"); print(out[])
  cat("\nDone.\n")
  sink()
}

main_ecm()
