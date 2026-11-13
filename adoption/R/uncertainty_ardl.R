# Uncertainty and validation for the oil ARDL counterfactual (Step 08).
#
# Sources R/analysis_ardl.R (ARDL_SKIP_MAIN=1) and adds:
#   1. expanding-origin backtests: fit through several origins, project a
#      fixed 14-day (and 28-day where data allow) horizon, compare with
#      actuals and the random-walk benchmark;
#   2. re-estimation bootstrap of the main projection (resample residuals,
#      rebuild the in-sample y path, re-estimate the lm, re-project): bands
#      that include coefficient uncertainty, unlike the iid-shock bands;
#   3. moving-block bootstrap (block length 7) of the projection shocks:
#      serial dependence in the shocks;
#   4. scenario variants: fit window (Jan vs Jul start; to 27 Sep vs 24 Sep
#      announcement), estimation sample (universe vs balanced vs
#      regularity-filtered net series), Brent path +-5%;
#      each variant's October mean gap and CPI effect -> spec_range.csv.
#
# Run from adoption/: Rscript R/uncertainty_ardl.R
# Outputs: output/uncertainty_results.txt
#          output/tables/backtest_origins.csv
#          output/tables/cf_bands_bootstrap.csv
#          output/tables/spec_range.csv

Sys.setenv(ARDL_SKIP_MAIN = "1")
.libPaths(c("~/Rlibs", .libPaths()))
source("R/analysis_ardl.R")

BT_ORIGINS <- as.Date(c("2026-05-31", "2026-06-30", "2026-07-31",
                        "2026-08-31", "2026-09-13"))
HORIZONS <- c(14L, 28L)
N_BOOT <- 1000L
BLOCK <- 7L
BRENT_SCALE <- 0.05

OUT_TXT <- "output/uncertainty_results.txt"
BT_CSV <- "output/tables/backtest_origins.csv"
BANDS_CSV <- "output/tables/cf_bands_bootstrap.csv"
SPEC_CSV <- "output/tables/spec_range.csv"

load_data <- function(net_col = "eff_mean_net") {
  prices <- fread(FUEL_DAILY, select = c("date", "fuel", "eff_mean_gross",
                                         net_col, "reg_mean_gross",
                                         "bal_mean_net"))
  setnames(prices, net_col, "net_use")
  prices[, date := as.Date(date)]
  oil <- fread(OIL_FFILL, select = c("date", "brent_eur"))
  oil[, date := as.Date(date)]
  dall <- prices[oil, on = "date"][!is.na(net_use) & !is.na(brent_eur)]
  dall[, y := log(net_use)]
  dall[, x := log(brent_eur)]
  dall
}

# ---- 1. expanding-origin backtests -------------------------------------- #
backtest_origins <- function(dall) {
  rows <- rbindlist(lapply(c("Benzina", "Gasolio"), function(f) {
    d <- dall[fuel == f & date >= FIT_FROM & date <= ANALYSIS_TO]
    d <- d[order(date)]
    rbindlist(lapply(BT_ORIGINS, function(o) {
      fit <- d[date <= o]
      if (nrow(fit) < 60) return(NULL)
      sel <- select_order(fit)
      obj <- fit_ardl(fit, sel$best_bic$p, sel$best_bic$q)
      rbindlist(lapply(HORIZONS, function(h) {
        # evaluation window must stay PRE-CAP: clip at FIT_TO (27 Sep) so no
        # backtest ever scores the model against cap-affected actuals
        win <- d[date > o & date <= FIT_TO][1:h]
        if (nrow(win) < h) return(NULL)
        pr <- project_ardl(obj, fit$y, d$x, h, n_sim = 200)
        rw <- rep(fit$y[nrow(fit)], h)
        data.table(
          fuel = f, origin = o, horizon = h, p = sel$best_bic$p,
          q = sel$best_bic$q, n_fit = nrow(fit),
          rmse_ardl_cpl = rmse((exp(win$y) - exp(pr$point)) * 100),
          rmse_rw_cpl = rmse((exp(win$y) - exp(rw)) * 100),
          bias_ardl_cpl = mean((exp(win$y) - exp(pr$point)) * 100)
        )
      }))
    }))
  }))
  fwrite(rows, BT_CSV)
  cat("\n===== expanding-origin backtests =====\n")
  print(rows[])
}

