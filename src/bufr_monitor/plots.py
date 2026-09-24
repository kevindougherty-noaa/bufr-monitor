"""
src/cris_monitor/plots.py

EMCPy diagnostic plots for the CrIS BUFR monitoring POC.

Mirrors the CreatePlot/CreateFigure composition pattern used in every
EMCPy gallery example: build one or more plot "layer" objects (e.g.
LinePlot, MapScatter), attach them to a CreatePlot via
`plot1.plot_layers = [...]`, add labels/features, then hand a list of
CreatePlot objects to CreateFigure.

Two entry points:
    coverage_map(...)          -- one cycle, lat/lon scatter per satellite
    obs_counts_timeseries(...) -- many cycles, obs count per satellite

Two things below are NOT confirmed against your local emcpy install
and are flagged inline -- please check before relying on them:
  1. The `domain` string for a global (non-CONUS) map extent. The
     gallery only demonstrates domain='conus'. If 'global' isn't a
     valid Domain value, check emcpy.plots.map_tools.Domain directly.
  2. Whether CreateFigure() accepts a figsize kwarg. Not shown in any
     gallery example -- left out below; matplotlib's default figure
     size will apply unless you confirm otherwise.
Everything else (plot_layers, add_title/add_xlabel/add_ylabel,
add_legend, add_map_features, add_stats_dict, MapScatter/LinePlot
attributes) matches the emcpy.github.io gallery examples directly.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from emcpy.plots.create_plots import CreatePlot, CreateFigure
from emcpy.plots.map_plots import MapScatter
from emcpy.plots.plots import LinePlot

# Keep satellite -> color consistent across every plot in the POC so a
# given satellite always reads the same way in coverage maps and
# timeseries alike.
SATELLITE_COLORS = {
    "npp": "tab:blue",
    "n20": "tab:orange",
    "n21": "tab:green",
}

SATELLITE_LABELS = {
    "npp": "Suomi-NPP",
    "n20": "NOAA-20",
    "n21": "NOAA-21",
}


def coverage_map(
    datasets: dict[str, xr.Dataset],
    cycle: str,
    output_path: str | Path,
    domain: str = "global",
    labels: dict[str, str] | None = None,
) -> Path:
    """Plot a lat/lon coverage map, one MapScatter layer per satellite.

    Parameters
    ----------
    datasets : dict[str, xr.Dataset]
        Output of read.py -- keyed by satellite (npp/n20/n21), each a
        merged MetaData+ObsValue Dataset with `latitude`/`longitude`.
    cycle : str
        Cycle label for the title, e.g. "2026091712".
    output_path : str | Path
        Where to save the PNG.
    domain : str
        emcpy map_tools Domain string -- see the module docstring
        TODO about confirming 'global' is valid.
    labels : dict[str, str] | None
        Satellite key -> display name, e.g. read.py's SATELLITE_NAMES.
        Falls back to this module's SATELLITE_LABELS if not given.
    """
    output_path = Path(output_path)
    labels = labels or SATELLITE_LABELS

    layers = []
    total_obs = 0
    for sat, ds in datasets.items():
        lats = np.asarray(ds["latitude"].values).ravel()
        lons = np.asarray(ds["longitude"].values).ravel()
        if lats.size == 0:
            continue  # skip satellites with no obs this cycle

        scatter = MapScatter(lats, lons)
        scatter.color = SATELLITE_COLORS.get(sat, "tab:gray")
        scatter.markersize = 2
        scatter.label = labels.get(sat, sat)
        layers.append(scatter)
        total_obs += lats.size

    plot1 = CreatePlot()
    plot1.plot_layers = layers
    plot1.projection = "plcarr"
    plot1.domain = domain
    plot1.add_map_features(["coastline"])
    plot1.add_xlabel(xlabel="longitude")
    plot1.add_ylabel(ylabel="latitude")
    plot1.add_title(label=f"CrIS Coverage\n{cycle}", loc="center", fontsize=12)
    plot1.add_legend(loc="lower left")
    plot1.add_stats_dict(stats_dict={"nobs": total_obs}, yloc=-0.25)

    fig = CreateFigure()
    fig.plot_list = [plot1]
    fig.create_figure()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close("all")

    return output_path


def obs_counts_timeseries(
    counts_by_cycle: dict[str, dict[str, int]],
    output_path: str | Path,
    labels: dict[str, str] | None = None,
) -> Path:
    """Plot obs counts by satellite across a series of cycles.

    Parameters
    ----------
    counts_by_cycle : dict[str, dict[str, int]]
        {cycle_label: {satellite: count}}, cycle_label as "%Y%m%d%H",
        e.g. {"2026091700": {"npp": 812345, "n20": 790102}, ...}.
        Pass an already time-sorted dict (or build it from a sorted
        cycle list) -- insertion order drives the x-axis.
    output_path : str | Path
        Where to save the PNG.
    labels : dict[str, str] | None
        Satellite key -> display name, e.g. read.py's SATELLITE_NAMES.
        Falls back to this module's SATELLITE_LABELS if not given.
    """
    output_path = Path(output_path)
    labels = labels or SATELLITE_LABELS

    cycles = list(counts_by_cycle.keys())
    # Real datetimes rather than bare integer positions, so matplotlib's
    # date formatting/rotation applies automatically -- avoids relying
    # on an unconfirmed tick-label API on CreatePlot.
    x = pd.to_datetime(cycles, format="%Y%m%d%H")

    satellites = sorted({sat for counts in counts_by_cycle.values() for sat in counts})

    layers = []
    for sat in satellites:
        y = [counts_by_cycle[cycle].get(sat, np.nan) for cycle in cycles]

        lp = LinePlot(x, y)
        lp.color = SATELLITE_COLORS.get(sat, "tab:gray")
        lp.label = labels.get(sat, sat)
        lp.marker = "o"
        layers.append(lp)

    plot1 = CreatePlot()
    plot1.plot_layers = layers
    plot1.add_title("CrIS Obs Counts by Satellite", loc="center", fontsize=16)
    plot1.add_xlabel("Cycle")
    plot1.add_ylabel("Obs Count")
    plot1.add_legend(loc="upper right")

    fig = CreateFigure()
    fig.plot_list = [plot1]
    fig.create_figure()
    plt.gcf().autofmt_xdate()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close("all")

    return output_path
