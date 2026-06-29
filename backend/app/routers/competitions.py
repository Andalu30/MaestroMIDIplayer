from fastapi import APIRouter, HTTPException

from ..data.dataset import store

router = APIRouter(prefix="/api/competitions", tags=["competitions"])


@router.get("")
def list_competitions():
    """List all competition years with round/session structure (without full track data)."""
    competitions = store.get_competitions()
    # Return summary without embedding all tracks
    return [
        {
            "year": c.year,
            "track_count": c.track_count,
            "rounds": [
                {"round": r.round, "track_count": r.track_count, "session_count": len(r.sessions)}
                for r in c.rounds
            ],
        }
        for c in competitions
    ]


@router.get("/{year}")
def get_competition(year: int):
    comp = store.get_competition(year)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition year not found")
    return comp
