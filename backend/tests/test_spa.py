"""SPA static serving: client routes, real files, and no escape from the build dir."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import mount_frontend


@pytest.fixture
def spa(tmp_path):
    build = tmp_path / "build"
    (build / "_app" / "immutable").mkdir(parents=True)
    (build / "index.html").write_text("<!doctype html>SPA")
    (build / "favicon.png").write_bytes(b"\x89PNG")
    (build / "_app" / "immutable" / "app.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("TOP SECRET")

    app = FastAPI()
    mount_frontend(app, build)
    return TestClient(app)


def test_client_route_serves_index(spa):
    res = spa.get("/composer/frederic-chopin")
    assert res.status_code == 200
    assert "SPA" in res.text


def test_real_file_served(spa):
    assert spa.get("/favicon.png").content == b"\x89PNG"
    assert spa.get("/_app/immutable/app.js").text == "console.log(1)"


@pytest.mark.parametrize("path", [
    "/../secret.txt",
    "/..%2fsecret.txt",
    "/%2e%2e/secret.txt",
    "/%2e%2e%2fsecret.txt",
    "/_app/..%2f..%2fsecret.txt",
])
def test_traversal_never_leaks_files(spa, path):
    res = spa.get(path)
    assert "TOP SECRET" not in res.text


def test_unknown_api_path_is_404(spa):
    res = spa.get("/api/does-not-exist")
    assert res.status_code == 404
    assert res.headers["content-type"].startswith("application/json")
