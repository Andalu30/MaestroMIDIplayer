from fastapi import APIRouter, HTTPException, Query

from ..dataset import store

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.get("")
def list_tracks(
    q: str | None = Query(None, description="Search composer or title"),
    composer: str | None = Query(None, description="Filter by composer slug"),
    year: int | None = Query(None, description="Filter by year"),
    sort: str = Query("composer", description="Sort by: composer, title, duration, year"),
    order: str = Query("asc", description="Sort order: asc or desc"),
):
    return store.search(q=q, composer=composer, year=year, sort=sort, order=order)


@router.get("/{track_id}")
def get_track(track_id: int):
    if 0 <= track_id < len(store.tracks):
        return store.tracks[track_id]
    raise HTTPException(status_code=404, detail="Track not found")
