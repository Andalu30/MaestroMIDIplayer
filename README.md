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
- **Transport controls** — play, pause, stop, seek, tempo adjustment (0.25x–2.0x), previous/next with play history
- **Queue** — view, reorder and remove upcoming tracks; "Play next" / "Add to queue" on any track; repeat (queue or track) and shuffle
- **Sleep timer and dynamics** — pause after 15–60 min or at the end of the piece; scale key velocity 50–150% for quiet playing
- **Media keys and lock screen** — Media Session integration (headset/Bluetooth buttons, OS media controls) and an optional screen wake lock while playing
- **Library** — favourites and recently played, kept in the browser; full search results page; "Surprise me" random piece
- **Keyboard shortcuts** — Space, ←/→, N/P, [ ] tempo, R repeat; press ? for the list
- **Dark/light theme** — follows the OS until toggled, persisted in localStorage; settings and the chosen MIDI output are remembered too
- **All-outputs mode** — sends MIDI to every available output simultaneously (no manual device selection needed)
- **Single-container Docker deployment** — multi-stage build, one image serves everything

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+ / FastAPI, managed with uv |
| Frontend | SvelteKit 3 (Svelte 5) + Tailwind CSS 4 |
| Client MIDI | Web MIDI API + @tonejs/midi |
| Composer images | Wikipedia PageImages API, disk-cached |
| Database | None — CSV loaded into memory at startup |
| Deployment | Docker (multi-stage build) |

## Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/)
- **Node.js 22.17+** (SvelteKit 3 minimum; 24 LTS recommended)
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

This builds a single image that serves both the API and the compiled frontend on port 8000. If no dataset is found at startup, the backend downloads and extracts MAESTRO v3.0.0 automatically.

### Production (RHEL / OpenShift)

The image is built to comply with OpenShift's **restricted / restricted-v2 SCC**:

- All files are owned by `UID 1000 / GID 0` (root group) with `chmod g=u` so any arbitrary UID injected by the namespace can read and write through group 0.
- The `USER` directive uses the numeric UID `1000` — named users are not resolvable when OpenShift assigns a high UID at runtime.
- Port 8000 is unprivileged, no special port capabilities are required.
- `allowPrivilegeEscalation: false` and `capabilities.drop: [ALL]` are set in the container securityContext.

#### Deploy with the provided manifests

All manifests live in [`deploy/`](deploy/) and work on both Kubernetes and OpenShift:

```bash
# Core: dataset PVC, Deployment, Service
oc apply -k deploy/            # or: kubectl apply -k deploy/

# Expose it with one of:
oc apply -f deploy/route.yaml          # OpenShift Route (TLS edge)
kubectl apply -f deploy/ingress.yaml   # Kubernetes Ingress (edit host/class first)
```

