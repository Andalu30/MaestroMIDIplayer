from fastapi import APIRouter, HTTPException, Query

from ..data.dataset import store
from ..data.models import PaginatedTracks, Track

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.get("", response_model=PaginatedTracks)
def list_tracks(
    q: str | None = Query(None, max_length=200, description="Search composer or title"),
    composer: str | None = Query(None, max_length=100, description="Filter by composer slug"),
    year: int | None = Query(None, ge=2000, le=2030, description="Filter by year"),
    sort: str = Query("composer", pattern="^(composer|title|duration|year)$", description="Sort by: composer, title, duration, year"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results to return"),
):
    return store.search(q=q, composer=composer, year=year, sort=sort, order=order, skip=skip, limit=limit)


@router.get("/random", response_model=Track)
def random_track(
    composer: str | None = Query(None, max_length=100, description="Pick from this composer slug only"),
    year: int | None = Query(None, ge=2000, le=2030, description="Pick from this year only"),
):
    """A random track, optionally limited to a composer and/or year ("Surprise me")."""
    track = store.random_track(composer=composer, year=year)
    if not track:
        raise HTTPException(status_code=404, detail="No tracks match")
    return track


@router.get("/{track_id}")
def get_track(track_id: int):
    if 0 <= track_id < len(store.tracks):
        return store.tracks[track_id]
    raise HTTPException(status_code=404, detail="Track not found")