# ---- 2+3. bootstrap bands for the main projection ------------------------ #
bootstrap_bands <- function(dall) {
  rows <- rbindlist(lapply(c("Benzina", "Gasolio"), function(f) {
    d <- dall[fuel == f & date >= FIT_FROM & date <= ANALYSIS_TO]
    d <- d[order(date), .(date, y, x)]
    fit <- d[date <= FIT_TO]
    sel <- select_order(fit)
    obj <- fit_ardl(fit, sel$best_bic$p, sel$best_bic$q)
    proj_win <- d[date >= PROJ_FROM]
    n_p <- nrow(proj_win)
    set.seed(SEED)
    res <- residuals(obj$fit)
    k <- coefs(obj); p <- obj$p; q <- obj$q
    idx0 <- nrow(fit)
    x_path <- d$x
    step <- function(yv, h, eps = 0) {
      t <- idx0 + h
      val <- k$a + k$th0 * x_path[t] + eps
      if (p > 0) for (i in seq_len(p)) val <- val + k$phi[i] * yv[t - i]
      if (q > 0) for (j in seq_len(q)) val <- val + k$th[j] * x_path[t - j]
      val
    }
    # (a) iid shocks (matches analysis_ardl.R bands)
    sims_iid <- matrix(0, n_p, N_BOOT)
    for (s in seq_len(N_BOOT)) {
      yv <- fit$y
      out <- numeric(n_p)
      for (h in seq_len(n_p)) {
        e <- sample(res, 1)
        yv <- c(yv, step(yv, h, e)); out[h] <- yv[length(yv)]
      }
      sims_iid[, s] <- out
    }
    # (b) moving-block shocks (block length BLOCK), no re-estimation
    n_res <- length(res)
    n_blocks <- ceiling(n_p / BLOCK)
    sims_blk <- matrix(0, n_p, N_BOOT)
    for (s in seq_len(N_BOOT)) {
      starts <- sample(seq_len(n_res - BLOCK + 1), n_blocks, replace = TRUE)
      shocks <- as.vector(sapply(starts, function(st) res[st:(st + BLOCK - 1)]))[1:n_p]
      yv <- fit$y; out <- numeric(n_p)
      for (h in seq_len(n_p)) {
        yv <- c(yv, step(yv, h, shocks[h])); out[h] <- yv[length(yv)]
      }
      sims_blk[, s] <- out
    }
    # (c) re-estimation bootstrap: resample residuals in-sample, rebuild y,
    #     re-fit the lm, re-project with the iid-shock scheme (fewer sims)
    n_b2 <- 400L
    sims_re <- matrix(0, n_p, n_b2)
    lag0 <- make_lagged(fit, p, q)
    yhat <- fitted(obj$fit)
    fml <- as.formula(paste("y ~", paste(obj$xs, collapse = " + ")))
    for (s in seq_len(n_b2)) {
      e_star <- sample(res, length(res), replace = TRUE)
      y_star <- yhat + e_star
      d_star <- copy(lag0)
      # replace the dependent variable rows with the bootstrapped y
      d_star$y <- y_star
      fit_star <- tryCatch(lm(fml, data = d_star), error = function(e) NULL)
      if (is.null(fit_star)) next
      cc <- coef(fit_star)
      k2 <- list(a = cc[["(Intercept)"]],
                 phi = if (p > 0) cc[paste0("yl", seq_len(p))] else numeric(0),
                 th0 = cc[["xl0"]],
                 th = if (q > 0) cc[paste0("xl", seq_len(q))] else numeric(0))
      if (any(is.na(unlist(k2)))) next
      st2 <- function(yv, h, eps = 0) {
        t <- idx0 + h
        val <- k2$a + k2$th0 * x_path[t] + eps
        if (p > 0) for (i in seq_len(p)) val <- val + k2$phi[i] * yv[t - i]
        if (q > 0) for (j in seq_len(q)) val <- val + k2$th[j] * x_path[t - j]
        val
      }
      yv <- fit$y; out <- numeric(n_p)
      for (h in seq_len(n_p)) {
        yv <- c(yv, st2(yv, h, sample(res, 1))); out[h] <- yv[length(yv)]
      }
      sims_re[, s] <- out
    }
    qtl <- function(m) {
      list(lo = exp(apply(m, 1, quantile, 0.025, na.rm = TRUE)),
           hi = exp(apply(m, 1, quantile, 0.975, na.rm = TRUE)))
    }
    qi <- qtl(sims_iid); qb <- qtl(sims_blk); qr <- qtl(sims_re)
    data.table(
      date = proj_win$date, fuel = f,
      net_lo_iid = qi$lo, net_hi_iid = qi$hi,
      net_lo_block = qb$lo, net_hi_block = qb$hi,
      net_lo_reest = qr$lo, net_hi_reest = qr$hi
    )
  }))
  fwrite(rows, BANDS_CSV)
  cat("\n===== bootstrap bands (95%) on the net path =====\n")
  print(rows[, lapply(.SD, mean), by = fuel,
             .SDcols = patterns("net_(lo|hi)")])
}

