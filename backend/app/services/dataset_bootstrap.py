"""Ensure the MAESTRO dataset exists locally, downloading it when needed."""

from __future__ import annotations

import logging
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

logger = logging.getLogger("maestro.dataset_bootstrap")

MAESTRO_MIDI_ZIP_URL = (
    "https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0-midi.zip"
)
DATASET_CSV_FILENAME = "maestro-v3.0.0.csv"


def _is_within_directory(base: Path, candidate: Path) -> bool:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    return candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents


def _safe_extract(zip_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            destination = target_dir / member
            if not _is_within_directory(target_dir, destination):
                raise RuntimeError(f"Unsafe ZIP entry blocked: {member}")
        archive.extractall(target_dir)


def ensure_dataset_available(
    dataset_path: Path,
    *,
    dataset_url: str = MAESTRO_MIDI_ZIP_URL,
    auto_download: bool = True,
) -> Path:
    """Return the CSV path, downloading/extracting the dataset if needed."""
    csv_path = dataset_path / DATASET_CSV_FILENAME
    if csv_path.is_file():
        return csv_path

    if not auto_download:
        raise FileNotFoundError(f"Dataset CSV not found at {csv_path}")

    logger.warning("Dataset missing at %s; downloading from %s", dataset_path, dataset_url)
    dataset_path.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        zip_tmp_path = Path(tmp.name)

    try:
        with urllib.request.urlopen(dataset_url, timeout=120) as response, zip_tmp_path.open(
            "wb"
        ) as out_file:
            shutil.copyfileobj(response, out_file)

        _safe_extract(zip_tmp_path, dataset_path)
    finally:
        zip_tmp_path.unlink(missing_ok=True)

    if not csv_path.is_file():
        raise RuntimeError(f"Dataset download completed but CSV is missing: {csv_path}")

    logger.info("Dataset ready at %s", dataset_path)
    return csv_path
