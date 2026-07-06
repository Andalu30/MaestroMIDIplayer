from pathlib import Path
import urllib.request
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


def test_downloads_and_extracts_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    dataset_dir = tmp_path / "dataset"
    zip_path = tmp_path / "maestro.zip"
    _make_zip(zip_path)

    def _fake_urlopen(url: str, timeout: int):
        assert url == "https://example.test/maestro.zip"
        assert timeout > 0
        return zip_path.open("rb")

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    result = ensure_dataset_available(
        dataset_dir,
        dataset_url="https://example.test/maestro.zip",
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


def test_rejects_non_https_dataset_url(tmp_path: Path):
    dataset_dir = tmp_path / "dataset"

    with pytest.raises(ValueError):
        ensure_dataset_available(
            dataset_dir,
            dataset_url="http://example.test/maestro.zip",
            auto_download=True,
        )