- **Image and updates:** the image is pinned to a release tag (e.g. `0.5.0`) so [Keel](https://keel.sh) can roll out newer releases (`keel.sh/policy: all`). Keel can't upgrade a deployment pinned to `:latest`.
- **First boot:** the pod downloads the MAESTRO v3.0.0 MIDI archive (~60 MB, ~85 MB extracted) into the PVC. A `startupProbe` allows up to 10 minutes for this. If your cluster lacks egress to Google Cloud Storage, pre-populate the PVC and set `MAESTRO_AUTO_DOWNLOAD_DATASET=false`.
- **Subfolder:** set `MAESTRO_BASE_PATH` in `deploy/deployment.yaml` and the matching `path:` on the Route or Ingress.

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

### Behind a reverse proxy, at the root or in a subfolder

The same image can be served at the root (`https://midi.example.com/`) or under a subfolder (`https://example.com/midi/`). For a subfolder, set `MAESTRO_BASE_PATH=/midi`. The app accepts requests **with or without** the prefix, so it works whether your proxy strips it or forwards it unchanged:

```yaml
# Traefik (labels): with or without the stripprefix middleware
- traefik.http.routers.midi.rule=PathPrefix(`/midi`)
- traefik.http.routers.midi.middlewares=midi-strip
- traefik.http.middlewares.midi-strip.stripprefix.prefixes=/midi
```

```nginx
location /midi/ { proxy_pass http://maestro:8000; }    # forwards /midi/...
# location /midi/ { proxy_pass http://maestro:8000/; } # strips /midi, also fine
```

```caddy
handle /midi* { reverse_proxy maestro:8000 }            # or handle_path (strips)
```

On OpenShift, set `path: /midi` on the Route; it forwards the prefix.

**Client IPs and rate limiting.** The API is rate-limited per client IP (120 req/min). Uvicorn only trusts `X-Forwarded-For` from `127.0.0.1`. Behind a proxy on another host, container or pod, all users therefore share the proxy's single bucket. Set `FORWARDED_ALLOW_IPS` to your proxy's address (e.g. `10.0.0.5` or `172.18.0.0/16`), or to `*` when the container is only reachable through the proxy (the Kubernetes/OpenShift manifests do this). Don't use `*` if the port is also exposed directly, because clients could then spoof their IP.

Without Docker, build the frontend with `MAESTRO_BUILD_BASE=/__MAESTRO_BASE__ npm run build` to make the base path configurable at runtime, or with `MAESTRO_BUILD_BASE=/midi` to fix it at build time.

## Configuration

All settings use the `MAESTRO_` prefix and can be set as environment variables:

| Variable | Default | Description |
|---|---|---|
| `MAESTRO_DATASET_PATH` | `../MaestroDataset` | Path to the MAESTRO dataset directory |
| `MAESTRO_AUTO_DOWNLOAD_DATASET` | `true` | Download and extract dataset automatically when CSV is missing |
| `MAESTRO_DATASET_DOWNLOAD_URL` | `https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0-midi.zip` | Dataset ZIP URL used for auto-download |
| `MAESTRO_DATASET_DOWNLOAD_TIMEOUT_SECONDS` | `10` | Per-socket-operation timeout (connect / each read) for the dataset download, not a total cap |
| `MAESTRO_IMAGE_CACHE_DIR` | `.cache/composer_images` | Cache directory for composer portraits |
| `MAESTRO_HOST` | `0.0.0.0` | Server bind address |
| `MAESTRO_PORT` | `8000` | Server port |
| `MAESTRO_ENV` | `development` | Set to `production` to disable the API docs UI |
| `MAESTRO_CORS_ORIGINS` | `["https://midi.andalu30.me","http://localhost:8000"]` | JSON list of allowed origins (only needed for cross-origin API use; the bundled SPA is same-origin) |
| `MAESTRO_BASE_PATH` | _(empty)_ | Serve from a subfolder, e.g. `/midi` (see [reverse proxy](#behind-a-reverse-proxy-at-the-root-or-in-a-subfolder)) |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxies whose `X-Forwarded-For` is trusted for client IPs (read by uvicorn; no `MAESTRO_` prefix) |

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check with track/composer/year counts |
| GET | `/api/tracks` | List tracks (query: `?q=`, `?composer=`, `?year=`, `?sort=`, `?order=`) |
| GET | `/api/tracks/random` | Random track (optional `composer` slug, `year`) |
| GET | `/api/tracks/{id}` | Single track by ID |
| GET | `/api/composers` | List composers with piece counts and durations |
| GET | `/api/composers/{slug}/image` | Composer portrait (Wikipedia or SVG placeholder) |
| GET | `/api/composers/{slug}/tracks` | Tracks by composer |
| GET | `/api/competitions` | Competition years with round/session summaries |
| GET | `/api/competitions/{year}` | Full year data with rounds, sessions, tracks |
| GET | `/api/midi/tracks/{id}/file` | Raw MIDI file download |

## Project Structure

```
MaestroMIDIPlayer/
├── MaestroDataset/              # Bind-mount point for MAESTRO v3.0.0 dataset
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, static file serving
│   │   ├── core/
│   │   │   ├── config.py        # Settings via pydantic-settings
│   │   │   └── limiter.py       # Rate limiter instance
│   │   ├── data/
│   │   │   ├── models.py        # Pydantic models
│   │   │   ├── dataset.py       # CSV loader, in-memory store, search
│   │   │   └── filename_parser.py  # Extract round/session from filenames
│   │   ├── services/
│   │   │   └── composer_images.py  # Wikipedia image fetcher + cache
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
├── Dockerfile                   # Multi-stage build
└── docker-compose.yml
```

## Dataset

The MAESTRO dataset is not included in this repository. If `maestro-v3.0.0.csv` is missing in `MAESTRO_DATASET_PATH`, the backend auto-downloads and extracts MAESTRO v3.0.0 at startup.

The dataset is provided under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## License

This project is for personal/educational use. The MAESTRO dataset has its own license (CC BY-NC-SA 4.0).
