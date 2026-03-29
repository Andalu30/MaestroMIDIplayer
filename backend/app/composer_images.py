"""Fetch and cache composer portrait images from Wikipedia/Wikimedia."""

import logging
from pathlib import Path

import httpx

from .config import settings

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


def _cache_path(slug: str) -> Path:
    return settings.image_cache_dir / f"{slug}.jpg"


def get_cached_image(slug: str) -> Path | None:
    """Return the cached image path if it exists."""
    path = _cache_path(slug)
    if path.exists() and path.stat().st_size > 0:
        return path
    return None


async def fetch_composer_image(slug: str, composer_name: str) -> Path | None:
    """Fetch a composer portrait from Wikipedia and cache it to disk.

    Returns the path to the cached image, or None if not found.
    """
    # Check cache first
    cached = get_cached_image(slug)
    if cached:
        return cached

    # Determine the Wikipedia article title to search
    wiki_title = WIKI_OVERRIDES.get(slug, composer_name)

    try:
        headers = {"User-Agent": "MaestroMIDIPlayer/0.1 (https://github.com; educational project)"}
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            # Step 1: Get the page image from Wikipedia API
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
                return None

            # Get the first (and usually only) page
            page = next(iter(pages.values()))
            thumbnail = page.get("thumbnail", {})
            image_url = thumbnail.get("source")

            if not image_url:
                logger.info("No image found for %s (wiki: %s)", slug, wiki_title)
                return None

            # Step 2: Download the actual image
            img_resp = await client.get(image_url)
            img_resp.raise_for_status()

            # Save to cache
            settings.image_cache_dir.mkdir(parents=True, exist_ok=True)
            path = _cache_path(slug)
            path.write_bytes(img_resp.content)
            logger.info("Cached image for %s (%d bytes)", slug, len(img_resp.content))
            return path

    except Exception:
        logger.warning("Failed to fetch image for %s", slug, exc_info=True)
        return None


def generate_placeholder_svg(name: str) -> bytes:
    """Generate a simple SVG placeholder with the composer's initials."""
    initials = "".join(w[0] for w in name.split() if w)[:2].upper()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <rect width="400" height="400" fill="#3f3f46"/>
  <text x="200" y="200" text-anchor="middle" dominant-baseline="central"
        font-family="serif" font-size="120" fill="#a1a1aa">{initials}</text>
</svg>"""
    return svg.encode("utf-8")
