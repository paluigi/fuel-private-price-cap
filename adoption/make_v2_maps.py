"""Restyled province map pair for the appendix (one pair, v2 style).

Share of station-fuel units priced below the ceiling at least once in the
first seven days of the cap (28 Sep - 4 Oct), by province, petrol and
diesel on a common 0-100% scale. Replaces the blue-red amap_* pair in the
paper (those files remain on disk for the audit trail).

Run from adoption/: uv run python make_v2_maps.py
Outputs: output/figures/v2_map_adopt7_ben.png, v2_map_adopt7_gas.png
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import polars as pl
import plotly.graph_objects as go
import shapefile
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

FIG = config.OUT_DIR / "figures"
BORDERS = (config.DATA_DIR / "istat_borders" / "ProvCM01012026_g"
           / "ProvCM01012026_g_WGS84.shp")
WINDOW_TO = config.CAP_DATE + dt.timedelta(days=6)  # first 7 days

# ISTAT 2026 province layer is UTM32N (EPSG:32632) despite the _WGS84 name
sf = shapefile.Reader(BORDERS)
_to_wgs84 = Transformer.from_crs("EPSG:32632", "EPSG:4326", always_xy=True)
fields = [f[0] for f in sf.fields[1:]]
geojson = {"type": "FeatureCollection", "features": []}
name2id = {}
for sr in sf.shapeRecords():
    rec = dict(zip(fields, sr.record))
    join_name = rec.get("SIGLA") or rec.get("DEN_PROV") or ""
    fid = str(rec.get("COD_UTS"))
    name2id[join_name] = fid
    parts = list(sr.shape.parts) + [len(sr.shape.points)]
    feats = []
    for i in range(len(parts) - 1):
        pts = sr.shape.points[parts[i]:parts[i + 1]]
        if len(pts) >= 3:
            ring = [[x, y] for x, y in
                    (_to_wgs84.transform(x, y) for x, y in pts)]
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            feats.append([ring])
    geojson["features"].append({
        "type": "Feature", "id": fid,
        "properties": {"sigla": join_name},
        "geometry": {"type": "MultiPolygon", "coordinates": feats},
    })

# light -> dark blue sequential scale (colour-blind safe)
SEQ_BLUES = [
    [0.00, "#deebf7"],
    [0.25, "#9ecae1"],
    [0.50, "#4292c6"],
    [0.75, "#08519c"],
    [1.00, "#08306b"],
]


def rates() -> pl.DataFrame:
    p = pl.scan_parquet(config.ADOPTION_PANEL).filter(
        pl.col("date").is_between(config.CAP_DATE, WINDOW_TO)
    )
    return (
        p.group_by("provincia_istat", "fuel")
        .agg(share=pl.col("at_cap").mean(), n=pl.len())
        .with_columns(pct=100 * pl.col("share"))
        .with_columns(fid=pl.col("provincia_istat").cast(pl.String)
                      .replace_strict(name2id, default=None))
        .filter(pl.col("fid").is_not_null())
        .collect()
        .sort("provincia_istat")
    )


def panel(df: pl.DataFrame, fname: str, title: str) -> None:
    fig = go.Figure(go.Choroplethmap(
        geojson=geojson, locations=df["fid"], z=df["pct"],
        featureidkey="id", colorscale=SEQ_BLUES, zmin=0, zmax=100,
        marker_line_width=0.4, marker_line_color="white",
        hovertemplate="%{z:.0f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="share below ceiling (%)", side="top",
                       font=dict(size=16)),
            orientation="h", thickness=12, len=0.55,
            x=0.5, xanchor="center", y=-0.01, yanchor="top",
            tickfont=dict(size=16), ticklen=4, outlinewidth=0,
        ),
    ))
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Helvetica, Arial, sans-serif", size=16),
        title=dict(text=title, x=0.5, font=dict(size=20)),
        margin=dict(l=0, r=0, t=36, b=86),
        # tight Italy frame: keeps Sicily and Sardinia; outer minor
        # islands (Pelagie) fall outside the bounds (D12). Canvas aspect
        # must exceed the bbox aspect (h/w ~1.22 at Italy's latitude) or
        # the map overflows and clips the Alpine border.
        width=880, height=1250,
        map=dict(
            style="white-bg",
            bounds=dict(west=6.6, east=18.7, south=36.3, north=47.2),
        ),
    )
    fig.write_image(FIG / fname, scale=2)
    rng = f"{df['pct'].min():.0f}-{df['pct'].max():.0f}"
    print(f"saved {fname} | province range {rng}%")


if __name__ == "__main__":
    r = rates()
    print("provinces matched:", r["provincia_istat"].n_unique())
    for fuel, fname, title in (
        ("Benzina", "v2_map_adopt7_ben.png", "Petrol"),
        ("Gasolio", "v2_map_adopt7_gas.png", "Diesel"),
    ):
        panel(r.filter(pl.col("fuel") == fuel), fname, title)
