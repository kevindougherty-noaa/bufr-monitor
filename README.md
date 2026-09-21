# BUFR Monitor

Hourly pipeline: download realtime CrIS BUFR dumps from NOMADS, read them
into xarray via `bufr-query`, plot timeseries/coverage diagnostics with
EMCPy, deploy to GitHub Pages. Scoped as a proof of concept for extending
`obs-monitor`-style monitoring to new datasets.
