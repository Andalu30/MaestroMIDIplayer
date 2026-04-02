# maestroMIDIplayer

A web app for browsing and playing the [MAESTRO v3.0.0](https://magenta.tensorflow.org/datasets/maestro) piano MIDI dataset on a real piano. Built for home server deployment — designed to drive a Roland FP digital piano via the Web MIDI API over Bluetooth.

1,276 piano performances from the International Piano-e-Competition, spanning 60 composers and 10 competition years (2004–2018).

> [!WARNING]
> This application is vibecoded.
> Do not use it as a reference for best practices in Python, FastAPI, SvelteKit, or any other technology. It is a personal project built for fun and learning, not production-quality code.
> For more information about this please see the [about page](https://midi.andalu30.me/about).

## Features

- **Browse by composer** — portrait cards with images from Wikipedia, sortable track lists
- **Browse by competition** — year/round/session hierarchy parsed from MIDI filenames
- **Client-side MIDI playback** — streams MIDI events to any connected output via the Web MIDI API
- **Live piano visualization** — 88-key display in the player bar lights up with active notes in real time
- **Search** — full-text search across composers and piece titles
- **Transport controls** — play, pause, stop, seek, tempo adjustment (0.25x–2.0x), auto-advance queue
- **Dark/light theme** — dark by default, persisted in localStorage
- **All-outputs mode** — sends MIDI to every available output simultaneously (no manual device selection needed)
- **Single-container Docker deployment** — multi-stage build, one image serves everything

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+ / FastAPI, managed with uv |
| Frontend | SvelteKit 2 (Svelte 5) + Tailwind CSS 4 |
| Client MIDI | Web MIDI API + @tonejs/midi |
| Composer images | Wikipedia PageImages API, disk-cached |
| Database | None — CSV loaded into memory at startup |
| Deployment | Docker (multi-stage build) |

## Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/)
- **Node.js 22+**
- The [MAESTRO v3.0.0 dataset](https://magenta.tensorflow.org/datasets/maestro) extracted to `MaestroDataset/` (or symlinked)
- A Chromium-based browser (Chrome, Edge) for Web MIDI API support

## Getting Started

### Development

Start the backend and frontend dev servers:

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

The frontend dev server proxies API requests to `localhost:8000`. Open http://localhost:5173 in your browser.

### Production (Docker)

```bash
docker compose up --build
```

This builds a single image that serves both the API and the compiled frontend on port 8000. The dataset is bind-mounted read-only.

### Production (without Docker)

```bash
# Build the frontend
cd frontend
npm ci && npm run build

# Run the backend (serves the built frontend automatically)
cd ../backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration

All settings use the `MAESTRO_` prefix and can be set as environment variables:

| Variable | Default | Description |
|---|---|---|
| `MAESTRO_DATASET_PATH` | `../MaestroDataset` | Path to the MAESTRO dataset directory |
| `MAESTRO_IMAGE_CACHE_DIR` | `.cache/composer_images` | Cache directory for composer portraits |
| `MAESTRO_HOST` | `0.0.0.0` | Server bind address |
| `MAESTRO_PORT` | `8000` | Server port |

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check with track/composer/year counts |
| GET | `/api/tracks` | List tracks (query: `?q=`, `?composer=`, `?year=`, `?sort=`, `?order=`) |
| GET | `/api/tracks/{id}` | Single track by ID |
| GET | `/api/composers` | List composers with piece counts and durations |
| GET | `/api/composers/{slug}/image` | Composer portrait (Wikipedia or SVG placeholder) |
| GET | `/api/composers/{slug}/tracks` | Tracks by composer |
| GET | `/api/competitions` | Competition years with round/session summaries |
| GET | `/api/competitions/{year}` | Full year data with rounds, sessions, tracks |
| GET | `/api/midi/tracks/{id}/file` | Raw MIDI file download |
| GET | `/api/midi/ports` | Available server-side MIDI output ports |
| WS | `/api/playback` | Server-side playback control (play, pause, stop, seek, tempo) |

## Project Structure

```
MaestroMIDIPlayer/
├── MaestroDataset/              # Symlink to MAESTRO v3.0.0 dataset
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              # FastAPI app, static file serving
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── models.py            # Pydantic models
│   │   ├── dataset.py           # CSV loader, in-memory store, search
│   │   ├── filename_parser.py   # Extract round/session from filenames
│   │   ├── composer_images.py   # Wikipedia image fetcher + cache
│   │   ├── midi_playback.py     # Server-side MIDI engine
│   │   └── routers/             # API route handlers
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.ts           # Backend API client
│   │   │   ├── midi-player.ts   # Web MIDI playback engine
│   │   │   ├── stores.ts        # Svelte stores + TypeScript interfaces
│   │   │   └── utils.ts         # Duration formatting, etc.
│   │   ├── components/          # PlayerBar, SearchBar, ComposerCard, etc.
│   │   └── routes/              # SvelteKit pages
│   └── static/
├── docs/                        # Architecture docs and dev log
├── Dockerfile                   # Multi-stage build
└── docker-compose.yml
```

## Dataset

The MAESTRO dataset is not included in this repository. Download it from [the official source](https://magenta.tensorflow.org/datasets/maestro) and place or symlink it as `MaestroDataset/` in the project root.

The dataset is provided under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## License

This project is for personal/educational use. The MAESTRO dataset has its own license (CC BY-NC-SA 4.0).
