from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

from ..services.composer_images import fetch_composer_image, generate_placeholder_svg, get_cached_image
from ..data.dataset import store
from ..core.limiter import limiter

router = APIRouter(prefix="/api/composers", tags=["composers"])


@router.get("")
def list_composers():
    return store.composers


@router.get("/{slug}")
def get_composer(slug: str):
    composer = store.get_composer(slug)
    if not composer:
        raise HTTPException(status_code=404, detail="Composer not found")
    return composer


@router.get("/{slug}/image")
@limiter.limit("30/minute")
async def get_composer_image(request: Request, slug: str):
    """Serve the composer portrait image (cached or fetched from Wikipedia)."""
    composer = store.get_composer(slug)
    if not composer:
        raise HTTPException(status_code=404, detail="Composer not found")

    # Try cache first (fast path, no async needed)
    cached = get_cached_image(slug)
    if cached:
        return FileResponse(cached, media_type="image/jpeg")

    # Try fetching from Wikipedia
    path = await fetch_composer_image(slug, composer.name)
    if path:
        return FileResponse(path, media_type="image/jpeg")

    # Fallback: SVG placeholder with initials
    svg = generate_placeholder_svg(composer.name)
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/{slug}/tracks")
def get_composer_tracks(slug: str):
    tracks = store.get_composer_tracks(slug)
    if not tracks:
        raise HTTPException(status_code=404, detail="Composer not found")
    return tracks
