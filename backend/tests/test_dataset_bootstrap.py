from pathlib import Path
import zipfile

import pytest

from app.services.dataset_bootstrap import (
    DATASET_CSV_FILENAME,
    ensure_dataset_available,
)


def _make_zip(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(
            DATASET_CSV_FILENAME,
            "canonical_composer,canonical_title,split,year,midi_filename,audio_filename,duration\n",
        )
        zf.writestr("sample.midi", "dummy")


def test_returns_existing_csv(tmp_path: Path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    csv_path = dataset_dir / DATASET_CSV_FILENAME
    csv_path.write_text("header\n", encoding="utf-8")

    result = ensure_dataset_available(
        dataset_dir, dataset_url="https://example.test/unused.zip", auto_download=True
    )

    assert result == csv_path


def test_downloads_and_extracts_when_missing(tmp_path: Path):
    dataset_dir = tmp_path / "dataset"
    zip_path = tmp_path / "maestro.zip"
    _make_zip(zip_path)

    result = ensure_dataset_available(
        dataset_dir,
        dataset_url=zip_path.as_uri(),
        auto_download=True,
    )

    assert result == dataset_dir / DATASET_CSV_FILENAME
    assert result.is_file()
    assert (dataset_dir / "sample.midi").is_file()


def test_raises_if_auto_download_disabled(tmp_path: Path):
    dataset_dir = tmp_path / "dataset"

    with pytest.raises(FileNotFoundError):
        ensure_dataset_available(
            dataset_dir, dataset_url="https://example.test/unused.zip", auto_download=False
        )
