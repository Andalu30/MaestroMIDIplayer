from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from ..config import settings
from ..dataset import store

router = APIRouter(prefix="/api/midi", tags=["midi"])


@router.get("/tracks/{track_id}/file")
def get_midi_file(track_id: int):
    if track_id < 0 or track_id >= len(store.tracks):
        return JSONResponse({"error": "Track not found"}, status_code=404)

    track = store.tracks[track_id]
    midi_path = settings.dataset_path / track.midi_filename
    if not midi_path.exists():
        return JSONResponse({"error": "MIDI file not found on disk"}, status_code=404)

    return FileResponse(
        midi_path,
        media_type="audio/midi",
        filename=Path(track.midi_filename).name,
    )
