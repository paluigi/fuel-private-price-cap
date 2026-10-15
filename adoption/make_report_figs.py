"""Export-ready report figures, v2 (larger fonts, no titles, tighter axes).

Same outputs as v1 (1_..7_ prefixed PNGs in output/figures/), restyled:
  a) legend/tick/annotation fonts enlarged; headline titles removed
  b) lines +50% thicker; axis ranges trimmed to the data; x ticks doubled
  c) figs 1-2: aggregate label "Aggregate"
  d) fig 2: excise annotation dropped; hline labels "cap 2.20 EUR/l from
     28 Sep" / "cap 2.261 EUR/l from 6 Oct"; cap-start vline label removed
  e) fig 3: window starts 26 Sep (2 pre-cap days); dashed vline at 28 Sep;
     per-panel hline labels "cap 2.00 EUR/l" / "cap 2.20 EUR/l"; the
     excise vline label becomes "cap 2.261 EUR/l"; panel titles Petrol /
     Diesel only.

Figures 4-7 remain as-is copies of the paper's figures 3, 4, 9, 10.

v3: square-format figures 10-12 — same content as figures 1-3, on a
square canvas, +50% font size, sparser date ticks (weekly for figs
10-11, every 4 days for fig 12). Fig 11's cap labels wrap onto two
lines so they can hug their dotted cap lines without reaching the
mid-September price ascent. Like figures 1-3, the data window follows
whatever the caches contain when the script runs.

Run from the repo root:  uv run python adoption/make_report_figs.py
(add --new-only to regenerate only figures 10-12)
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

_BROWSER = (
    "/home/ubuntu/.cache/ms-playwright/chromium_headless_shell-1243/"
    "chrome-headless-shell-linux-arm64/chrome-headless-shell"
)
if Path(_BROWSER).exists():  # pin the browser only on the machine that has it
    os.environ.setdefault("BROWSER_PATH", _BROWSER)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import datetime as dt

import plotly.graph_objects as go
import polars as pl

from fuel_price_cap import config

FIG = config.FIGURES_DIR
ADOPT_FIG = ROOT / "adoption" / "output" / "figures"
ADOPT_TAB = ROOT / "adoption" / "output" / "tables"

CUT = dt.date(2026, 9, 1)
CAP_DATE = dt.date(2026, 9, 28)
EXCISE_STEP = dt.date(2026, 10, 6)
FIG3_CUT = dt.date(2026, 9, 26)  # two days before the cap

FONT = 22   # base font: ticks, legend, annotations
LINE_W = 3  # base 2 -> +50%

# figures 10-12: square canvas, +50% font over the report base; the data
# window follows the caches (end=None), like figures 1-3
FONT_SQ = 33
SQ_SIZE = (1100, 1100)

GROUP_EN = {"Majors": "Majors", "Large": "Large", "Pompe Bianche": "Independents"}
AGG_EN = "Aggregate"

GROUP_COLORS = {"Majors": "#D62728", "Large": "#1F77B4", "Pompe Bianche": "#7F7F7F"}
AGG_COLOR = "#0B6E4F"


def group_price_chart_en(
    fuel: str,
    show_excise_line: bool,
    stem: str,
    *,
    size: tuple[int, int] = (1400, 620),
    font: int = FONT,
    xdtick_days: int = 3,
    end: dt.date | None = None,
    cap_labels: str = "inline",
) -> Path:
    prices = pl.read_parquet(config.DATA_DIR / "prices_enriched.parquet")
    tipo = "Stradale"

    def stats(dims: list[str]) -> pl.DataFrame:
        q = prices.filter(
            (pl.col("fuel") == fuel) & (pl.col("tipo_impianto") == tipo)
        ).filter(pl.col("date") >= CUT)
        if end is not None:
            q = q.filter(pl.col("date") <= end)
        return (
            q.group_by(["date", *dims])
            .agg(mean_prezzo=pl.col("prezzo").mean())
            .sort("date")
        )

    overall = stats([])
    by_group = stats(["group"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=overall["date"], y=overall["mean_prezzo"], mode="lines",
            name=AGG_EN, line=dict(color=AGG_COLOR, width=LINE_W + 1, dash="dot"),
        )
    )
    for group in config.GROUP_ORDER:
        s = by_group.filter(pl.col("group") == group)
        if s.height:
            fig.add_trace(
                go.Scatter(
                    x=s["date"], y=s["mean_prezzo"], mode="lines",
                    name=GROUP_EN[group],
                    line=dict(color=GROUP_COLORS[group], width=LINE_W),
                )
            )

    threshold = config.THRESHOLDS[fuel]
    second_cap = (
        config.GASOLIO_CAP_AFTER
        if fuel == "Gasolio" and overall["date"].max() >= EXCISE_STEP
        else None
    )
    caps = [threshold, second_cap] if second_cap else [threshold]

    y_lo = overall["mean_prezzo"].min()
    y_hi = overall["mean_prezzo"].max()
    # include the cap hline(s) and their labels in the y range; extra headroom
    # below for the "cap ... from 28 Sep" label
    y_min = min(y_lo, *caps)
    y_max = max(y_hi, *caps)
    pad = (y_max - y_min) * 0.06
    pad_hi = (y_max - y_min) * 0.12  # headroom: some series still got clipped
    pad_lo = pad * 2.5  # room for the hline label under the cap line

    # square variant: two-line cap labels hug their dotted line while staying
    # clear of the mid-September price ascent (the one-line text reaches it)
    sep = "<br>" if cap_labels == "wrapped" else " "
    fig.add_hline(
        y=threshold, line_dash="dot", line_color="firebrick",
        annotation_text=f"cap {threshold:.2f} EUR/l{sep}from 28 Sep",
        annotation_position="top left", annotation_align="left",
        annotation_font=dict(size=font, color="firebrick"),
    )
    if second_cap is not None:
        fig.add_hline(
            y=second_cap, line_dash="dot", line_color="firebrick",
            annotation_text=f"cap {second_cap:.3f} EUR/l{sep}from 6 Oct",
            annotation_position="top left", annotation_align="left",
            annotation_font=dict(size=font, color="firebrick"),
        )
    # vlines carry no text labels (d)
    fig.add_vline(x=CAP_DATE.isoformat(), line_dash="dash", line_color="black")
    if show_excise_line:
        fig.add_vline(x=EXCISE_STEP.isoformat(), line_dash="dash", line_color="black")

    fig.update_layout(
        font=dict(size=font),
        margin=dict(l=10, r=30, t=15, b=10),
        template="plotly_white",
        hovermode="x unified",
        width=size[0],
        height=size[1],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
    )
    fig.update_xaxes(
        tickformat="%d %b", tickangle=0,
        dtick=xdtick_days * 86400000,
        range=[CUT, overall["date"].max() + dt.timedelta(days=1)],
    )
    fig.update_yaxes(
        tickformat=".2f", range=[y_min - pad_lo, y_max + pad_hi],
        title=dict(text="EUR/l", font=dict(size=font)),
    )
    out = FIG / f"{stem}.png"
    fig.write_image(out, scale=2)
    return out


def fig3_adoption_share(
    stem: str = "3_adoption_share_daily",
    *,
    size: tuple[int, int] = (1400, 620),
    font: int = FONT,
    xdtick_days: int = 2,
    end: dt.date | None = None,
) -> Path:
    """Single panel, two lines (Petrol/Diesel), no in-panel text."""
    panel = pl.read_parquet(ADOPT_TAB / "adoption_panel.parquet")
    q = panel.filter(pl.col("date") >= FIG3_CUT)
    if end is not None:
        q = q.filter(pl.col("date") <= end)
    d = (
        q.group_by(["date", "fuel"])
        .agg(pl.col("at_cap").mean().alias("share"))
        .sort(["fuel", "date"])
    )

    fig = go.Figure()
    colors = {"Benzina": "#1f77b4", "Gasolio": "#d62728"}
    names = {"Benzina": "Petrol", "Gasolio": "Diesel"}
    for fuel in ["Benzina", "Gasolio"]:
        sub = d.filter(pl.col("fuel") == fuel)
        fig.add_trace(
            go.Scatter(
                x=sub["date"], y=sub["share"] * 100, mode="lines+markers",
                name=names[fuel],
                line=dict(color=colors[fuel], width=LINE_W), marker=dict(size=9),
            )
        )
    # cap / cap-change vlines, no in-panel text labels
    fig.add_vline(x=CAP_DATE.isoformat(), line_dash="dash", line_color="black")
    fig.add_vline(x=EXCISE_STEP.isoformat(), line_dash="dash", line_color="black")
    fig.update_xaxes(
        tickformat="%d %b", tickangle=0, dtick=xdtick_days * 86400000,
        tickfont=dict(size=font),
        range=[FIG3_CUT, d["date"].max() + dt.timedelta(days=1)],
    )
    fig.update_yaxes(
        ticksuffix="%", tickfont=dict(size=font), range=[-2, 80],
        title=dict(text="Cap adoption rate", font=dict(size=font)),
    )
    fig.update_layout(
        font=dict(size=font), margin=dict(l=10, r=30, t=15, b=10),
        template="plotly_white", width=size[0], height=size[1],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
    )
    out = FIG / f"{stem}.png"
    fig.write_image(out, scale=2)
    return out




BRAND_ORDER = ("Eni", "Api-Ip", "Q8", "Esso", "Tamoil", "Shell", "Pompe Bianche")
BRAND_COLORS = {
    "Eni": "#D62728", "Api-Ip": "#FF7F0E", "Q8": "#9467BD",
    "Esso": "#1F77B4", "Tamoil": "#8C564B", "Shell": "#00BCD4",
    "Pompe Bianche": "#7F7F7F",
}
BRAND_EN = {"Pompe Bianche": "Independent"}


def brand_price_chart(fuel: str, show_excise_vline: bool, stem: str) -> Path:
    """Numbered variant of the brand chart: from 1 Sep, aggregate line added,
    Pompe Bianche renamed Independent, style of figs 1/2 (no title, FONT,
    thick lines, 3-day ticks, tight y range incl. cap lines)."""
    daily = pl.read_csv(config.TABLES_DIR / "brand_daily_prices.csv",
                        try_parse_dates=True)
    # data value is 'Agip Eni'; display/rebrand as 'Eni'
    daily = daily.with_columns(
        pl.when(pl.col("canonical_name") == "Agip Eni")
        .then(pl.lit("Eni"))
        .otherwise(pl.col("canonical_name"))
        .alias("canonical_name")
    )
    d = daily.filter(pl.col("fuel") == fuel).filter(pl.col("date") >= CUT)

    fig = go.Figure()
    agg = d.group_by("date").agg(p=pl.col("mean_price").mean()).sort("date")
    fig.add_trace(
        go.Scatter(x=agg["date"], y=agg["p"], mode="lines", name=AGG_EN,
                   line=dict(color=AGG_COLOR, width=LINE_W + 1, dash="dot"))
    )
    for brand in BRAND_ORDER:
        s = d.filter(pl.col("canonical_name") == brand).sort("date")
        if not s.height:
            continue
        fig.add_trace(
            go.Scatter(x=s["date"], y=s["mean_price"], mode="lines",
                       name=BRAND_EN.get(brand, brand),
                       line=dict(color=BRAND_COLORS[brand], width=LINE_W))
        )

    threshold = config.THRESHOLDS[fuel]
    caps = [threshold]
    fig.add_hline(
        y=threshold, line_dash="dot", line_color="firebrick",
        annotation_text=f"cap {threshold:.2f} EUR/l from 28 Sep",
        annotation_position="top left",
        annotation_font=dict(size=FONT, color="firebrick"),
    )
    if fuel == "Gasolio":
        fig.add_hline(
            y=config.GASOLIO_CAP_AFTER, line_dash="dot", line_color="firebrick",
            annotation_text=f"cap {config.GASOLIO_CAP_AFTER:.3f} EUR/l from 6 Oct",
            annotation_position="top left",
            annotation_font=dict(size=FONT, color="firebrick"),
        )
        caps.append(config.GASOLIO_CAP_AFTER)
    fig.add_vline(x=CAP_DATE.isoformat(), line_dash="dash", line_color="black")
    if show_excise_vline:
        fig.add_vline(x=EXCISE_STEP.isoformat(), line_dash="dash", line_color="black")

    y_min = min(d["mean_price"].min(), *caps)
    y_max = max(d["mean_price"].max(), *caps)
    pad = (y_max - y_min) * 0.06
    pad_hi = (y_max - y_min) * 0.12
    pad_lo = pad * 2.5
    fig.update_layout(
        font=dict(size=FONT),
        margin=dict(l=10, r=30, t=15, b=10),
        template="plotly_white",
        hovermode="x unified",
        width=1400,
        height=620,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
    )
    fig.update_xaxes(
        tickformat="%d %b", tickangle=0, dtick=3 * 86400000,
        range=[CUT, d["date"].max() + dt.timedelta(days=1)],
    )
    fig.update_yaxes(
        tickformat=".2f", range=[y_min - pad_lo, y_max + pad_hi],
        title=dict(text="EUR/l", font=dict(size=FONT)),
    )
    out = FIG / f"{stem}.png"
    fig.write_image(out, scale=2)
    return out



def copy_fig(src_name: str, stem: str) -> Path:
    out = FIG / f"{stem}.png"
    shutil.copyfile(ADOPT_FIG / src_name, out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Numbered English report figures.")
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="only regenerate the square-format figures 10-12",
    )
    args = parser.parse_args()

    outs = []
    if not args.new_only:
        outs += [
            group_price_chart_en("Benzina", show_excise_line=False,
                                 stem="1_benzina_mean_price_brands"),
            group_price_chart_en("Gasolio", show_excise_line=True,
                                 stem="2_gasolio_mean_price_brands"),
            fig3_adoption_share(),
            brand_price_chart("Benzina", show_excise_vline=False,
                              stem="8_benzina_mean_price_bandiera"),
            brand_price_chart("Gasolio", show_excise_vline=True,
                              stem="9_gasolio_mean_price_bandiera"),
            copy_fig("map_adoption_share.png", "4_map_adoption_share"),
            copy_fig("map_pb_adoption_share.png", "5_map_pb_adoption_share"),
            copy_fig("amap_price_post7_ben.png", "6_map_price_oct5_petrol"),
            copy_fig("amap_price_post7_gas.png", "7_map_price_oct5_diesel"),
        ]
    # square variants of figures 1-3: weekly ticks (fig 12: every 4 days),
    # +50% fonts, data window follows the caches
    outs += [
        group_price_chart_en("Benzina", show_excise_line=False,
                             stem="10_benzina_mean_price_brands",
                             size=SQ_SIZE, font=FONT_SQ, xdtick_days=7),
        group_price_chart_en("Gasolio", show_excise_line=True,
                             stem="11_gasolio_mean_price_brands",
                             size=SQ_SIZE, font=FONT_SQ, xdtick_days=7,
                             cap_labels="wrapped"),
        fig3_adoption_share(stem="12_adoption_share_daily",
                            size=SQ_SIZE, font=FONT_SQ, xdtick_days=4),
    ]
    for p in outs:
        print(f"saved {p}")


if __name__ == "__main__":
    main()
