# ARDL counterfactual for net fuel prices on Brent (EUR).
#
# Per fuel: log-log ARDL ln(net price) ~ lags(ln net) + lags(ln Brent EUR/bbl),
# estimated on the pre-cap window 2026-07-01..2026-09-27. The target is the
# net-of-tax price (prezzo/1.22 - excise, reconstructed from published pump
# prices), so the tax calendar is stripped by construction and NO excise
# dummy enters the regression: statutory tax changes have no place in a
# net-price equation, and any staggered pass-through around them stays in
# the error. Lag order (p,q) selected over 0..MAX_ORDER by AIC and BIC on an
# explicit-lag lm grid (cross-checked against ARDL::auto_ardl), then
# estimated with lm so the recursive projection is fully transparent.
# Diagnostics: Breusch-Godfrey, RESET, long-run pass-through elasticity =
# sum(theta)/(1 - sum(phi)).
#
# Counterfactual: recursive no-cap projection 2026-09-28..2026-10-31 given the
# actual Brent path and the model's own projected lags (actual post-cap net
# prices are never fed back). ~95% bands from an iid-residual bootstrap.
# Counterfactual pump price = (net_cf + excise(day)) * 1.22 with the actual
# excise calendar, backed out per day as excise = gross_eff/1.22 - net_eff, so
# tax steps (07-04, 07-28, 09-18, 09-26, 10-06, 10-28) hit both series equally.
#
# Placebo backtest: fit 07-01..09-13, project 09-14..27 (still pre-cap),
# compare with actuals and a random-walk benchmark.
#
# ISTAT reference days (1st/11th/21st): actual vs counterfactual Sep->Oct MoM
# changes and the implied contribution to headline CPI using the NIC 2026
# definitive weight of ECOICOP 07.2.2 'Carburanti e lubrificanti' (45,219 per
# 10,000 = 4.5219%; data/external/istat_ponderazioni_2026.xlsx).
#
# Inputs:  output/tables/fuel_daily_prices.csv (build_fuel_daily.py)
#          output/tables/oil_fx_daily_ffill.csv (build_oil_series.py)
# Outputs: output/ardl_results.txt
#          output/tables/counterfactual_daily.csv
#          output/tables/backtest_daily.csv
#          output/tables/inflation_days.csv
#          output/tables/inflation_summary.csv

.libPaths(c("~/Rlibs", .libPaths()))
suppressPackageStartupMessages({
  library(data.table)
  library(lmtest)
  library(sandwich)
  library(ARDL)
})

FUEL_DAILY <- "output/tables/fuel_daily_prices.csv"
OIL_FFILL <- "output/tables/oil_fx_daily_ffill.csv"
RESULTS <- "output/ardl_results.txt"
CF_CSV <- "output/tables/counterfactual_daily.csv"
BACKTEST_CSV <- "output/tables/backtest_daily.csv"
ARDL_SUMMARY_CSV <- "output/tables/ardl_summary.csv"
INFL_DAYS_CSV <- "output/tables/inflation_days.csv"
INFL_SUMMARY_CSV <- "output/tables/inflation_summary.csv"

FIT_FROM <- as.Date("2026-07-01")
FIT_TO <- as.Date("2026-09-27") # day before the cap (included)
BT_FIT_TO <- as.Date("2026-09-13") # placebo fit end
BT_FROM <- as.Date("2026-09-14") # placebo projection window
PROJ_FROM <- as.Date("2026-09-28")
ANALYSIS_TO <- as.Date("2026-10-31")
MAX_ORDER <- 10L
N_SIM <- 2000L
SEED <- 20260928
VAT <- 1.22
W_CARBURANTI <- 0.045219 # NIC 2026 definitive weight, ECOICOP 07.2.2
REF_DAYS <- as.Date(c(
  "2026-09-01", "2026-09-11", "2026-09-21",
  "2026-10-01", "2026-10-11", "2026-10-21"
))

# ---------------------------------------------------------------- #
# ARDL machinery (explicit lags -> lm -> manual recursion)
# ---------------------------------------------------------------- #

make_lagged <- function(d, p, q) {
  out <- copy(d)
  for (i in seq_len(p)) out[[paste0("yl", i)]] <- shift(out$y, i)
  for (j in seq_len(q)) out[[paste0("xl", j)]] <- shift(out$x, j)
  out$xl0 <- out$x
  cols <- c("y", grep("^yl|^xl", names(out), value = TRUE))
  out[stats::complete.cases(out[, ..cols])]
}

