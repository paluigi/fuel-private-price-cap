# Specification robustness for the ARDL counterfactual.
#
# Variants (per fuel), each selecting (p, q) by AIC and BIC on its grid,
# refitting the placebo backtest, and re-running the full no-cap projection:
#   V1 baseline : p in [0,10], q in [0,10]            (= analysis_ardl.R; q
#                 counts oil lags beyond the contemporaneous term)
#   V2 max15    : p in [0,15], q in [0,15]
#   V3 minq2    : p in [0,10], q in [2,10]            (>= 2 oil lags)
#   V4 dl_only  : p = 0, q in [0,15]                  (no autoregressive term)
#   V5 ar_only  : pure AR(p), NO oil term at all - economically untenable
#                 reference (petrol cannot depend only on its own past);
#                 shown to make that point, never used as counterfactual.
#
# Also reports HAC block-exclusion Wald tests on the baseline AIC spec:
# oil block (all theta_j = 0) and autoregressive block (all phi_i = 0).
#
# Reuses the machinery of analysis_ardl.R (sourced with ARDL_SKIP_MAIN=1).
# Run from anywhere:  Rscript adoption/R/spec_robustness.R
#
# Outputs: output/spec_robustness.txt, output/tables/spec_robustness.csv,
#          output/tables/spec_block_tests.csv

Sys.setenv(ARDL_SKIP_MAIN = "1")

# work from adoption/ regardless of the caller's directory
this_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
if (length(this_file) == 1) {
  setwd(normalizePath(file.path(dirname(normalizePath(this_file)), "..")))
}

source("R/analysis_ardl.R")  # libs, constants, fit_ardl, project_ardl, ...

OUT_TXT <- "output/spec_robustness.txt"
OUT_CSV <- "output/tables/spec_robustness.csv"
N_SIM_ROB <- 400L  # bands not needed here; keep the bootstrap light

VARIANTS <- list(
  list(key = "V1_baseline", label = "Baseline (max 10)", ps = 0:10, qs = 0:10),
  list(key = "V2_max15",    label = "Max 15 lags",       ps = 0:15, qs = 0:15),
  list(key = "V3_minq2",    label = "Min 2 oil lags",    ps = 0:10, qs = 2:10),
  list(key = "V4_dl_only",  label = "Distributed lag only (no AR)", ps = 0, qs = 0:15)
)

select_grid <- function(d, ps, qs) {
  rows <- rbindlist(lapply(ps, function(p) {
    rbindlist(lapply(qs, function(q) {
      if (p == 0 && q == 0) return(NULL)
      obj <- fit_ardl(d, p, q)
      data.table(p = p, q = q,
                 AIC = AIC(obj$fit), BIC = BIC(obj$fit),
                 n = nrow(obj$lag))
    }))
  }))
  list(best_aic = rows[which.min(AIC)], best_bic = rows[which.min(BIC)])
}

# ---- pure AR(p), no oil term (reference only) ----------------------------- #

fit_ar_only <- function(d, p) {
  lag <- copy(d)
  for (i in seq_len(p)) lag[[paste0("yl", i)]] <- shift(lag$y, i)
  cols <- c("y", paste0("yl", seq_len(p)))
  lag <- lag[stats::complete.cases(lag[, ..cols])]
  f <- as.formula(paste("y ~", paste(cols[-1], collapse = " + ")))
  list(fit = lm(f, data = lag), lag = lag, p = p)
}

project_ar_only <- function(obj, hist_y, n_ahead) {
  cc <- coef(obj$fit)
  a <- cc[["(Intercept)"]]
  phi <- cc[paste0("yl", seq_len(obj$p))]
  idx0 <- length(hist_y)
  point <- hist_y
  for (h in seq_len(n_ahead)) {
    t <- idx0 + h
    val <- a
    for (i in seq_len(obj$p)) val <- val + phi[i] * point[t - i]
    point <- c(point, val)
  }
  point[(idx0 + 1):(idx0 + n_ahead)]
}

