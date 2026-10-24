"""Serving the app from a subfolder (e.g. https://host/midi/) behind any reverse proxy.

The frontend is built (in Docker) with a placeholder base path that is rewritten
at startup, and requests are accepted both with and without the prefix, so it
works whether the proxy strips the prefix (Traefik StripPrefix, nginx
`proxy_pass .../;`, Caddy `handle_path`) or keeps it (OpenShift Route paths).
"""

import logging
import re
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger("maestro.base_path")

# Must match MAESTRO_BUILD_BASE in the Dockerfile
BUILD_PLACEHOLDER = "/__MAESTRO_BASE__"

_SEGMENT = r"[A-Za-z0-9._~-]+"
_REWRITE_SUFFIXES = {".html", ".js", ".css", ".json", ".webmanifest", ".txt"}


def normalize_base_path(value: str) -> str:
    """'' for root, otherwise '/a' or '/a/b' (leading slash, no trailing slash)."""
    value = value.strip().strip("/")
    if not value:
        return ""
    if not re.fullmatch(rf"{_SEGMENT}(/{_SEGMENT})*", value) or any(set(seg) == {"."} for seg in value.split("/")):
        raise ValueError(f"Invalid base path {value!r}: use URL-safe segments like /midi or /apps/midi")
    return "/" + value


def prepare_frontend(build_dir: Path, base_path: str) -> Path:
    """Return a directory to serve the SPA from, with the build placeholder replaced.

    Builds without the placeholder (local `npm run build`) are served as-is.
    Otherwise the build is copied to a temp dir so the image itself stays
    read-only and the same image works for any base path.
    """
    index = build_dir / "index.html"
    if BUILD_PLACEHOLDER not in index.read_text(encoding="utf-8"):
        if base_path:
            logger.warning("MAESTRO_BASE_PATH=%s ignored: frontend was not built with the base-path placeholder", base_path)
        return build_dir

    target = Path(tempfile.mkdtemp(prefix="maestro-frontend-"))
    shutil.copytree(build_dir, target, dirs_exist_ok=True)
    rewritten = 0
    for file in target.rglob("*"):
        if file.is_file() and file.suffix in _REWRITE_SUFFIXES:
            text = file.read_text(encoding="utf-8")
            if BUILD_PLACEHOLDER in text:
                file.write_text(text.replace(BUILD_PLACEHOLDER, base_path), encoding="utf-8")
                rewritten += 1
    logger.info("Frontend prepared for base path %r (%d files rewritten) in %s", base_path or "/", rewritten, target)
    return target


class BasePathMiddleware:
    """Strip the base path when the proxy forwarded it; pass through when it already stripped it."""

    def __init__(self, app, base_path: str):
        self.app = app
        self.base_path = base_path

    async def __call__(self, scope, receive, send):
        if self.base_path and scope["type"] in ("http", "websocket"):
            path = scope["path"]
            if path == self.base_path or path.startswith(self.base_path + "/"):
                stripped = path[len(self.base_path):] or "/"
                scope = dict(scope, path=stripped, raw_path=stripped.encode())
        await self.app(scope, receive, send)
