"""Fetch and cache composer portrait images from Wikipedia/Wikimedia."""

import asyncio
import logging
from pathlib import Path

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Some composers in MAESTRO have names that differ from their Wikipedia article title.
# Map slug -> Wikipedia article title for those cases.
WIKI_OVERRIDES: dict[str, str] = {
    "frederic-chopin": "Frédéric Chopin",
    "claude-debussy": "Claude Debussy",
    "ludwig-van-beethoven": "Ludwig van Beethoven",
    "johann-sebastian-bach": "Johann Sebastian Bach",
    "wolfgang-amadeus-mozart": "Wolfgang Amadeus Mozart",
    "franz-schubert": "Franz Schubert",
    "franz-liszt": "Franz Liszt",
    "robert-schumann": "Robert Schumann",
    "johannes-brahms": "Johannes Brahms",
    "sergei-rachmaninoff": "Sergei Rachmaninoff",
    "alexander-scriabin": "Alexander Scriabin",
    "pyotr-ilyich-tchaikovsky": "Pyotr Ilyich Tchaikovsky",
    "felix-mendelssohn": "Felix Mendelssohn",
    "joseph-haydn": "Joseph Haydn",
    "maurice-ravel": "Maurice Ravel",
    "edvard-grieg": "Edvard Grieg",
    "sergei-prokofiev": "Sergei Prokofiev",
    "dmitri-shostakovich": "Dmitri Shostakovich",
    "bela-bartok": "Béla Bartók",
    "antonin-dvorak": "Antonín Dvořák",
}

# At most 4 Wikipedia fetches run concurrently — prevents OOM on cold start
# when the frontend requests all 60 composer images simultaneously.
_fetch_semaphore = asyncio.Semaphore(4)

# Track in-flight fetches so duplicate requests for the same slug share one download.
_in_flight: dict[str, asyncio.Task] = {}

# Shared client — avoids spawning 60 connection pools on a cold start.
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "MaestroMIDIPlayer/0.1 (https://github.com; educational project)"},
        )
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


def _cache_path(slug: str) -> Path:
    return settings.image_cache_dir / f"{slug}.jpg"


def get_cached_image(slug: str) -> Path | None:
    """Return the cached image path if it exists."""
    path = _cache_path(slug)
    if path.exists() and path.stat().st_size > 0:
        return path
    return None


async def _do_fetch(slug: str, composer_name: str) -> Path | None:
    """Inner fetch — runs under the semaphore, one at a time per slug."""
    wiki_title = WIKI_OVERRIDES.get(slug, composer_name)
    client = get_http_client()

    try:
        logger.info("Fetching Wikipedia image for %s (article: %s)", slug, wiki_title)
        resp = await client.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "titles": wiki_title,
                "prop": "pageimages",
                "pipiprop": "thumbnail",
                "pithumbsize": 400,
                "format": "json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            logger.info("No Wikipedia pages found for %s", slug)
            return None

        page = next(iter(pages.values()))
        thumbnail = page.get("thumbnail", {})
        image_url = thumbnail.get("source")

        if not image_url:
            logger.info("No image found for %s (wiki: %s)", slug, wiki_title)
            return None

        img_resp = await client.get(image_url)
        img_resp.raise_for_status()

        settings.image_cache_dir.mkdir(parents=True, exist_ok=True)
        path = _cache_path(slug)
        path.write_bytes(img_resp.content)
        logger.info("Cached image for %s (%d bytes)", slug, len(img_resp.content))
        return path

    except Exception:
        logger.warning("Failed to fetch image for %s", slug, exc_info=True)
        return None


async def fetch_composer_image(slug: str, composer_name: str) -> Path | None:
    """Fetch a composer portrait from Wikipedia and cache it to disk.

    Concurrent requests for the same slug are deduplicated — they share one
    download task. At most 4 fetches run simultaneously to avoid OOM on cold
    starts when all composers are requested at once.
    """
    cached = get_cached_image(slug)
    if cached:
        return cached

    # If there's already a fetch in flight for this slug, wait for it
    if slug in _in_flight:
        logger.debug("Waiting for in-flight fetch of %s", slug)
        try:
            return await asyncio.shield(_in_flight[slug])
        except asyncio.CancelledError:
            pass

    async def _guarded() -> Path | None:
        async with _fetch_semaphore:
            # Re-check cache — another request may have populated it while we waited
            cached = get_cached_image(slug)
            if cached:
                return cached
            return await _do_fetch(slug, composer_name)

    task = asyncio.create_task(_guarded())
    _in_flight[slug] = task
    try:
        return await task
    finally:
        _in_flight.pop(slug, None)


def generate_placeholder_svg(name: str) -> bytes:
    """Generate a simple SVG placeholder with the composer's initials."""
    import html
    initials = html.escape("".join(w[0] for w in name.split() if w)[:2].upper())
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <rect width="400" height="400" fill="#3f3f46"/>
  <text x="200" y="200" text-anchor="middle" dominant-baseline="central"
        font-family="serif" font-size="120" fill="#a1a1aa">{initials}</text>
</svg>"""
    return svg.encode("utf-8")