run_ar_only <- function(d, fuel_name) {
  fit <- d[date <= FIT_TO]
  grid <- rbindlist(lapply(1:10, function(p) {
    o <- fit_ar_only(fit, p)
    data.table(p = p, AIC = AIC(o$fit), BIC = BIC(o$fit), n = nrow(o$lag))
  }))
  p_a <- grid[which.min(AIC)]$p; p_b <- grid[which.min(BIC)]$p
  obj <- fit_ar_only(fit, p_a)

  fit_bt <- d[date <= BT_FIT_TO]
  grid_bt <- rbindlist(lapply(1:10, function(pp) {
    o <- fit_ar_only(fit_bt, pp)
    data.table(p = pp, AIC = AIC(o$fit))
  }))
  obj_bt <- fit_ar_only(fit_bt, grid_bt[which.min(AIC)]$p)
  bt_win <- d[date >= BT_FROM & date <= FIT_TO]
  pr <- exp(project_ar_only(obj_bt, fit_bt$y, nrow(bt_win)))
  rw_path <- rep(fit_bt$y[length(fit_bt$y)], nrow(bt_win))
  err <- (exp(bt_win$y) - pr) * 100
  err_rw <- (exp(bt_win$y) - exp(rw_path)) * 100

  proj_win <- d[date >= PROJ_FROM]
  cf_net <- exp(project_ar_only(obj, fit$y, nrow(proj_win)))
  excise <- proj_win$eff_mean_gross / VAT - proj_win$eff_mean_net
  cf_gross <- (cf_net + excise) * VAT
  gap <- (proj_win$eff_mean_gross - cf_gross) * 100

  base <- d[date %in% REF_DAYS, .(date, actual = eff_mean_gross)]
  cf_rd <- data.table(date = proj_win$date, cf = cf_gross)[date %in% REF_DAYS]
  m <- cf_rd[base, on = .(date)]  # all six reference days; cf NA pre-cap
  sep_a <- mean(m[substr(format(date), 1, 7) == "2026-09"]$actual)
  oct_a <- mean(m[substr(format(date), 1, 7) == "2026-10"]$actual)
  oct_c <- mean(m[substr(format(date), 1, 7) == "2026-10"]$cf)
  mom_a <- (oct_a / sep_a - 1) * 100
  mom_c <- (oct_c / sep_a - 1) * 100
  w_f <- W_CARBURANTI / 2

  cat(sprintf("%-10s %-9s AIC (%d,.) BIC (%d,.) | NO OIL TERM | N %d | R2 %.4f\n",
              "V5_ar_only", fuel_name, p_a, p_b,
              nrow(obj$lag), summary(obj$fit)$r.squared))
  cat(sprintf("           backtest RMSE %.2f (RW %.2f, bias %+.2f) | mean gap %.1f c/l, end gap %.1f c/l | MoM cf %+.2f%% | CPI effect %+.3f pp\n",
              rmse(err), rmse(err_rw), mean(err), mean(gap), gap[length(gap)],
              mom_c, w_f * (mom_a - mom_c)))

  data.table(
    fuel = fuel_name, variant = "V5_ar_only",
    label = "Autoregression only (no oil)",
    p = p_a, q = NA_integer_, order_bic = sprintf("(%d,.)", p_b),
    lr_elasticity = NA_real_, lr_elasticity_bic = NA_real_,
    backtest_rmse_cpl = rmse(err), backtest_rmse_rw_cpl = rmse(err_rw),
    backtest_bias_cpl = mean(err),
    mean_gap_cpl = mean(gap), end_gap_cpl = gap[length(gap)],
    mom_actual_pct = mom_a, mom_cf_pct = mom_c,
    cpi_effect_pp = w_f * (mom_a - mom_c),
    n_fit = nrow(obj$lag), r2 = summary(obj$fit)$r.squared
  )
}

