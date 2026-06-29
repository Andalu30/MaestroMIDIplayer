# MaestroMIDIplayer — AI Agent Instructions

A web app for browsing and playing the [MAESTRO v3.0.0](https://magenta.tensorflow.org/datasets/maestro) piano MIDI dataset. Designed for home server deployment — drives a Roland FP digital piano via Web MIDI API over Bluetooth.

> **Note:** This project is "vibecoded" — see [README](./README.md) for why it's not production-quality code. Expect experimental patterns and prioritize learning/functionality over best practices.

## Quick Start

### Development
```bash
# Backend (FastAPI on :8000)
cd backend && uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (SvelteKit + Vite on :5173, proxies /api to :8000)
cd frontend && npm install && npm run dev
```

### Production
```bash
docker compose up --build   # Multi-stage build, serves both API + frontend on :8000
```

## Architecture

| Component | Tech | Purpose |
|-----------|------|---------|
| **Backend** | Python 3.12+ / FastAPI / uv | API routes, CSV→memory load, composer image caching, server-side MIDI |
| **Frontend** | SvelteKit 2 / Svelte 5 / Tailwind 4 | Browse composers/competitions, player UI, Web MIDI playback |
| **Data** | CSV (no database) | MAESTRO dataset loaded entirely at startup into `store` |
| **Deployment** | Docker (multi-stage) | Node build → Python image, static frontend mounted |

## File Organization

```
backend/app/
  main.py                 → FastAPI app, middleware stack, static file serving
  core/
    config.py             → Pydantic Settings (MAESTRO_* env vars)
    limiter.py            → slowapi rate limiter instance (shared by main + routers)
  data/
    models.py             → Pydantic models (Track, Composer, CompetitionYear, etc.)
    filename_parser.py    → Extract round/session from MIDI filenames (regex)
    dataset.py            → CSV loader, singleton store, search/filter/sort
  services/
    composer_images.py    → Wikipedia fetcher + disk cache
  routers/                → Modular route handlers (tracks, composers, competitions, midi)

frontend/src/
  lib/api.ts              → Typed fetch wrapper (backend API client)
  lib/stores.ts           → Svelte stores (theme, player state, queue, MIDI viz)
  lib/midi-player.ts      → Web MIDI API playback engine
  lib/utils.ts            → Helpers (format duration, etc.)
  components/             → Reusable Svelte components (PlayerBar, ComposerCard, etc.)
  routes/                 → SvelteKit pages (file-based routing)
```

## Patterns & Conventions

### Backend (Python)

- **Routers**: Modular, each prefixed `/api/{resource}`. Access data via `from .data.dataset import store`.
- **Naming**: `snake_case` functions/variables, `MAESTRO_` env vars (SCREAMING_SNAKE_CASE).
- **Errors**: `HTTPException(status_code=404)` for missing resources.
- **Query params**: Optional filters (`q`, `composer`, `year`, `sort`, `order`) as `Query` objects with validation (max_length, pattern, ge/le).
- **Async for I/O only**: Image fetching is async; fast in-memory operations stay sync.
- **Computed fields**: Pydantic `@computed_field` for derived values (slugs, formatted duration).
- **Rate limiting**: `from .core.limiter import limiter` — use `@limiter.limit("N/minute")` for per-endpoint overrides; global default is 120/minute.

### Frontend (TypeScript / Svelte)

- **API client**: Generic `fetchJson<T>()` with typed responses matching backend models.
- **Stores**: Writable Svelte stores for theme, player state, queue, MIDI visualization.
- **Components**: PascalCase filenames (`.svelte`), use SvelteKit props.
- **Routes**: Bracket notation for dynamic segments (`[slug]`, `[year]`).
- **Build output**: Vite → `build/` directory, mounted in production Docker.
- **localStorage**: Theme persisted with browser check (media query fallback).

### General

- **No database**: Everything loaded from CSV at startup, immutable per session.
- **ID references**: Tracks use integer IDs (array index); composers use URL slugs.
- **Slug generation**: Simple ASCII normalization (lowercase, spaces→hyphens, Unicode stripped).

## Configuration

### Environment Variables (backend only, all `MAESTRO_` prefix)

| Variable | Default | Example |
|----------|---------|---------|
| `MAESTRO_DATASET_PATH` | `../MaestroDataset` | `/data` (Docker) |
| `MAESTRO_IMAGE_CACHE_DIR` | `.cache/composer_images` | `/cache` |
| `MAESTRO_HOST` | `0.0.0.0` | — |
| `MAESTRO_PORT` | `8000` | — |
| `MAESTRO_ENV` | `development` | `production` (disables `/docs`, `/redoc`, `/openapi.json`) |
| `MAESTRO_CORS_ORIGINS` | `["http://localhost:5173","http://localhost:8000"]` | `["https://midi.example.com"]` |
| `MAESTRO_UID` / `MAESTRO_GID` | None | `1000` (Docker permission switching) |

### Frontend Config

- **Dev proxy**: Vite routes `/api/*` → `http://localhost:8000` (see `vite.config.ts`)
- **Tailwind**: Configured via `@tailwindcss/vite` plugin
- **TypeScript**: Strict mode, `moduleResolution: "bundler"`
- **SvelteKit adapter**: Static, SPA fallback to `index.html`

## API Reference

See [README](./README.md#api) for full endpoint list. Key routes:

```
GET    /api/health                        # Health check + track/composer/year counts
GET    /api/tracks?q=search&sort=date     # Search, sort, paginate tracks
GET    /api/composers                     # All composers with stats
GET    /api/composers/{slug}/image        # Cached composer portrait (or SVG placeholder)
GET    /api/competitions/{year}           # Full competition data (rounds, sessions, tracks)
GET    /api/midi/tracks/{id}/file         # Raw MIDI download
WS     /api/playback                      # Server-side playback control (WebSocket)
```

## Development Tips

### Running Tests
```bash
cd backend && uv run pytest
```

### Adding a New Endpoint
1. Create a route handler in `backend/app/routers/{resource}.py`
2. Import and include in `main.py`: `app.include_router(my_router.router)`
3. Add Pydantic models to `backend/app/data/models.py` if needed
4. Access data store: `from ..data.dataset import store`
5. Frontend: add typed fetch call in `lib/api.ts`

### Adding a New Frontend Page
1. Create `frontend/src/routes/{path}/+page.svelte`
2. Import stores/components as needed
3. Fetch data from `lib/api.ts` with type safety
4. SvelteKit handles routing automatically

### Modifying the CSV Loader
- Edit `backend/app/data/dataset.py` (singleton `store`)
- Add computed fields to models via `@computed_field` in `backend/app/data/models.py`
- Restart backend for changes to take effect

### Cache Busting Composer Images
- Delete `.cache/composer_images/` directory (backend recreates on next fetch)
- Or set `MAESTRO_IMAGE_CACHE_DIR` to a new path

### Docker Debugging
```bash
docker compose up --build   # Full rebuild
docker compose logs -f      # Follow logs
docker exec -it <container> bash  # Shell access
```

## Common Gotchas

1. **Symlinks not supported in Docker** — Use bind mounts instead (`volumes:` in compose). Dataset is read-only.
2. **Web MIDI API requires Chromium** — Firefox, Safari don't support Web MIDI.
3. **CSV load at startup** — All data immutable during session. Restart backend to reload.
4. **Composer slug generation** — Simple ASCII normalization; Unicode chars are stripped. Test edge cases.
5. **Filename parsing is regex-heavy** — See `filename_parser.py` for year format variations (2004–2018).
6. **localStorage theme fallback** — Browser dark-mode preference used if no stored theme.

## References

- [README](./README.md) — Full feature list, tech stack, configuration, API reference
- [Project Structure](./README.md#project-structure) — Directory layout
- [MAESTRO Dataset](https://magenta.tensorflow.org/datasets/maestro) — Official dataset docs
- [SvelteKit Docs](https://kit.svelte.dev/) — Frontend framework
- [FastAPI Docs](https://fastapi.tiangolo.com/) — Backend framework
- [Web MIDI API](https://www.w3.org/TR/webmidi/) — Browser MIDI support
