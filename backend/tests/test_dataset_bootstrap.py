import io
from pathlib import Path
import urllib.request
import zipfile

import pytest

from app.services.dataset_bootstrap import (
    DATASET_CSV_FILENAME,
    DATASET_JSON_FILENAME,
    DATASET_METADATA_BASE_URL,
    ensure_dataset_available,
)

CSV_CONTENT = b"canonical_composer,canonical_title,split,year,midi_filename,audio_filename,duration\n"
JSON_CONTENT = b'{"metadata": []}'


def _make_zip(zip_path: Path) -> None:
    """Create a ZIP that only contains MIDI files (no CSV/JSON, matching real dataset)."""
    with zipfile.ZipFile(zip_path, "w") as zf:
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

    csv_url = DATASET_METADATA_BASE_URL + DATASET_CSV_FILENAME
    json_url = DATASET_METADATA_BASE_URL + DATASET_JSON_FILENAME

    responses = {
        "https://example.test/maestro.zip": zip_path.read_bytes(),
        csv_url: CSV_CONTENT,
        json_url: JSON_CONTENT,
    }

    def _fake_urlopen(url: str, timeout: int):
        assert timeout > 0
        assert url in responses, f"Unexpected URL: {url}"
        return io.BytesIO(responses[url])

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    result = ensure_dataset_available(
        dataset_dir,
        dataset_url="https://example.test/maestro.zip",
        auto_download=True,
    )

    assert result == dataset_dir / DATASET_CSV_FILENAME
    assert result.is_file()
    assert (dataset_dir / "sample.midi").is_file()
    assert (dataset_dir / DATASET_JSON_FILENAME).is_file()


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