# ---- ARDL variants --------------------------------------------------------- #

run_variant <- function(d, fuel_name, var) {
  fit <- d[date <= FIT_TO]
  sel <- select_grid(fit, var$ps, var$qs)
  obj <- fit_ardl(fit, sel$best_aic$p, sel$best_aic$q)
  obj_bic <- fit_ardl(fit, sel$best_bic$p, sel$best_bic$q)

  # placebo backtest with the same grid
  fit_bt <- d[date <= BT_FIT_TO]
  sel_bt <- select_grid(fit_bt, var$ps, var$qs)
  obj_bt <- fit_ardl(fit_bt, sel_bt$best_aic$p, sel_bt$best_aic$q)
  bt_win <- d[date >= BT_FROM & date <= FIT_TO]
  proj_bt <- project_ardl(obj_bt, fit_bt$y, d$x, nrow(bt_win), n_sim = N_SIM_ROB)
  rw_path <- rep(fit_bt$y[length(fit_bt$y)], nrow(bt_win))
  err <- (exp(bt_win$y) - exp(proj_bt$point)) * 100
  err_rw <- (exp(bt_win$y) - exp(rw_path)) * 100

  # no-cap projection and reference-day counterfactual
  proj_win <- d[date >= PROJ_FROM]
  proj <- project_ardl(obj, fit$y, d$x, nrow(proj_win), n_sim = N_SIM_ROB)
  excise <- proj_win$eff_mean_gross / VAT - proj_win$eff_mean_net
  cf_gross <- (exp(proj$point) + excise) * VAT
  gap <- (proj_win$eff_mean_gross - cf_gross) * 100

  base <- d[date %in% REF_DAYS, .(date, actual = eff_mean_gross)]
  cf_rd <- data.table(date = proj_win$date, cf = cf_gross)[date %in% REF_DAYS]
  m <- cf_rd[base, on = .(date)]  # all six reference days; cf NA pre-cap
  sep_a <- mean(m[substr(format(date), 1, 7) == "2026-09"]$actual)
  oct_a <- mean(m[substr(format(date), 1, 7) == "2026-10"]$actual)
  oct_c <- mean(m[substr(format(date), 1, 7) == "2026-10"]$cf)
  mom_a <- (oct_a / sep_a - 1) * 100
  mom_c <- (oct_c / sep_a - 1) * 100
  w_f <- W_CARBURANTI / 2

  cat(sprintf("%-10s %-9s AIC (%d,%d) BIC (%d,%d) | lr_elas %.3f/%.3f | N %d | R2 %.4f\n",
              var$key, fuel_name,
              sel$best_aic$p, sel$best_aic$q, sel$best_bic$p, sel$best_bic$q,
              long_run(obj), long_run(obj_bic),
              nrow(obj$lag), summary(obj$fit)$r.squared))
  cat(sprintf("           backtest RMSE %.2f (RW %.2f, bias %+.2f) | mean gap %.1f c/l, end gap %.1f c/l | MoM cf %+.2f%% (actual %+.2f%%) | CPI effect %+.3f pp\n",
              rmse(err), rmse(err_rw), mean(err), mean(gap), gap[length(gap)],
              mom_c, mom_a, w_f * (mom_a - mom_c)))

  data.table(
    fuel = fuel_name, variant = var$key, label = var$label,
    p = sel$best_aic$p, q = sel$best_aic$q,
    order_bic = sprintf("(%d,%d)", sel$best_bic$p, sel$best_bic$q),
    lr_elasticity = long_run(obj),
    lr_elasticity_bic = long_run(obj_bic),
    backtest_rmse_cpl = rmse(err), backtest_rmse_rw_cpl = rmse(err_rw),
    backtest_bias_cpl = mean(err),
    mean_gap_cpl = mean(gap), end_gap_cpl = gap[length(gap)],
    mom_actual_pct = mom_a, mom_cf_pct = mom_c,
    cpi_effect_pp = w_f * (mom_a - mom_c),
    n_fit = nrow(obj$lag), r2 = summary(obj$fit)$r.squared
  )
}

