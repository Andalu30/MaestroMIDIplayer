from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .dataset import store
from .routers import composers, competitions, midi, tracks


@asynccontextmanager
async def lifespan(app: FastAPI):
    csv_path = settings.dataset_path / "maestro-v3.0.0.csv"
    store.load(csv_path)
    print(f"Loaded {len(store.tracks)} tracks, {len(store.composers)} composers")
    yield


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
