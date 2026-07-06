"""Ensure the MAESTRO dataset exists locally, downloading it when needed."""

from __future__ import annotations

import logging
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

logger = logging.getLogger("maestro.dataset_bootstrap")

DATASET_CSV_FILENAME = "maestro-v3.0.0.csv"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
PROGRESS_LOG_INTERVAL_BYTES = 100 * 1024 * 1024
DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 1800
BYTES_PER_MEGABYTE = 1024 * 1024


def _is_within_directory(base: Path, candidate: Path) -> bool:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    return candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents


def _safe_extract(zip_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_path = PurePosixPath(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RuntimeError(f"Unsafe ZIP entry blocked: {member.filename}")
            mode = stat.S_IFMT(member.external_attr >> 16)
            if mode == stat.S_IFLNK:
                raise RuntimeError(f"Symlink ZIP entry blocked: {member.filename}")
            destination = target_dir / member.filename
            if not _is_within_directory(target_dir, destination):
                raise RuntimeError(f"Unsafe ZIP entry blocked: {member.filename}")
            archive.extract(member, target_dir)


def _validate_dataset_url(dataset_url: str) -> None:
    parsed = urllib.parse.urlparse(dataset_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Dataset URL must be an absolute HTTPS URL")


def ensure_dataset_available(
    dataset_path: Path,
    *,
    dataset_url: str,
    download_timeout_seconds: int = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    auto_download: bool = True,
) -> Path:
    """Return the CSV path, downloading/extracting the dataset if needed."""
    csv_path = dataset_path / DATASET_CSV_FILENAME
    if csv_path.is_file():
        return csv_path

    if not auto_download:
        raise FileNotFoundError(f"Dataset CSV not found at {csv_path}")

    _validate_dataset_url(dataset_url)
    logger.info("Dataset CSV missing at %s; downloading from %s", csv_path, dataset_url)
    dataset_path.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="maestro-dataset-") as temp_dir:
        zip_tmp_path = Path(temp_dir) / "maestro.zip"
        try:
            with urllib.request.urlopen(
                dataset_url, timeout=download_timeout_seconds
            ) as response, zip_tmp_path.open("wb") as out_file:
                downloaded = 0
                next_progress_bytes = PROGRESS_LOG_INTERVAL_BYTES
                while True:
                    chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if downloaded >= next_progress_bytes:
                        logger.info(
                            "Downloaded %.1f MB of dataset archive",
                            downloaded / BYTES_PER_MEGABYTE,
                        )
                        next_progress_bytes += PROGRESS_LOG_INTERVAL_BYTES
                logger.info("Downloaded dataset archive (%d bytes)", downloaded)
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Failed to download dataset archive from {dataset_url}: {str(e)}"
            ) from e

        logger.info("Extracting dataset archive into %s", dataset_path)
        _safe_extract(zip_tmp_path, dataset_path)
        logger.info("Dataset archive extraction complete")

    if not csv_path.is_file():
        raise RuntimeError(f"Dataset download completed but CSV is missing: {csv_path}")

    logger.info("Dataset ready at %s", dataset_path)
    return csv_path