fit_ardl <- function(d, p, q) {
  lag <- make_lagged(d, p, q)
  # note: paste0("yl", seq_len(0)) yields "yl" (zero-length recycles to ""),
  # so the p = 0 case needs an explicit guard
  yl_names <- if (p > 0) paste0("yl", seq_len(p)) else character(0)
  xs <- c(yl_names, paste0("xl", 0:q))
  f <- as.formula(paste("y ~", paste(xs, collapse = " + ")))
  fit <- lm(f, data = lag)
  list(fit = fit, lag = lag, p = p, q = q, xs = xs)
}

select_order <- function(d, max_order = MAX_ORDER) {
  rows <- rbindlist(lapply(0:max_order, function(p) {
    rbindlist(lapply(0:max_order, function(q) {
      if (p == 0 && q == 0) return(NULL)
      obj <- fit_ardl(d, p, q)
      data.table(p = p, q = q, n = nrow(obj$lag),
                 AIC = AIC(obj$fit), BIC = BIC(obj$fit))
    }))
  }))
  list(
    best_aic = rows[which.min(AIC)],
    best_bic = rows[which.min(BIC)],
    grid = rows
  )
}

coefs <- function(obj) {
  cc <- coef(obj$fit)
  list(
    a = cc[["(Intercept)"]],
    phi = if (obj$p > 0) cc[paste0("yl", seq_len(obj$p))] else numeric(0),
    th0 = cc[["xl0"]],
    th = if (obj$q > 0) cc[paste0("xl", seq_len(obj$q))] else numeric(0)
  )
}

long_run <- function(obj) {
  k <- coefs(obj)
  as.numeric((k$th0 + sum(k$th)) / (1 - sum(k$phi)))
}

project_ardl <- function(obj, hist_y, x_path, n_ahead,
                         n_sim = N_SIM, seed = SEED) {
  # hist_y: historical y up to the fit end; x_path: full series
  # (history+future). Returns list(point, lo, hi) (bootstrap 95% bands).
  k <- coefs(obj); p <- obj$p; q <- obj$q
  set.seed(seed)
  res <- residuals(obj$fit)
  idx0 <- length(hist_y)
  stopifnot(length(x_path) >= idx0 + n_ahead, idx0 >= max(p, q, 1))
  step <- function(yv, h, eps = 0) {
    t <- idx0 + h
    val <- k$a + k$th0 * x_path[t] + eps
    if (p > 0) for (i in seq_len(p)) val <- val + k$phi[i] * yv[t - i]
    if (q > 0) for (j in seq_len(q)) val <- val + k$th[j] * x_path[t - j]
    val
  }
  point <- hist_y
  for (h in seq_len(n_ahead)) point <- c(point, step(point, h))
  sims <- matrix(0, nrow = n_ahead, ncol = n_sim)
  for (s in seq_len(n_sim)) {
    yv <- hist_y
    for (h in seq_len(n_ahead)) {
      e <- sample(res, 1, replace = TRUE)
      yv <- c(yv, step(yv, h, e))
      sims[h, s] <- yv[length(yv)]
    }
  }
  list(
    point = point[(idx0 + 1):(idx0 + n_ahead)],
    lo = exp(apply(sims, 1, quantile, 0.025)),
    hi = exp(apply(sims, 1, quantile, 0.975))
  )
}

rmse <- function(e) sqrt(mean(e^2))

# ---------------------------------------------------------------- #
# Per-fuel pipeline
# ---------------------------------------------------------------- #

