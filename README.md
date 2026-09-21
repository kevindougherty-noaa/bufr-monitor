# CrIS BUFR Monitor (proof of concept)

Hourly pipeline: download realtime CrIS BUFR dumps from NOMADS, read them
into xarray via `bufr-query`, plot timeseries/coverage diagnostics with
EMCPy, deploy to GitHub Pages. Scoped as a proof of concept for extending
`obs-monitor`-style monitoring to new datasets.

## Pipeline stages

1. **Download** (`cris_monitor.download`) — pull `gdas.tHHz.crisf4.tm00.bufr_d`
   from NOMADS for a given cycle.
2. **Read / process** (`cris_monitor.read`) — parse the BUFR file with
   `bufr.Parser` + `netcdf.Encoder`, driven by the vendored
   [NOAA-EMC/spoc mapping YAML](config/radiance_cris-fsr.yaml), then load
   the resulting per-satellite NetCDF files as merged `xr.Dataset`s
   (`MetaData` + `ObsValue` groups). Handles the NPP/NOAA-20/NOAA-21
   split and the Channel-dimensioned spectral radiance for free, since
   that's already encoded in the SPOC config.
3. **Plot** (not yet implemented) — EMCPy timeseries (obs counts by
   satellite/hour) and coverage maps (lat/lon scatter).
4. **Deploy** (not yet implemented) — publish figures to GitHub Pages.
5. **Anomaly detection** (deferred) — hook point for the SPC-style
   alerting work once 1-4 are proven out.

## Status

Steps 1-2 implemented below. Not yet run against real data in this
session -- `bufr-query` is a compiled package (NCEPLIB-bufr, eckit, etc.)
that isn't available in this sandbox. Next action: run
`scripts/validate_step1.py` in the devcontainer on `ursa` against a real
cycle and sanity-check the resulting Datasets before touching plotting.

```
config/
  radiance_cris-fsr.yaml   # vendored as-is from NOAA-EMC/spoc (develop)
src/cris_monitor/
  download.py              # NOMADS -> local *.bufr_d
  read.py                  # *.bufr_d -> dict[str, xr.Dataset] per satellite
scripts/
  validate_step1.py        # manual real-data sanity check
```

## Why the mapping YAML is vendored, not re-derived

`bufr.Parser` + `netcdf.Encoder` take the mapping YAML at call time, so
the file needs to live in this repo rather than being fetched from SPOC
at runtime. It's a straight copy of
`NOAA-EMC/spoc:dump/config/atmosphere/radiance_cris-fsr.yaml` (develop
branch) -- if the upstream schema changes, re-pull it manually rather
than patching this copy by hand, to avoid drift between the two.

## Open questions for the next steps

- EMCPy plotting: which routines/figure types to reuse from `obs_monitor`
  (LineScatter for timeseries counts, MapScatter for coverage) --
  confirm exact API against the current EMCPy version before writing.
- GitHub Actions: hourly cron, cache/skip-if-already-processed logic for
  a given cycle, and where processed NetCDF intermediates should live
  (artifact vs. discarded after plotting).
- GitHub Pages deploy target: dedicated `gh-pages` branch vs.
  `actions/deploy-pages`.
