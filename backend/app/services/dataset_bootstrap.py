"""Ensure the MAESTRO dataset exists locally, downloading it when needed."""

from __future__ import annotations

import logging
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

logger = logging.getLogger("maestro.dataset_bootstrap")

DATASET_CSV_FILENAME = "maestro-v3.0.0.csv"


def _is_within_directory(base: Path, candidate: Path) -> bool:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    return candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents


def _safe_extract(zip_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            destination = target_dir / member.filename
            if not _is_within_directory(target_dir, destination):
                raise RuntimeError(f"Unsafe ZIP entry blocked: {member.filename}")
            archive.extract(member, target_dir)


def ensure_dataset_available(
    dataset_path: Path,
    *,
    dataset_url: str,
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

    with tempfile.TemporaryDirectory(prefix="maestro-dataset-") as temp_dir:
        zip_tmp_path = Path(temp_dir) / "maestro.zip"
        try:
            with urllib.request.urlopen(dataset_url, timeout=120) as response, zip_tmp_path.open(
                "wb"
            ) as out_file:
                downloaded = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                logger.info("Downloaded dataset archive (%d bytes)", downloaded)
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to download dataset archive from {dataset_url}: {e}") from e

        _safe_extract(zip_tmp_path, dataset_path)

    if not csv_path.is_file():
        raise RuntimeError(f"Dataset download completed but CSV is missing: {csv_path}")

    logger.info("Dataset ready at %s", dataset_path)
    return csv_path
