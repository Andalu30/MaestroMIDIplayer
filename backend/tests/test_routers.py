"""Integration tests for all API routers using FastAPI TestClient."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

CSV_PATH = Path(__file__).resolve().parent / "data" / "minimal.csv"


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with the store loaded from the minimal CSV fixture.

    Mocks out dataset bootstrapping so the lifespan doesn't re-load real data,
    then uses the test CSV fixture for all API calls.
    """
    from app.main import app

    # Patch ensure_dataset_available to return the test CSV and prevent real download
    with patch("app.main.ensure_dataset_available", return_value=CSV_PATH), \
         patch("app.main.close_http_client", new=AsyncMock()):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        body = res.json()
        assert body["tracks"] == 4
        assert body["composers"] == 3
        assert "years" in body

    def test_health_has_dataset_readable(self, client):
        res = client.get("/api/health")
        assert "dataset_readable" in res.json()


# ---------------------------------------------------------------------------
# Tracks
# ---------------------------------------------------------------------------

class TestTracks:
    def test_list_tracks_default(self, client):
        res = client.get("/api/tracks")
        assert res.status_code == 200
        body = res.json()
        assert "total" in body
        assert "items" in body
        assert body["total"] == 4
        assert len(body["items"]) == 4

    def test_list_tracks_search(self, client):
        res = client.get("/api/tracks?q=chopin")
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 2
        assert all("Chopin" in t["composer"] for t in body["items"])

    def test_list_tracks_filter_year(self, client):
        res = client.get("/api/tracks?year=2018")
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 2
        assert all(t["year"] == 2018 for t in body["items"])

    def test_list_tracks_pagination(self, client):
        res = client.get("/api/tracks?limit=2&skip=0")
        assert res.status_code == 200
        body = res.json()
        assert len(body["items"]) == 2
        assert body["total"] == 4
        assert body["limit"] == 2
        assert body["skip"] == 0

    def test_list_tracks_pagination_skip(self, client):
        res = client.get("/api/tracks?limit=2&skip=2")
        assert res.status_code == 200
        body = res.json()
        assert len(body["items"]) == 2

    def test_list_tracks_invalid_sort(self, client):
        res = client.get("/api/tracks?sort=invalid")
        assert res.status_code == 422

    def test_list_tracks_invalid_year(self, client):
        res = client.get("/api/tracks?year=1900")
        assert res.status_code == 422

    def test_get_track_valid(self, client):
        res = client.get("/api/tracks/0")
        assert res.status_code == 200
        assert "id" in res.json()
        assert res.json()["id"] == 0

    def test_get_track_not_found(self, client):
        res = client.get("/api/tracks/9999")
        assert res.status_code == 404

    def test_get_track_negative(self, client):
        res = client.get("/api/tracks/-1")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# Composers
# ---------------------------------------------------------------------------

class TestComposers:
    def test_list_composers(self, client):
        res = client.get("/api/composers")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, list)
        assert len(body) == 3

    def test_get_composer_valid(self, client):
        res = client.get("/api/composers/frederic-chopin")
        assert res.status_code == 200
        assert res.json()["name"] == "Frédéric Chopin"

    def test_get_composer_not_found(self, client):
        res = client.get("/api/composers/does-not-exist")
        assert res.status_code == 404

    def test_get_composer_tracks(self, client):
        res = client.get("/api/composers/frederic-chopin/tracks")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, list)
        assert len(body) == 2
        assert all(t["composer"] == "Frédéric Chopin" for t in body)

    def test_get_composer_tracks_not_found(self, client):
        res = client.get("/api/composers/nobody/tracks")
        assert res.status_code == 404

    def test_get_composer_image_not_found(self, client):
        res = client.get("/api/composers/does-not-exist/image")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# Competitions
# ---------------------------------------------------------------------------

class TestCompetitions:
    def test_list_competitions(self, client):
        res = client.get("/api/competitions")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, list)
        years = [c["year"] for c in body]
        assert 2018 in years

    def test_get_competition_valid(self, client):
        res = client.get("/api/competitions/2018")
        assert res.status_code == 200
        body = res.json()
        assert body["year"] == 2018
        assert body["track_count"] == 2

    def test_get_competition_not_found(self, client):
        res = client.get("/api/competitions/1999")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# MIDI
# ---------------------------------------------------------------------------

class TestMidi:
    def test_midi_track_not_found(self, client):
        res = client.get("/api/midi/tracks/9999/file")
        assert res.status_code == 404

    def test_midi_track_negative(self, client):
        res = client.get("/api/midi/tracks/-1/file")
        assert res.status_code == 404

    def test_midi_track_valid_missing_file(self, client):
        # Track 0 exists in store but its MIDI file won't be on disk in CI
        res = client.get("/api/midi/tracks/0/file")
        # Either 200 (file found) or 404 (file missing from disk) are acceptable
        assert res.status_code in (200, 403, 404)
