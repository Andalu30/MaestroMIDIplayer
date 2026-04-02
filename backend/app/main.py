import logging
import os
import stat
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .composer_images import close_http_client
from .dataset import store
from .routers import composers, competitions, midi, tracks

logger = logging.getLogger("maestro")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:  %(name)s - %(message)s")


def _switch_identity() -> None:
    """Switch process UID/GID if MAESTRO_UID/MAESTRO_GID are set."""
    if settings.gid is not None:
        logger.info("Switching GID to %d", settings.gid)
        os.setgid(settings.gid)
    if settings.uid is not None:
        logger.info("Switching UID to %d", settings.uid)
        os.setuid(settings.uid)
    logger.info("Running as uid=%d gid=%d", os.getuid(), os.getgid())


def _log_path_info(label: str, path: Path) -> None:
    """Log existence, permissions, and ownership of a path."""
    if not path.exists():
        logger.error("%s: %s does NOT exist", label, path)
        return
    try:
        st = path.stat()
        mode = stat.filemode(st.st_mode)
        logger.info("%s: %s [%s uid=%d gid=%d]", label, path, mode, st.st_uid, st.st_gid)
    except OSError as e:
        logger.error("%s: %s stat failed: %s", label, path, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Maestro MIDI Player backend")
    logger.info("Dataset path: %s", settings.dataset_path)

    _log_path_info("Dataset dir", settings.dataset_path)

    csv_path = settings.dataset_path / "maestro-v3.0.0.csv"
    _log_path_info("CSV file", csv_path)

    _switch_identity()

    try:
        store.load(csv_path)
        logger.info("Loaded %d tracks, %d composers", len(store.tracks), len(store.composers))
    except PermissionError as e:
        logger.error("Permission denied loading CSV: %s", e)
        logger.error("Current uid=%d gid=%d — set MAESTRO_UID/MAESTRO_GID to match file ownership", os.getuid(), os.getgid())
        raise
    except Exception as e:
        logger.error("Failed to load dataset: %s", e)
        raise

    # Spot-check a MIDI file to catch permission issues early
    if store.tracks:
        sample = settings.dataset_path / store.tracks[0].midi_filename
        _log_path_info("Sample MIDI file", sample)
        if sample.exists():
            try:
                with open(sample, "rb") as f:
                    f.read(4)
                logger.info("Sample MIDI file readable OK")
            except PermissionError:
                logger.warning("Sample MIDI file exists but is NOT readable — MIDI serving will fail")

    yield

    await close_http_client()


app = FastAPI(title="Maestro MIDI Player", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracks.router)
app.include_router(composers.router)
app.include_router(competitions.router)
app.include_router(midi.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "tracks": len(store.tracks),
        "composers": len(store.composers),
        "years": sorted(store.by_year.keys()),
    }


# Serve frontend static files in production
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "build"
if _frontend_dir.is_dir():
    app.mount("/_app", StaticFiles(directory=_frontend_dir / "_app"), name="frontend-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve static files or fall back to index.html for SPA routing."""
        file_path = _frontend_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dir / "index.html")