# ---- 4. scenario variants ------------------------------------------------ #
variant_gap_cpi <- function(dall, label, fit_from = FIT_FROM,
                            fit_to = FIT_TO, net_col = "eff_mean_net",
                            brent_mult = 1) {
  prices <- fread(FUEL_DAILY, select = c("date", "fuel", "eff_mean_gross", net_col))
  setnames(prices, net_col, "net_use")
  prices[, date := as.Date(date)]
  oil <- fread(OIL_FFILL, select = c("date", "brent_eur"))
  oil[, date := as.Date(date)]
  if (brent_mult != 1) {
    oil[date >= PROJ_FROM, brent_eur := brent_eur * brent_mult]
  }
  dall2 <- prices[oil, on = "date"][!is.na(net_use) & !is.na(brent_eur)]
  dall2[, `:=`(y = log(net_use), x = log(brent_eur))]
  rbindlist(lapply(c("Benzina", "Gasolio"), function(f) {
    d <- dall2[fuel == f & date >= fit_from & date <= ANALYSIS_TO]
    d <- d[order(date), .(date, eff_mean_gross, y, x)]
    fit <- d[date <= fit_to]
    sel <- select_order(fit)
    obj <- fit_ardl(fit, sel$best_bic$p, sel$best_bic$q)
    proj_win <- d[date >= PROJ_FROM]
    pr <- project_ardl(obj, fit$y, d$x, nrow(proj_win), n_sim = 200)
    cf_gross <- (exp(pr$point) +
                   (proj_win$eff_mean_gross / VAT - exp(proj_win$y))) * VAT
    gap <- (proj_win$eff_mean_gross - cf_gross) * 100
    # CPI effect at reference days
    rd <- proj_win[date %in% REF_DAYS]
    cfr <- (exp(pr$point[which(proj_win$date %in% REF_DAYS)]) +
              (rd$eff_mean_gross / VAT - exp(rd$y))) * VAT
    base <- dall2[date %in% REF_DAYS & fuel == f]
    sep_a <- mean(base[substr(date, 1, 7) == "2026-09"]$eff_mean_gross)
    oct_a <- mean(base[substr(date, 1, 7) == "2026-10"]$eff_mean_gross)
    mom_a <- (oct_a / sep_a - 1) * 100
    mom_c <- (mean(cfr[substr(rd$date, 1, 7) == "2026-10"]) / sep_a - 1) * 100
    data.table(fuel = f, variant = label, p = sel$best_bic$p,
               q = sel$best_bic$q, mean_gap_cpl = mean(gap),
               end_gap_cpl = tail(gap, 1), cpi_effect_pp = W_FUEL[[f]] *
                 (mom_a - mom_c))
  }))
}

scenario_table <- function(dall) {
  rows <- rbindlist(list(
    variant_gap_cpi(dall, "fit from Jan (baseline)"),
    variant_gap_cpi(dall, "fit from Jul (v1 window)", fit_from = as.Date("2026-07-01")),
    variant_gap_cpi(dall, "fit to 24 Sep (announcement)", fit_to = as.Date("2026-09-24")),
    variant_gap_cpi(dall, "balanced panel series", net_col = "bal_mean_net"),
    variant_gap_cpi(dall, "regularity sample series", net_col = "reg_mean_net"),
    variant_gap_cpi(dall, "Brent +5% post-cap", brent_mult = 1 + BRENT_SCALE),
    variant_gap_cpi(dall, "Brent -5% post-cap", brent_mult = 1 - BRENT_SCALE)
  ))
  fwrite(rows, SPEC_CSV)
  cat("\n===== scenario variants (October mean gap / CPI effect) =====\n")
  print(rows[])
}

main_unc <- function() {
  sink(OUT_TXT, split = TRUE)
  dall <- load_data()
  backtest_origins(dall)
  bootstrap_bands(dall)
  scenario_table(dall)
  cat("\nDone.\n")
  sink()
}

main_unc()
