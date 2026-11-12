"""Counterfactual figures for the research paper.

Follows the styling conventions of make_report_figs.py (plotly_white,
larger fonts, no chart titles, € units, firebrick cap labels, Petrol /
Diesel panel titles). Data window: 2026-07-01 .. 2026-10-31.

Outputs (committed, adoption/output/figures/):
  fig_brent_net_index.png — Brent EUR/bbl, net petrol, net diesel, each
      indexed to 100 on 2026-07-01; cap-date vline.
  fig_counterfactual.png — actual vs ARDL-counterfactual pump prices per
      fuel, 95% bootstrap band, tax-adjusted cap lines, ISTAT reference
      days marked.

Run from the repo root:  uv run python adoption/make_counterfactual_figs.py
"""

import datetime as dt
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import polars as pl
from plotly.subplots import make_subplots

HERE = Path(__file__).resolve().parent
TAB = HERE / "output" / "tables"
FIG = HERE / "output" / "figures"

pio.templates.default = "plotly_white"

CAP_DATE = dt.date(2026, 9, 28)
EXCISE_STEP = dt.date(2026, 10, 6)
EXCISE_CUT = dt.date(2026, 10, 28)
SEP_REF_DAYS = (dt.date(2026, 9, 1), dt.date(2026, 9, 11), dt.date(2026, 9, 21))
OCT_REF_DAYS = (dt.date(2026, 10, 1), dt.date(2026, 10, 11), dt.date(2026, 10, 21))

FONT = 22
LINE_W = 3.5
FUEL_COLOR = {"Benzina": "#1f77b4", "Gasolio": "#d62728"}
FUEL_EN = {"Benzina": "Petrol", "Gasolio": "Diesel"}
FIREBRICK = "#B22222"
GREY = "#7F7F7F"
SIZE = (1400, 620)


def load_daily() -> pl.DataFrame:
    fuel = pl.read_csv(
        TAB / "fuel_daily_prices.csv",
        columns=["date", "fuel", "eff_mean_gross", "eff_mean_net"],
        try_parse_dates=True,
    )
    oil = pl.read_csv(
        TAB / "oil_fx_daily_ffill.csv", columns=["date", "brent_eur"],
        try_parse_dates=True,
    )
    return fuel.join(oil, on="date", how="inner").sort("date")