run_fuel <- function(dall, fuel_name) {
  d <- dall[fuel == fuel_name & date >= FIT_FROM & date <= ANALYSIS_TO]
  d <- d[order(date), .(date, eff_mean_gross, eff_mean_net,
                        y = log(eff_mean_net), x = log(brent_eur))]
  fit <- d[date <= FIT_TO]
  sel <- select_order(fit)
  p <- sel$best_aic$p; q <- sel$best_aic$q
  obj <- fit_ardl(fit, p, q)
  obj_bic <- fit_ardl(fit, sel$best_bic$p, sel$best_bic$q)

  cat("\n=====", fuel_name, "=====\n")
  cat("fit window:", format(FIT_FROM), "-", format(FIT_TO),
      "(", nrow(obj$lag), "obs after lags )\n")
  cat("order by AIC: (", p, ",", q, ")  by BIC: (",
      sel$best_bic$p, ",", sel$best_bic$q, ")\n")
  print(summary(obj$fit))
  cat("\nNewey-West (lag 7, prewhite=FALSE) robust coefficients:\n")
  print(coeftest(obj$fit,
                 vcov = NeweyWest(obj$fit, lag = 7, prewhite = FALSE)))
  cat("\nBreusch-Godfrey (order 7 and 14):\n")
  print(bgtest(obj$fit, order = 7))
  print(bgtest(obj$fit, order = 14))
  cat("\nRESET (powers 2:3):\n")
  print(resettest(obj$fit, power = 2:3))
  cat("\nlong-run pass-through elasticity (AIC spec):",
      round(long_run(obj), 4), "\n")
  cat("long-run pass-through elasticity (BIC spec):",
      round(long_run(obj_bic), 4), "\n")
  ph <- sum(coefs(obj)$phi)
  if (ph > 0 && ph < 1) {
    cat("half-life of shock (days, AIC spec):",
        round(log(0.5) / log(ph), 1), "\n")
  }

  # cross-check: ARDL::auto_ardl best order (AIC)
  aa <- tryCatch(auto_ardl(y ~ x, data = as.data.frame(fit),
                           max_order = MAX_ORDER, selection = "AIC"),
                 error = function(e) {
                   cat("auto_ardl failed:", conditionMessage(e), "\n"); NULL
                 })
  if (!is.null(aa)) {
    cat("auto_ardl cross-check, best order:\n")
    print(aa$best_order)
  }

  # ---- placebo backtest: fit ..09-13, project 09-14..27 ----
  fit_bt <- d[date <= BT_FIT_TO]
  sel_bt <- select_order(fit_bt)
  obj_bt <- fit_ardl(fit_bt, sel_bt$best_aic$p, sel_bt$best_aic$q)
  bt_win <- d[date >= BT_FROM & date <= FIT_TO]
  n_bt <- nrow(bt_win)
  proj_bt <- project_ardl(obj_bt, fit_bt$y, d$x, n_bt)
  rw_path <- rep(fit_bt$y[length(fit_bt$y)], n_bt) # random-walk benchmark
  bt <- data.table(
    date = bt_win$date, fuel = fuel_name,
    actual_net = exp(bt_win$y),
    cf_net = exp(proj_bt$point),
    rw_net = exp(rw_path)
  )
  bt[, `:=`(
    err_ardl_cpl = (actual_net - cf_net) * 100,
    err_rw_cpl = (actual_net - rw_net) * 100
  )]
  cat("\nbacktest", format(BT_FROM), "-", format(FIT_TO),
      ": RMSE ARDL", sprintf("%.3f", rmse(bt$err_ardl_cpl)),
      "c/l | RW", sprintf("%.3f", rmse(bt$err_rw_cpl)),
      "c/l | mean bias", sprintf("%.3f", mean(bt$err_ardl_cpl)), "c/l\n")

  # ---- counterfactual projection 09-28..10-31 ----
  proj_win <- d[date >= PROJ_FROM]
  n_p <- nrow(proj_win)
  hist_y <- fit$y # actual (uncapped) net logs up to 09-27
  proj <- project_ardl(obj, hist_y, d$x, n_p)
  cf <- data.table(
    date = proj_win$date, fuel = fuel_name,
    actual_gross_eff = proj_win$eff_mean_gross,
    actual_net_eff = proj_win$eff_mean_net,
    cf_net = exp(proj$point),
    cf_net_lo = proj$lo,
    cf_net_hi = proj$hi
  )
  cf[, excise := actual_gross_eff / VAT - actual_net_eff]
  cf[, `:=`(
    cf_gross = (cf_net + excise) * VAT,
    cf_gross_lo = (cf_net_lo + excise) * VAT,
    cf_gross_hi = (cf_net_hi + excise) * VAT
  )]
  cf[, gap_cpl := (actual_gross_eff - cf_gross) * 100]
  cat("\nprojection", format(PROJ_FROM), "-", format(max(cf$date)),
      ": mean gap actual - counterfactual",
      sprintf("%.2f", mean(cf$gap_cpl)), "c/l  (net path",
      sprintf("%.3f", exp(hist_y[length(hist_y)])), "->",
      sprintf("%.3f", tail(cf$cf_net, 1)), "EUR/l)\n")
  invisible(list(
    cf = cf, bt = bt, sel = sel, obj = obj,
    meta = data.table(
      fuel = fuel_name, p = p, q = q,
      order_bic = sprintf("(%d,%d)", sel$best_bic$p, sel$best_bic$q),
      lr_elasticity = long_run(obj),
      lr_elasticity_bic = long_run(obj_bic),
      backtest_rmse_cpl = rmse(bt$err_ardl_cpl),
      backtest_rmse_rw_cpl = rmse(bt$err_rw_cpl),
      backtest_bias_cpl = mean(bt$err_ardl_cpl),
      n_fit = nrow(obj$lag),
      resid_sd_log = sigma(obj$fit)
    )
  ))
}

# ---------------------------------------------------------------- #
# ISTAT reference days + CPI contribution
# ---------------------------------------------------------------- #

