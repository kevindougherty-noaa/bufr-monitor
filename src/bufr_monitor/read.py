"""Read a CrIS BUFR dump into per-satellite xarray Datasets.

Uses bufr-query's high-level API (bufr.Parser + netcdf.Encoder) driven by
the vendored NOAA-EMC/spoc mapping YAML, rather than hand-built QuerySet
queries. The SPOC YAML already encodes the satId split (NPP/N20/N21) and
the Channel dimension for spectral radiance, so re-deriving that logic in
Python here would just be a second, more fragile copy of the same schema.

Only the ``bufr`` import (compiled bufr-query package) is required at call
time -- it is imported lazily so this module can be imported (e.g. for
type checking or unit tests of the surrounding pipeline) on machines
without the compiled library installed.
"""
from __future__ import annotations

import logging
from pathlib import Path

import xarray as xr

logger = logging.getLogger(__name__)

# Satellite ID -> human-readable name, per the SPOC splits/satId mapping
# (*/SAID: 224=NPP, 225=NOAA-20, 226=NOAA-21) and subset NC021206.
SATELLITE_NAMES = {
    "npp": "NPP",
    "n20": "NOAA-20",
    "n21": "NOAA-21",
}


class BufrReadError(RuntimeError):
    """Raised when a BUFR file fails to parse or encode."""


def read_cris_bufr(
    bufr_path: Path,
    mapping_yaml: Path,
    output_dir: Path,
) -> dict[str, xr.Dataset]:
    """Parse a CrIS BUFR file and return one xarray Dataset per satellite.

    Args:
        bufr_path: Path to the raw ``*.bufr_d`` dump file.
        mapping_yaml: Path to the bufr-query mapping YAML (vendored copy
            of NOAA-EMC/spoc's radiance_cris-fsr.yaml).
        output_dir: Directory where intermediate per-satellite NetCDF
            files are written. Created if missing.

    Returns:
        Dict mapping satellite short name (e.g. "npp") to an xr.Dataset
        with MetaData and ObsValue variables merged, including the
        Channel-dimensioned spectralRadiance variable.

    Raises:
        BufrReadError: If parsing, encoding, or the xarray load fails.
    """
    try:
        import bufr
        from bufr.encoders import netcdf
    except ImportError as exc:
        raise BufrReadError(
            "bufr-query is not importable in this environment. It must be "
            "built/installed (see NOAA-EMC/bufr-query quick start) -- this "
            "is expected to run inside the devcontainer / on ursa, not in "
            "a generic Python env."
        ) from exc

    if not bufr_path.exists():
        raise BufrReadError(f"BUFR file not found: {bufr_path}")
    if not mapping_yaml.exists():
        raise BufrReadError(f"Mapping YAML not found: {mapping_yaml}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "cris_{splits/satId}.nc")

    logger.info("Parsing %s with mapping %s", bufr_path, mapping_yaml)
    try:
        container = bufr.Parser(str(bufr_path), str(mapping_yaml)).parse()
        encoded = netcdf.Encoder(str(mapping_yaml)).encode(
            container, output_template
        )
    except Exception as exc:  # noqa: BLE001 - bufr-query raises plain RuntimeError
        raise BufrReadError(
            f"bufr-query failed to parse/encode {bufr_path}: {exc}"
        ) from exc

    if not encoded:
        raise BufrReadError(
            f"No categories encoded from {bufr_path} -- check that the "
            "file actually contains NC021206 subsets for this cycle."
        )

    datasets: dict[str, xr.Dataset] = {}
    for category, _obs_group in encoded.items():
        sat_key = category[0] if isinstance(category, tuple) else str(category)
        nc_path = Path(output_dir / f"cris_{sat_key}.nc")
        if not nc_path.exists():
            logger.warning("Expected output %s not found, skipping", nc_path)
            continue
        datasets[sat_key] = _load_dataset(nc_path)

    if not datasets:
        raise BufrReadError(f"Encoding produced no readable output files for {bufr_path}")

    return datasets


def _load_dataset(nc_path: Path) -> xr.Dataset:
    """Merge the MetaData and ObsValue groups of an ioda-style NetCDF file."""
    try:
        meta = xr.open_dataset(nc_path, group="MetaData")
        obs = xr.open_dataset(nc_path, group="ObsValue")
    except Exception as exc:  # noqa: BLE001
        raise BufrReadError(f"Failed to open groups in {nc_path}: {exc}") from exc

    ds = xr.merge([meta, obs], combine_attrs="override")
    ds.attrs["source_file"] = nc_path.name
    return ds