def fig_index(df: pl.DataFrame) -> Path:
    """Brent EUR + net petrol + net diesel, all indexed to 1 Jul = 100."""
    first = df["date"].min()
    base = df.filter(pl.col("date") == first)
    base_map = {
        "Brent": base["brent_eur"][0],
        "Benzina": base.filter(pl.col("fuel") == "Benzina")["eff_mean_net"][0],
        "Gasolio": base.filter(pl.col("fuel") == "Gasolio")["eff_mean_net"][0],
    }
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["brent_eur"] / base_map["Brent"] * 100,
        name="Brent (€/bbl)", mode="lines",
        line=dict(color="black", width=LINE_W)))
    for fuel in ("Benzina", "Gasolio"):
        d = df.filter(pl.col("fuel") == fuel)
        fig.add_trace(go.Scatter(
            x=d["date"], y=d["eff_mean_net"] / base_map[fuel] * 100,
            name=f"{FUEL_EN[fuel]} net price", mode="lines",
            line=dict(color=FUEL_COLOR[fuel], width=LINE_W)))
    fig.add_vline(
        x=CAP_DATE.isoformat(), line=dict(color=FIREBRICK, width=2, dash="dot"),
        annotation=dict(
            text="cap 28 Sep", font=dict(size=int(FONT * 0.8), color=FIREBRICK),
            xanchor="left", yanchor="top"),
    )
    n = df["date"].n_unique()
    fig.update_layout(
        width=SIZE[0], height=SIZE[1],
        font=dict(size=FONT),
        yaxis_title="Index (1 Jul 2026 = 100)",
        legend=dict(orientation="h", y=1.12, x=0),
        margin=dict(l=70, r=30, t=60, b=60),
        xaxis=dict(dtick=max(1, n // 10) * 86_400_000,
                   tickformat="%d %b", tickangle=0),
    )
    out = FIG / "fig_brent_net_index.png"
    fig.write_image(out, scale=2)
    return out


def fig_counterfactual(cf: pl.DataFrame, daily: pl.DataFrame) -> Path:
    """Actual vs counterfactual pump prices, one panel per fuel.

    The actual series is shown from 1 Sep; the counterfactual and its
    band exist only from the cap date (28 Sep). ISTAT reference days
    (1st, 11th, 21st) are marked with filled dots on the actual line
    (Sep and Oct) and open dots on the counterfactual line (Oct only,
    where a counterfactual exists).
    """
    daily = daily.filter(pl.col("date") >= dt.date(2026, 9, 1))
    fig = make_subplots(
        rows=1, cols=2, shared_yaxes=False,
        subplot_titles=list(FUEL_EN.values()),
        horizontal_spacing=0.08,
    )
    for k, fuel in enumerate(("Benzina", "Gasolio")):
        d = cf.filter(pl.col("fuel") == fuel).sort("date")
        act = (
            daily.filter(pl.col("fuel") == fuel)
            .sort("date")
            .select(
                pl.col("date"),
                pl.col("eff_mean_gross").alias("actual_gross_eff"),
            )
        )
        col = k + 1
        # bootstrap band
        fig.add_trace(go.Scatter(
            x=list(d["date"]) + list(d["date"][::-1]),
            y=list(d["cf_gross_hi"]) + list(d["cf_gross_lo"][::-1]),
            fill="toself", fillcolor="rgba(178,34,34,0.12)",
            line=dict(width=0), showlegend=(k == 0),
            name="95% band (no cap)", legendgroup="band",
            hoverinfo="skip"), row=1, col=col)
        fig.add_trace(go.Scatter(
            x=d["date"], y=d["cf_gross"], name="Counterfactual (no cap)",
            legendgroup="cf", showlegend=(k == 0),
            line=dict(color=FIREBRICK, width=LINE_W, dash="dash")),
            row=1, col=col)
        fig.add_trace(go.Scatter(
            x=act["date"], y=act["actual_gross_eff"],
            name="Actual (with cap)",
            legendgroup="act", showlegend=(k == 0),
            line=dict(color=FUEL_COLOR[fuel], width=LINE_W)),
            row=1, col=col)
        # ISTAT reference days: filled dots on the actual line (Sep + Oct)
        rd = act.filter(pl.col("date").is_in(
            list(SEP_REF_DAYS) + list(OCT_REF_DAYS)))
        fig.add_trace(go.Scatter(
            x=rd["date"], y=rd["actual_gross_eff"], mode="markers",
            marker=dict(color="black", size=10, symbol="circle"),
            showlegend=False, hoverinfo="skip"), row=1, col=col)
        # open dots on the counterfactual line (Oct only)
        rd_cf = d.filter(pl.col("date").is_in(list(OCT_REF_DAYS)))
        fig.add_trace(go.Scatter(
            x=rd_cf["date"], y=rd_cf["cf_gross"], mode="markers",
            marker=dict(color=FIREBRICK, size=11, symbol="circle-open",
                        line=dict(width=2.5)),
            showlegend=False, hoverinfo="skip"), row=1, col=col)
        # cap line: diesel is tax-adjusted (+6.1 c/l from 6 Oct, -4.88 c/l
        # from 28 Oct -> 2.212; revision D4)
        if fuel == "Gasolio":
            cap_steps = [(d["date"].min(), 2.20), (EXCISE_STEP, 2.261),
                         (EXCISE_CUT, 2.212)]
        else:
            cap_steps = [(d["date"].min(), 2.00)]
        for k, (x0, level) in enumerate(cap_steps):
            x1 = (cap_steps[k + 1][0] if k + 1 < len(cap_steps)
                  else d["date"].max())
            fig.add_shape(type="line", x0=x0.isoformat(), x1=x1.isoformat(),
                          y0=level, y1=level,
                          line=dict(color=FIREBRICK, width=1.5, dash="dot"),
                          row=1, col=col)
        fig.add_vline(x=CAP_DATE.isoformat(),
                      line=dict(color=GREY, width=1.5, dash="dash"),
                      row=1, col=col)
    fig.update_layout(
        width=SIZE[0], height=SIZE[1],
        font=dict(size=FONT),
        legend=dict(orientation="h", y=1.13, x=0),
        margin=dict(l=70, r=30, t=70, b=60),
    )
    fig.update_yaxes(tickprefix="€", tickformat=".2f")
    n = daily["date"].n_unique()  # spans 1 Sep .. 31 Oct
    fig.update_xaxes(dtick=max(1, n // 6) * 86_400_000,
                     tickformat="%d %b", tickangle=0)
    out = FIG / "fig_counterfactual.png"
    fig.write_image(out, scale=2)
    return out


def main() -> None:
    daily = load_daily()
    cf = pl.read_csv(TAB / "counterfactual_daily.csv", try_parse_dates=True)
    print(f"wrote {fig_index(daily)}")
    print(f"wrote {fig_counterfactual(cf, daily)}")


if __name__ == "__main__":
    main()