block_tests <- function(d, fuel_name) {
  # HAC block-exclusion Wald tests on the baseline AIC spec. Restricted
  # models are refit on the FULL model's lagged frame so all models use
  # the same estimation sample.
  fit <- d[date <= FIT_TO]
  sel <- select_grid(fit, 0:10, 0:10)
  p <- sel$best_aic$p; q <- sel$best_aic$q
  lagdf <- fit_ardl(fit, p, q)$lag
  yl <- paste0("yl", seq_len(p))
  xl <- paste0("xl", 0:q)
  f_all <- paste(c(yl, xl), collapse = " + ")
  full <- lm(as.formula(paste("y ~", f_all)), data = lagdf)
  vc <- NeweyWest(full, lag = 7, prewhite = FALSE)
  tx <- waldtest(full,
                 as.formula(paste("y ~", paste(yl, collapse = " + "))),
                 vcov = vc)
  if (p > 0) {
    ta <- waldtest(full,
                   as.formula(paste("y ~", paste(xl, collapse = " + "))),
                   vcov = vc)
  } else {
    ta <- list(F = c(NA, NA), `Pr(>F)` = c(NA, NA))
  }
  cat(sprintf("\n%s baseline (%d,%d) HAC block Wald tests:\n", fuel_name, p, q))
  cat(sprintf("  oil block excluded:      F = %.2f, p = %.3g\n", tx$F[2], tx$`Pr(>F)`[2]))
  cat(sprintf("  autoregressive block:    F = %.2f, p = %.3g\n", ta$F[2], ta$`Pr(>F)`[2]))
  data.table(fuel = fuel_name,
             oil_block_F = tx$F[2], oil_block_p = tx$`Pr(>F)`[2],
             ar_block_F = ta$F[2], ar_block_p = ta$`Pr(>F)`[2])
}

main_rob <- function() {
  sink(OUT_TXT, split = TRUE)
  prices <- fread(FUEL_DAILY,
                  select = c("date", "fuel", "eff_mean_gross", "eff_mean_net"))
  prices[, date := as.Date(date)]
  oil <- fread(OIL_FFILL, select = c("date", "brent_eur"))
  oil[, date := as.Date(date)]
  dall <- prices[oil, on = "date"][!is.na(eff_mean_net) & !is.na(brent_eur)]

  res <- rbindlist(lapply(c("Benzina", "Gasolio"), function(f) {
    d <- dall[fuel == f & date >= FIT_FROM & date <= ANALYSIS_TO]
    d <- d[order(date), .(date, eff_mean_gross, eff_mean_net,
                          y = log(eff_mean_net), x = log(brent_eur))]
    rbindlist(lapply(VARIANTS, function(v) run_variant(d, f, v)))
  }))
  res <- rbind(res, rbindlist(lapply(c("Benzina", "Gasolio"), function(f) {
    d <- dall[fuel == f & date >= FIT_FROM & date <= ANALYSIS_TO]
    d <- d[order(date), .(date, eff_mean_gross, eff_mean_net,
                          y = log(eff_mean_net), x = log(brent_eur))]
    run_ar_only(d, f)
  })))
  fwrite(res, OUT_CSV)

  bt <- rbindlist(lapply(c("Benzina", "Gasolio"), function(f) {
    d <- dall[fuel == f & date >= FIT_FROM & date <= ANALYSIS_TO]
    d <- d[order(date), .(date, eff_mean_gross, eff_mean_net,
                          y = log(eff_mean_net), x = log(brent_eur))]
    block_tests(d, f)
  }))
  fwrite(bt, "output/tables/spec_block_tests.csv")
  cat("\nDone.\n")
  sink()
}

main_rob()
