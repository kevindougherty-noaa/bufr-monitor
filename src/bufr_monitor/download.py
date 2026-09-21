"""Download realtime CrIS BUFR dump files from NOMADS.

Kept deliberately small and dependency-light (stdlib + requests only) since
this runs as the first step of an hourly GitHub Actions job.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

NOMADS_BASE_URL = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/obsproc/prod"


class BufrDownloadError(RuntimeError):
    """Raised when a BUFR dump file cannot be retrieved from NOMADS."""


def build_cris_url(cycle: datetime) -> str:
    """Build the NOMADS URL for a given GDAS cycle.

    Args:
        cycle: The GDAS cycle time. Only the date and hour are used;
            NOMADS publishes dumps at 00/06/12/18Z.

    Returns:
        Full URL to the crisf4 BUFR dump for that cycle.
    """
    date_str = cycle.strftime("%Y%m%d")
    hour_str = cycle.strftime("%H")
    return (
        f"{NOMADS_BASE_URL}/gdas.{date_str}/"
        f"gdas.t{hour_str}z.crisf4.tm00.bufr_d"
    )


def download_cris_bufr(
    cycle: datetime,
    output_dir: Path,
    *,
    timeout_s: int = 60,
    chunk_size: int = 1024 * 1024,
) -> Path:
    """Download a single CrIS BUFR dump file for the given cycle.

    Args:
        cycle: GDAS cycle time (date + hour).
        output_dir: Directory to write the file into. Created if missing.
        timeout_s: Per-request timeout in seconds.
        chunk_size: Streaming download chunk size in bytes.

    Returns:
        Path to the downloaded file on disk.

    Raises:
        BufrDownloadError: If the request fails, returns a non-200 status,
            or the resulting file is empty.
    """
    url = build_cris_url(cycle)
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / Path(url).name

    logger.info("Downloading CrIS BUFR dump: %s", url)
    try:
        with requests.get(url, stream=True, timeout=timeout_s) as resp:
            if resp.status_code != 200:
                raise BufrDownloadError(
                    f"NOMADS returned status {resp.status_code} for {url}"
                )
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    fh.write(chunk)
    except requests.RequestException as exc:
        raise BufrDownloadError(f"Failed to download {url}: {exc}") from exc

    if dest.stat().st_size == 0:
        dest.unlink(missing_ok=True)
        raise BufrDownloadError(f"Downloaded file for {url} is empty")

    logger.info("Saved %s (%d bytes)", dest, dest.stat().st_size)
    return dest
