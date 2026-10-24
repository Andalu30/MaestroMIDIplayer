"""Subfolder hosting: base path normalisation, build rewrite, and proxy-agnostic routing."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.base_path import BUILD_PLACEHOLDER, BasePathMiddleware, normalize_base_path, prepare_frontend
from app.main import mount_frontend


@pytest.mark.parametrize("raw, expected", [
    ("", ""), ("/", ""), ("midi", "/midi"), ("/midi/", "/midi"), ("/apps/midi", "/apps/midi"),
])
def test_normalize(raw, expected):
    assert normalize_base_path(raw) == expected


@pytest.mark.parametrize("raw", ["/mi di", "/../x", "/a//b", "/x?y"])
def test_normalize_rejects_unsafe(raw):
    with pytest.raises(ValueError):
        normalize_base_path(raw)


def _build(tmp_path, placeholder=True):
    build = tmp_path / "build"
    (build / "_app").mkdir(parents=True)
    base = BUILD_PLACEHOLDER if placeholder else ""
    (build / "index.html").write_text(f'<script src="{base}/_app/start.js"></script>SPA')
    (build / "_app" / "start.js").write_text(f'const base = "{base}";')
    (build / "favicon.svg").write_text("<svg/>")
    return build


@pytest.mark.parametrize("base", ["", "/midi"])
def test_prepare_rewrites_placeholder(tmp_path, base):
    served = prepare_frontend(_build(tmp_path), base)
    assert BUILD_PLACEHOLDER not in (served / "index.html").read_text()
    assert f'src="{base}/_app/start.js"' in (served / "index.html").read_text()
    assert f'const base = "{base}";' == (served / "_app" / "start.js").read_text()
    # original build untouched
    assert BUILD_PLACEHOLDER in (tmp_path / "build" / "index.html").read_text()


def test_prepare_without_placeholder_serves_as_is(tmp_path):
    build = _build(tmp_path, placeholder=False)
    assert prepare_frontend(build, "/midi") == build


@pytest.fixture
def client(tmp_path):
    (tmp_path / "secret.txt").write_text("TOP SECRET")
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"ok": True}

    mount_frontend(app, prepare_frontend(_build(tmp_path), "/midi"))
    app.add_middleware(BasePathMiddleware, base_path="/midi")
    return TestClient(app)


@pytest.mark.parametrize("prefix", ["/midi", ""], ids=["proxy-keeps-prefix", "proxy-strips-prefix"])
def test_routes_with_and_without_prefix(client, prefix):
    assert client.get(f"{prefix}/api/health").json() == {"ok": True}
    assert client.get(f"{prefix}/_app/start.js").text == 'const base = "/midi";'
    page = client.get(f"{prefix}/composer/frederic-chopin")
    assert page.status_code == 200 and 'src="/midi/_app/start.js"' in page.text
    assert client.get(f"{prefix}/api/nope").status_code == 404


def test_bare_prefix_serves_app(client):
    assert "SPA" in client.get("/midi").text


def test_lookalike_prefix_not_stripped(client):
    # /midifoo must not be treated as /midi + foo
    res = client.get("/midifoo/api/health")
    assert "SPA" in res.text  # treated as an unknown client route, not as /api/health


@pytest.mark.parametrize("path", ["/midi/..%2fsecret.txt", "/midi/%2e%2e%2f%2e%2e%2fsecret.txt"])
def test_traversal_still_blocked_under_prefix(client, path):
    assert "TOP SECRET" not in client.get(path).text
