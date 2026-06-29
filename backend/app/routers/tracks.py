from fastapi import APIRouter, HTTPException, Query

from ..data.dataset import store

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.get("")
def list_tracks(
    q: str | None = Query(None, max_length=200, description="Search composer or title"),
    composer: str | None = Query(None, max_length=100, description="Filter by composer slug"),
    year: int | None = Query(None, ge=2000, le=2030, description="Filter by year"),
    sort: str = Query("composer", pattern="^(composer|title|duration|year)$", description="Sort by: composer, title, duration, year"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
):
    return store.search(q=q, composer=composer, year=year, sort=sort, order=order)


@router.get("/{track_id}")
def get_track(track_id: int):
    if 0 <= track_id < len(store.tracks):
        return store.tracks[track_id]
    raise HTTPException(status_code=404, detail="Track not found")
