"""
scripts/run_cycle.py

CI entry point: download the most recent available CrIS BUFR cycle,
process it, and write a coverage map into site/figures/.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from bufr_monitor.download import download_cris_bufr
from bufr_monitor.read import read_cris_bufr, SATELLITE_NAMES
from bufr_monitor.plots import coverage_map

REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPING_YAML = REPO_ROOT / "config" / "radiance_cris-fsr_coverage.yaml"
DATA_DIR = REPO_ROOT / "data"
SITE_FIGURES_DIR = REPO_ROOT / "site" / "figures"

# GDAS/CrIS cycles run 00/06/12/18Z. Obsproc dumps aren't available
# immediately -- LATENCY_HOURS is a buffer before assuming a cycle's
# data has landed on NOMADS. 4 hours is a starting guess; tighten or
# loosen it based on how often this actually finds data vs. 404s once
# this is running regularly.
LATENCY_HOURS = 7
CYCLE_STRIDE_HOURS = 6


def most_recent_available_cycle(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    candidate = now - timedelta(hours=LATENCY_HOURS)
    floored_hour = (candidate.hour // CYCLE_STRIDE_HOURS) * CYCLE_STRIDE_HOURS
    return candidate.replace(hour=floored_hour, minute=0, second=0, microsecond=0)


def main() -> None:
    cycle = most_recent_available_cycle()
    cycle_label = cycle.strftime("%Y%m%d%H")
    print(f"Running cycle {cycle_label}")

    SITE_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    bufr_path = download_cris_bufr(cycle, DATA_DIR / "raw")
    nc_dir = DATA_DIR / "processed" / cycle_label
    datasets = read_cris_bufr(bufr_path, MAPPING_YAML, nc_dir)

    coverage_map(
        datasets,
        cycle=cycle_label,
        output_path=SITE_FIGURES_DIR / f"cris_coverage_{cycle_label}.png",
        labels=SATELLITE_NAMES,
    )
    print("Coverage map written.")


if __name__ == "__main__":
    main()
