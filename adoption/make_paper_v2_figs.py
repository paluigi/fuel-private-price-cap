"""Main exhibits for the revised (v2) paper — Steps 13-15.

Figure 1  National daily pump prices, Jan-Oct 2026, with policy markers
          (19 Mar spring excise cut, 4 Jul reinstatement, 25/28 Sep cap,
          6/28 Oct diesel excise steps) and the stepped diesel ceiling.
Figure 2  Brent in EUR (top) and national net-of-tax prices (bottom),
          indexed display for the pre-cap estimation window.
Figure 3  Actual vs conditional no-cap pump prices with 95% re-estimation
          bootstrap band and ISTAT reference-day markers (extends
          make_counterfactual_figs.py with the new bands).
Figure 4  Mechanism: (a) below-ceiling share by brand group; (b) the
          28 October diesel episode (mean price + below-ceiling share).

Outputs: output/figures/v2_fig1_prices.png, v2_fig2_brent_net.png,
         v2_fig3_counterfactual.png, v2_fig4_mechanism.png
Run from adoption/: uv run python make_paper_v2_figs.py
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

VAT = 1.22
FIG = config.OUT_DIR / "figures"
TAB = config.OUT_DIR / "tables"

# Okabe-Ito colour-blind-safe palette
O_BLUE, O_ORANGE, O_SKY, O_GREEN = "#0072B2", "#E69F00", "#56B4E9", "#009E73"
O_VERM, O_RED, O_BLACK = "#D55E00", "#CC79A7", "#000000"
GREY = "#7f7f7f"

FONT = dict(family="Helvetica, Arial, sans-serif", size=19, color="#000000")


def base_layout(fig, legend=False, h=620, legend_below=False):
    fig.update_layout(
        template="plotly_white",
        font=FONT,
        margin=dict(l=70, r=30, t=20, b=60 if not legend_below else 130),
        width=1350,
        height=h,
        showlegend=legend,
        legend=dict(
            orientation="h",
            # below the panels by default: in-figure titles occupy the band
            # just above the axes, and a top legend collides with them
            y=-0.20 if legend_below else 1.13,
            x=0.0,
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(gridcolor="#e6e6e6", zeroline=False)
    fig.update_yaxes(gridcolor="#e6e6e6", zeroline=False)


def load_series():
    fd = pl.read_csv(TAB / "fuel_daily_prices.csv", try_parse_dates=True)
    oil = pl.read_csv(TAB / "oil_fx_daily_ffill.csv", try_parse_dates=True)
    return fd, oil


# --------------------------------------------------------------------- F1
def fig1():
    fd, _ = load_series()
    d = fd.filter(pl.col("date") <= config.ANALYSIS_TO)
    fig = go.Figure()
    for fuel, name, color in (
        ("Benzina", "Petrol", O_BLUE),
        ("Gasolio", "Diesel", O_VERM),
    ):
        f = d.filter(pl.col("fuel") == fuel)
        fig.add_trace(go.Scatter(
            x=f["date"], y=f["eff_mean_gross"], mode="lines", name=name,
            line=dict(color=color, width=3)))
    # stepped diesel ceiling (strict levels; dotted)
    for x0, x1, lvl in [
        (config.CAP_DATE, config.GASOLIO_TAX_BACK, 2.200),
        (config.GASOLIO_TAX_BACK, config.GASOLIO_TAX_CUT, 2.261),
        (config.GASOLIO_TAX_CUT, config.ANALYSIS_TO, 2.212),
    ]:
        fig.add_shape(type="line", x0=x0, x1=x1, y0=lvl, y1=lvl,
                      line=dict(color=O_VERM, width=1.6, dash="dot"))
    fig.add_annotation(x=config.CAP_DATE, y=2.005, text="ceiling 2.00/2.20",
                       showarrow=False, xanchor="left", yanchor="top",
                       font=dict(size=15, color=GREY))
    for dt_, lbl, ytxt in (
        (dt.date(2026, 3, 19), "19 Mar: −20 c/l excise cut", 1.84),
        (dt.date(2026, 7, 4), "4 Jul: excise restored", 1.94),
        (config.CAP_DATE, "25/28 Sep: cap", 2.42),
        (config.GASOLIO_TAX_BACK, "6 Oct: diesel excise +5", 2.47),
        (config.GASOLIO_TAX_CUT, "28 Oct: diesel excise −4", 2.42),
    ):
        fig.add_vline(x=dt_, line=dict(color=GREY, width=1, dash="dash"))
        fig.add_annotation(x=dt_, y=ytxt, text=lbl, showarrow=False,
                           textangle=-90, xanchor="right", yanchor="top",
                           font=dict(size=13, color=GREY))
    fig.update_yaxes(title="Gross pump price (EUR/l)")
    base_layout(fig, legend=True)
    fig.write_image(FIG / "v2_fig1_prices.png", scale=2)
    print("wrote v2_fig1_prices.png")


# --------------------------------------------------------------------- F2
def fig2():
    fd, oil = load_series()
    d = fd.filter(pl.col("date") <= config.ANALYSIS_TO)
    o = oil.filter(pl.col("date") <= config.ANALYSIS_TO)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.06)
    fig.add_trace(go.Scatter(
        x=o["date"], y=o["brent_eur"], mode="lines", name="Brent (EUR/bbl)",
        line=dict(color=O_BLACK, width=2.5)), row=1, col=1)
    for fuel, name, color in (("Benzina", "Petrol net", O_BLUE),
                              ("Gasolio", "Diesel net", O_VERM)):
        f = d.filter(pl.col("fuel") == fuel)
        fig.add_trace(go.Scatter(
            x=f["date"], y=f["eff_mean_net"], mode="lines", name=name,
            line=dict(color=color, width=3)), row=2, col=1)
    fig.add_vline(x=config.CAP_DATE, line=dict(color=O_RED, width=1.5,
                                               dash="dash"), row="all")
    fig.add_annotation(x=config.CAP_DATE, y=100, text="cap",
                       showarrow=False, xanchor="left", font=dict(size=15, color=O_RED))
    fig.update_yaxes(title="Brent (EUR/bbl)", row=1, col=1)
    fig.update_yaxes(title="Net-of-tax price (EUR/l)", row=2, col=1)
    base_layout(fig, legend=True, h=760)
    fig.write_image(FIG / "v2_fig2_brent_net.png", scale=2)
    print("wrote v2_fig2_brent_net.png")


# --------------------------------------------------------------------- F3
def fig3():
    fd, _ = load_series()
    cf = pl.read_csv(TAB / "counterfactual_daily.csv", try_parse_dates=True)
    bands = pl.read_csv(TAB / "cf_bands_bootstrap.csv", try_parse_dates=True)
    # gross bands: (net band + excise) * VAT, excise from cf table
    cf = cf.join(bands.select("date", "fuel", "net_lo_reest", "net_hi_reest"),
                 on=["date", "fuel"])
    excise = cf["actual_gross_eff"] / VAT - cf["actual_net_eff"]
    cf = cf.with_columns(
        cf_gross_lo=(pl.col("net_lo_reest") + excise) * VAT,
        cf_gross_hi=(pl.col("net_hi_reest") + excise) * VAT,
    )
    ref_days = [dt.date(2026, 9, 1), dt.date(2026, 9, 11), dt.date(2026, 9, 21),
                dt.date(2026, 10, 1), dt.date(2026, 10, 11), dt.date(2026, 10, 21)]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.08,
                        subplot_titles=("Petrol", "Diesel"))
    for k, (fuel, name) in enumerate((("Benzina", "Petrol"), ("Gasolio", "Diesel"))):
        col = k + 1
        dd = fd.filter((pl.col("fuel") == fuel)
                       & (pl.col("date") >= dt.date(2026, 9, 1))).sort("date")
        c = cf.filter(pl.col("fuel") == fuel).sort("date")
        fig.add_trace(go.Scatter(
            x=dd["date"], y=dd["eff_mean_gross"], mode="lines", name="Actual",
            line=dict(color=O_BLUE if k == 0 else O_VERM, width=3)), row=1, col=col)
        fig.add_trace(go.Scatter(
            x=c["date"], y=c["cf_gross"], mode="lines", name="No-cap path",
            line=dict(color=O_BLACK, width=3, dash="dash")), row=1, col=col)
        fig.add_trace(go.Scatter(
            x=list(c["date"]) + list(c["date"][::-1]),
            y=list(c["cf_gross_hi"]) + list(c["cf_gross_lo"][::-1]),
            fill="toself", fillcolor="rgba(0,0,0,0.10)",
            line=dict(width=0), name="95% band (re-estimation)",
            showlegend=(k == 0)), row=1, col=col)
        rd = c.filter(pl.col("date").is_in(ref_days))
        fig.add_trace(go.Scatter(
            x=rd["date"], y=rd["cf_gross"], mode="markers",
            name="Reference days", marker=dict(color=O_GREEN, size=10,
                                               symbol="diamond"),
            showlegend=(k == 0)), row=1, col=col)
        fig.add_vline(x=config.CAP_DATE, line=dict(color=GREY, width=1.2,
                                                   dash="dash"), row=1, col=col)
    fig.update_yaxes(title="Gross pump price (EUR/l)", range=[1.95, 2.62])
    fig.update_annotations(font_size=18)
    base_layout(fig, legend=True, h=560, legend_below=True)
    fig.write_image(FIG / "v2_fig3_counterfactual.png", scale=2)
    print("wrote v2_fig3_counterfactual.png")


# --------------------------------------------------------------------- F4
def fig4():
    p = pl.read_parquet(
        config.ADOPTION_PANEL,
        columns=["date", "fuel", "id_impianto", "prezzo", "at_cap", "bandiera"],
    ).filter(pl.col("date") >= config.CAP_DATE)
    groups = {"Agip Eni": "Eni", "Q8": "Q8", "Api-Ip": "Api-Ip",
              "Esso": "Esso", "Tamoil": "Tamoil",
              "Pompe Bianche": "White pumps"}
    p = p.with_columns(
        group=pl.col("bandiera").replace_strict(groups, default=None)
    ).filter(pl.col("group").is_not_null())

    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.09,
                        subplot_titles=("Below-ceiling share by brand group",
                                        "Diesel at the 28 Oct excise cut"),
                        specs=[[{"type": "xy"}, {"type": "xy"}]])

    # (a) petrol below-ceiling share by group
    colors = {"Eni": O_BLACK, "Q8": O_BLUE, "Api-Ip": O_SKY,
              "Esso": O_GREEN, "Tamoil": O_ORANGE, "White pumps": O_VERM}
    a = p.filter(pl.col("fuel") == "Benzina").group_by("date", "group").agg(
        share=pl.col("at_cap").mean()).sort("date")
    for g in ["Eni", "Q8", "Api-Ip", "Esso", "Tamoil", "White pumps"]:
        gg = a.filter(pl.col("group") == g)
        fig.add_trace(go.Scatter(
            x=gg["date"], y=100 * gg["share"], mode="lines", name=g,
            line=dict(color=colors[g], width=2.6)), row=1, col=1)
    fig.update_yaxes(title="Petrol share below ceiling (%)", range=[0, 102],
                     row=1, col=1)

    # (b) diesel 24-31 Oct: mean price (left) + below-share (right)
    b = (p.filter((pl.col("fuel") == "Gasolio")
                  & (pl.col("date") >= dt.date(2026, 10, 24)))
         .group_by("date").agg(mean=pl.col("prezzo").mean(),
                               share=pl.col("at_cap").mean()).sort("date"))
    fig.add_trace(go.Scatter(
        x=b["date"], y=b["mean"], mode="lines+markers", name="Mean diesel price",
        line=dict(color=O_VERM, width=3), showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=b["date"], y=2.261 + 0.0 * b["mean"], mode="lines",
        name="old ceiling 2.261", line=dict(color=GREY, width=1.5, dash="dot"),
        showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=b["date"], y=2.212 + 0.0 * b["mean"], mode="lines",
        name="new ceiling 2.212", line=dict(color=O_BLACK, width=1.5, dash="dot"),
        showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=b["date"], y=b["mean"], mode="markers", name="share below 2.212",
        marker=dict(color=O_SKY, size=8, symbol="circle",
                    opacity=[0.3 + 0.7 * s for s in b["share"]]),
        showlegend=False, customdata=100 * b["share"],
        hovertemplate="%{y:.3f} %{customdata:.0f}%"), row=1, col=2)
    fig.add_annotation(x=dt.date(2026, 10, 28), y=2.266,
                       text="excise −4 c/l", showarrow=False,
                       font=dict(size=14, color=GREY), xanchor="left")
    fig.update_yaxes(title="Diesel price (EUR/l)", range=[2.20, 2.29],
                     row=1, col=2)
    fig.update_xaxes(range=[dt.date(2026, 10, 23), dt.date(2026, 11, 1)],
                     row=1, col=2)
    fig.update_annotations(font_size=18)
    base_layout(fig, legend=True, h=560, legend_below=True)
    fig.write_image(FIG / "v2_fig4_mechanism.png", scale=2)
    print("wrote v2_fig4_mechanism.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