inflation_tables <- function(cf_all, dall) {
  # reference-day table; pre-cap days have no projection (the no-cap path IS
  # the observed path), so cf = actual there; post-cap days come from cf_all
  base <- dall[date %in% REF_DAYS,
               .(date, fuel, actual_gross = eff_mean_gross)]
  cf_oct <- cf_all[date %in% REF_DAYS, .(date, fuel, cf_gross)]
  days_long <- base[cf_oct, cf_gross := i.cf_gross, on = .(date, fuel)]
  days_long[is.na(cf_gross), cf_gross := actual_gross]
  days_long[, gap_cpl := (actual_gross - cf_gross) * 100]
  days_long[, period := format(date)]
  days_long <- days_long[, .(period, fuel, actual_gross, cf_gross, gap_cpl)]
  fwrite(days_long, INFL_DAYS_CSV)

  summ <- rbindlist(lapply(unique(days_long$fuel), function(f) {
    dl <- days_long[fuel == f]
    sep <- dl[substr(period, 1, 7) == "2026-09"]
    oct <- dl[substr(period, 1, 7) == "2026-10"]
    sep_a <- mean(sep$actual_gross); sep_c <- mean(sep$cf_gross)
    oct_a <- mean(oct$actual_gross); oct_c <- mean(oct$cf_gross)
    mom_a <- (oct_a / sep_a - 1) * 100
    mom_c <- (oct_c / sep_c - 1) * 100
    # ECOICOP 07.2.2 covers all motor fuels: split its NIC weight evenly
    # across petrol and diesel (documented assumption; ISTAT publishes no
    # public sub-class split)
    w_f <- W_CARBURANTI / length(unique(days_long$fuel))
    data.table(
      fuel = f,
      sep_avg_actual = sep_a, sep_avg_cf = sep_c,
      oct_avg_actual = oct_a, oct_avg_cf = oct_c,
      mom_actual_pct = mom_a, mom_cf_pct = mom_c,
      cap_effect_pp = mom_a - mom_c,
      cpi_actual_pp = w_f * mom_a,
      cpi_cf_pp = w_f * mom_c,
      cpi_effect_pp = w_f * (mom_a - mom_c)
    )
  }))
  # combined row: equal-weight blend of the two fuels (same 50/50 split)
  comb <- summ[, .(
    fuel = "TOT carburanti",
    sep_avg_actual = mean(sep_avg_actual), sep_avg_cf = mean(sep_avg_cf),
    oct_avg_actual = mean(oct_avg_actual), oct_avg_cf = mean(oct_avg_cf),
    mom_actual_pct = mean(mom_actual_pct), mom_cf_pct = mean(mom_cf_pct),
    cap_effect_pp = mean(cap_effect_pp),
    cpi_actual_pp = W_CARBURANTI * mean(mom_actual_pct),
    cpi_cf_pp = W_CARBURANTI * mean(mom_cf_pct),
    cpi_effect_pp = W_CARBURANTI * mean(mom_actual_pct - mom_cf_pct)
  )]
  summ <- rbind(summ, comb)
  fwrite(summ, INFL_SUMMARY_CSV)

  cat("\n===== ISTAT reference days (1/11/21) =====\n")
  print(days_long)
  cat("\nSep avg vs Oct avg, actual vs counterfactual "
      , "(weight carburanti = ", W_CARBURANTI, ", split 50/50):\n", sep = "")
  print(summ)
}

# ---------------------------------------------------------------- #
# Main
# ---------------------------------------------------------------- #

main <- function() {
  sink(RESULTS, split = TRUE)
  prices <- fread(FUEL_DAILY, select = c("date", "fuel", "eff_mean_gross", "eff_mean_net"))
  prices[, date := as.Date(date)]
  oil <- fread(OIL_FFILL, select = c("date", "brent_eur"))
  oil[, date := as.Date(date)]
  dall <- prices[oil, on = "date"][!is.na(eff_mean_net) & !is.na(brent_eur)]
  dall[, x := log(brent_eur)]
  stopifnot(!anyNA(dall$x))

  out <- lapply(c("Benzina", "Gasolio"), function(f) run_fuel(dall, f))
  cf_all <- rbindlist(lapply(out, `[[`, "cf"))
  bt_all <- rbindlist(lapply(out, `[[`, "bt"))
  meta_all <- rbindlist(lapply(out, `[[`, "meta"))
  fwrite(bt_all, BACKTEST_CSV)
  fwrite(cf_all, CF_CSV)
  fwrite(meta_all, ARDL_SUMMARY_CSV)
  inflation_tables(cf_all, dall)
  cat("\nDone.\n")
  sink()
}

main()
