import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..core.config import settings
from ..data.dataset import store

logger = logging.getLogger("maestro.midi")

router = APIRouter(prefix="/api/midi", tags=["midi"])


@router.get("/tracks/{track_id}/file")
def get_midi_file(track_id: int):
    if track_id < 0 or track_id >= len(store.tracks):
        raise HTTPException(status_code=404, detail="Track not found")

    track = store.tracks[track_id]
    dataset_root = settings.dataset_path.resolve()
    midi_path = (dataset_root / track.midi_filename).resolve()

    # Guard against path traversal via a corrupted CSV entry
    if not str(midi_path).startswith(str(dataset_root) + "/"):
        logger.error("Path traversal attempt blocked for track %d: %s", track_id, midi_path)
        raise HTTPException(status_code=403, detail="Access denied")

    if not midi_path.exists():
        logger.warning("MIDI file not found: %s", midi_path)
        raise HTTPException(status_code=404, detail="MIDI file not found on disk")

    return FileResponse(
        midi_path,
        media_type="audio/midi",
        filename=Path(track.midi_filename).name,
    )
