<svelte:head>
	<title>Technical Documentation — maestroMIDIplayer</title>
</svelte:head>

<article class="max-w-2xl mx-auto">
	<h1 class="text-3xl font-bold text-surface-900 dark:text-surface-100 mb-2">Technical Documentation</h1>
	<p class="text-sm text-surface-400 mb-8">Architecture, API, data model, and deployment reference for maestroMIDIplayer.</p>

	<div class="space-y-10 text-surface-600 dark:text-surface-400 leading-relaxed">

		<!-- Table of contents -->
		<nav class="rounded-xl border border-surface-200 dark:border-surface-800 p-5 bg-surface-100/50 dark:bg-surface-900/50">
			<h2 class="text-sm font-semibold text-surface-800 dark:text-surface-200 mb-3 uppercase tracking-wider">Contents</h2>
			<ol class="columns-2 gap-8 text-sm space-y-1.5">
				<li><a href="#architecture" class="text-accent-500 hover:underline">Architecture overview</a></li>
				<li><a href="#dataset" class="text-accent-500 hover:underline">Dataset</a></li>
				<li><a href="#backend" class="text-accent-500 hover:underline">Backend</a></li>
				<li><a href="#api" class="text-accent-500 hover:underline">API reference</a></li>
				<li><a href="#frontend" class="text-accent-500 hover:underline">Frontend</a></li>
				<li><a href="#midi-engine" class="text-accent-500 hover:underline">MIDI playback engine</a></li>
				<li><a href="#stores" class="text-accent-500 hover:underline">State management</a></li>
				<li><a href="#testing" class="text-accent-500 hover:underline">Testing</a></li>
				<li><a href="#deployment" class="text-accent-500 hover:underline">Deployment</a></li>
				<li><a href="#configuration" class="text-accent-500 hover:underline">Configuration</a></li>
			</ol>
		</nav>

		<!-- Architecture overview -->
		<section id="architecture">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Architecture overview</h2>
			<p>
				The application follows a standard client-server split. A <strong class="text-surface-800 dark:text-surface-200">Python/FastAPI</strong>
				backend serves the dataset metadata, composer images, and raw MIDI files over a REST API. A <strong class="text-surface-800 dark:text-surface-200">SvelteKit</strong>
				frontend provides the UI and handles all MIDI playback client-side using the Web MIDI API.
			</p>
			<p class="mt-3">
				Once a MIDI file is fetched from the server, playback is entirely browser-based — no
				further server communication is needed. The backend is stateless for playback purposes;
				it only serves data.
			</p>

			<div class="mt-4 rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 font-mono text-xs text-surface-500 dark:text-surface-400 overflow-x-auto">
				<pre>┌─────────────────────────────────────────────────────┐
│                    Browser                          │
│                                                     │
│  SvelteKit App ──▶ Web MIDI API ──▶ Piano (BT/USB) │
│       │                                             │
│       │ fetch(/api/...)                             │
└───────┼─────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────┐
│                 FastAPI Backend                      │
│                                                     │
│  /api/tracks      CSV in-memory store               │
│  /api/composers   Wikimedia image proxy + cache     │
│  /api/competitions                                  │
│  /api/midi        Raw MIDI file serving             │
│  /api/health                                        │
└─────────────────────────────────────────────────────┘</pre>
			</div>
		</section>

		<!-- Dataset -->
		<section id="dataset">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Dataset</h2>
			<p>
				The app uses <strong class="text-surface-800 dark:text-surface-200">MAESTRO v3.0.0</strong>
				(MIDI and Audio Edited for Synchronous TRacks and Organization), created by Google's Magenta team.
			</p>

			<div class="mt-4 grid grid-cols-2 gap-3">
				<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-3 text-center">
					<div class="text-2xl font-bold text-accent-500">1,276</div>
					<div class="text-xs text-surface-400 mt-1">MIDI files</div>
				</div>
				<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-3 text-center">
					<div class="text-2xl font-bold text-accent-500">60</div>
					<div class="text-xs text-surface-400 mt-1">Composers</div>
				</div>
				<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-3 text-center">
					<div class="text-2xl font-bold text-accent-500">10</div>
					<div class="text-xs text-surface-400 mt-1">Competition years</div>
				</div>
				<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-3 text-center">
					<div class="text-2xl font-bold text-accent-500">2004–2018</div>
					<div class="text-xs text-surface-400 mt-1">Year range</div>
				</div>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Metadata CSV</h3>
			<p class="text-sm">
				The file <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">maestro-v3.0.0.csv</code>
				is the single source of truth. It is loaded into memory on startup — no database is used.
				Each row contains:
			</p>
			<div class="mt-2 overflow-x-auto">
				<table class="text-xs w-full border-collapse">
					<thead>
						<tr class="border-b border-surface-200 dark:border-surface-800">
							<th class="text-left py-1.5 pr-3 font-medium text-surface-700 dark:text-surface-300">Column</th>
							<th class="text-left py-1.5 font-medium text-surface-700 dark:text-surface-300">Description</th>
						</tr>
					</thead>
					<tbody class="text-surface-500 dark:text-surface-400">
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">canonical_composer</td><td>Full composer name</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">canonical_title</td><td>Piece title</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">split</td><td>train / validation / test</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">year</td><td>Competition year</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">midi_filename</td><td>Relative path to MIDI file</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">audio_filename</td><td>Relative path to audio (WAV)</td></tr>
						<tr><td class="py-1.5 pr-3 font-mono">duration</td><td>Duration in seconds (float)</td></tr>
					</tbody>
				</table>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Filename parsing</h3>
			<p class="text-sm">
				Competition round, session, and piece index are not columns in the CSV — they are extracted
				from the <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">audio_filename</code>
				at load time by a dedicated parser. The AUDIO portion is used because it contains richer
				structural metadata than the MIDI filename.
			</p>
			<ul class="text-sm mt-2 space-y-1 ml-4 list-disc">
				<li><strong class="text-surface-700 dark:text-surface-300">All years except 2017:</strong> Round
					extracted via <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">_R(\d+)_</code>
					regex, session from the two-digit number preceding the round marker.
				</li>
				<li><strong class="text-surface-700 dark:text-surface-300">2017:</strong> Round inferred from date
					in filename (July 6–7 = R1, July 8 = R2, July 9 = R3). Session from
					<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">Piano-e_{'{n}'}-{'{session}'}</code> pattern.
				</li>
				<li><strong class="text-surface-700 dark:text-surface-300">Piece index:</strong> Parsed from
					<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">wav--{'{n}'}</code> or
					<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">Track{'{nn}'}</code> suffixes.
				</li>
			</ul>
		</section>

		<!-- Backend -->
		<section id="backend">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Backend</h2>
			<p>
				Python 3.12+ with <strong class="text-surface-800 dark:text-surface-200">FastAPI</strong>.
				Dependencies managed with <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">uv</code>.
				No database — the CSV is loaded into an in-memory store on startup.
			</p>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Project structure</h3>
			<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 font-mono text-xs overflow-x-auto">
				<pre>backend/
├── pyproject.toml
├── app/
│   ├── main.py               # FastAPI app, lifespan, SPA serving
│   ├── config.py              # Pydantic Settings (env vars)
│   ├── dataset.py             # In-memory CSV store
│   ├── models.py              # Pydantic data models
│   ├── filename_parser.py     # Round/session extraction
│   ├── composer_images.py     # Wikipedia portrait fetcher + cache
│   └── routers/
│       ├── tracks.py          # /api/tracks
│       ├── composers.py       # /api/composers
│       ├── competitions.py    # /api/competitions
│       └── midi.py            # /api/midi (MIDI file serving)
└── tests/
    ├── test_filename_parser.py
    └── test_dataset.py</pre>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Key modules</h3>
			<div class="space-y-3 text-sm">
				<div>
					<strong class="text-surface-700 dark:text-surface-300">DatasetStore</strong>
					<span class="text-surface-400">(dataset.py)</span> —
					Singleton that loads the CSV via <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">csv.DictReader</code>,
					builds indexed lookups (<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">by_composer</code>,
					<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">by_year</code>),
					and provides search, filtering, and competition-structure queries.
				</div>
				<div>
					<strong class="text-surface-700 dark:text-surface-300">Composer images</strong>
					<span class="text-surface-400">(composer_images.py)</span> —
					Fetches portraits from Wikipedia's <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">pageimages</code>
					API, caches to disk as JPEG. Falls back to an SVG placeholder with the composer's initials.
					A <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">WIKI_OVERRIDES</code>
					dict maps slugs to correct Wikipedia article titles for ~20 common composers.
				</div>
				<div>
					<strong class="text-surface-700 dark:text-surface-300">Filename parser</strong>
					<span class="text-surface-400">(filename_parser.py)</span> —
					Extracts competition metadata (round, session, piece index) from audio filenames
					using year-specific regex patterns. Returns a
					<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">ParsedFilename</code> dataclass.
				</div>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Data models</h3>
			<p class="text-sm">All models are Pydantic v2 with computed fields:</p>
			<ul class="text-sm mt-2 space-y-1 ml-4 list-disc">
				<li><strong class="text-surface-700 dark:text-surface-300">Track</strong> — id, composer, title, split, year, midi/audio filenames, duration, round, session, piece_index. Computed: <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">duration_formatted</code>, <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">composer_slug</code>.</li>
				<li><strong class="text-surface-700 dark:text-surface-300">Composer</strong> — name, slug, track_count, total_duration. Computed: <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">total_duration_formatted</code>.</li>
				<li><strong class="text-surface-700 dark:text-surface-300">CompetitionYear</strong> — year, track_count, nested rounds → sessions → tracks.</li>
			</ul>
		</section>

		<!-- API Reference -->
		<section id="api">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">API reference</h2>
			<p class="text-sm mb-4">All endpoints are prefixed with <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">/api</code>. Responses are JSON unless noted.</p>

			<div class="space-y-4">
				<!-- Tracks -->
				<div class="rounded-lg border border-surface-200 dark:border-surface-800 overflow-hidden">
					<div class="bg-surface-100 dark:bg-surface-900 px-4 py-2 border-b border-surface-200 dark:border-surface-800">
						<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200">Tracks</h3>
					</div>
					<div class="divide-y divide-surface-100 dark:divide-surface-800/50 text-sm">
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/tracks</code>
							<span class="text-xs text-surface-400 ml-2">List/search tracks</span>
							<div class="text-xs text-surface-400 mt-1">
								Query params: <code class="px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">q</code> (search),
								<code class="px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">composer</code> (slug),
								<code class="px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">year</code>,
								<code class="px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">sort</code> (composer|title|duration|year),
								<code class="px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">order</code> (asc|desc)
							</div>
						</div>
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/tracks/{'{track_id}'}</code>
							<span class="text-xs text-surface-400 ml-2">Get single track by ID</span>
						</div>
					</div>
				</div>

				<!-- Composers -->
				<div class="rounded-lg border border-surface-200 dark:border-surface-800 overflow-hidden">
					<div class="bg-surface-100 dark:bg-surface-900 px-4 py-2 border-b border-surface-200 dark:border-surface-800">
						<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200">Composers</h3>
					</div>
					<div class="divide-y divide-surface-100 dark:divide-surface-800/50 text-sm">
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/composers</code>
							<span class="text-xs text-surface-400 ml-2">List all composers (sorted by track count desc)</span>
						</div>
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/composers/{'{slug}'}</code>
							<span class="text-xs text-surface-400 ml-2">Get single composer by slug</span>
						</div>
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/composers/{'{slug}'}/tracks</code>
							<span class="text-xs text-surface-400 ml-2">Get all tracks for a composer</span>
						</div>
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/composers/{'{slug}'}/image</code>
							<span class="text-xs text-surface-400 ml-2">Composer portrait (JPEG or SVG fallback)</span>
						</div>
					</div>
				</div>

				<!-- Competitions -->
				<div class="rounded-lg border border-surface-200 dark:border-surface-800 overflow-hidden">
					<div class="bg-surface-100 dark:bg-surface-900 px-4 py-2 border-b border-surface-200 dark:border-surface-800">
						<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200">Competitions</h3>
					</div>
					<div class="divide-y divide-surface-100 dark:divide-surface-800/50 text-sm">
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/competitions</code>
							<span class="text-xs text-surface-400 ml-2">List all competition years (summary)</span>
						</div>
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/competitions/{'{year}'}</code>
							<span class="text-xs text-surface-400 ml-2">Full detail: rounds → sessions → tracks</span>
						</div>
					</div>
				</div>

				<!-- MIDI -->
				<div class="rounded-lg border border-surface-200 dark:border-surface-800 overflow-hidden">
					<div class="bg-surface-100 dark:bg-surface-900 px-4 py-2 border-b border-surface-200 dark:border-surface-800">
						<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200">MIDI</h3>
					</div>
					<div class="text-sm">
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/midi/tracks/{'{track_id}'}/file</code>
							<span class="text-xs text-surface-400 ml-2">Raw MIDI file download (<code>audio/midi</code>)</span>
						</div>
					</div>
				</div>

				<!-- Health -->
				<div class="rounded-lg border border-surface-200 dark:border-surface-800 overflow-hidden">
					<div class="bg-surface-100 dark:bg-surface-900 px-4 py-2 border-b border-surface-200 dark:border-surface-800">
						<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200">System</h3>
					</div>
					<div class="text-sm">
						<div class="px-4 py-2.5">
							<code class="text-xs font-mono text-green-600 dark:text-green-400">GET</code>
							<code class="text-xs font-mono ml-2">/api/health</code>
							<span class="text-xs text-surface-400 ml-2">Health check (status, counts, years)</span>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- Frontend -->
		<section id="frontend">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Frontend</h2>
			<p>
				<strong class="text-surface-800 dark:text-surface-200">SvelteKit 2</strong> with
				<strong class="text-surface-800 dark:text-surface-200">Svelte 5</strong> (runes mode),
				<strong class="text-surface-800 dark:text-surface-200">Tailwind CSS 4</strong> via the Vite plugin,
				and <strong class="text-surface-800 dark:text-surface-200">TypeScript</strong>.
				Built as a static SPA using <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">adapter-static</code>
				with SPA fallback.
			</p>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Project structure</h3>
			<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 font-mono text-xs overflow-x-auto">
				<pre>frontend/
├── package.json
├── svelte.config.js         # adapter-static, SPA fallback
├── vite.config.ts           # Tailwind plugin, /api proxy
├── src/
│   ├── app.css              # Tailwind imports, theme tokens
│   ├── lib/
│   │   ├── api.ts           # Typed fetch wrappers
│   │   ├── stores.ts        # Svelte stores + TS interfaces
│   │   ├── midi-player.ts   # Client-side MIDI playback engine
│   │   └── utils.ts         # Helpers (formatDuration, etc.)
│   ├── components/
│   │   ├── PlayerBar.svelte  # Playback controls + piano viz
│   │   ├── SettingsPanel.svelte  # MIDI output + viz toggles
│   │   ├── SearchBar.svelte
│   │   ├── ThemeToggle.svelte
│   │   └── ...
│   └── routes/
│       ├── +layout.svelte   # App shell, nav, footer
│       ├── +page.svelte     # Home (composers + competitions)
│       ├── about/           # About page
│       ├── docs/            # This page
│       ├── player/          # Standalone MIDI player
│       ├── composers/       # All composers listing
│       ├── composer/[slug]/ # Composer detail
│       └── competition/[year]/ # Competition year detail
└── build/                   # Static output (production)</pre>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Dependencies</h3>
			<div class="overflow-x-auto">
				<table class="text-xs w-full border-collapse">
					<thead>
						<tr class="border-b border-surface-200 dark:border-surface-800">
							<th class="text-left py-1.5 pr-3 font-medium text-surface-700 dark:text-surface-300">Package</th>
							<th class="text-left py-1.5 pr-3 font-medium text-surface-700 dark:text-surface-300">Type</th>
							<th class="text-left py-1.5 font-medium text-surface-700 dark:text-surface-300">Purpose</th>
						</tr>
					</thead>
					<tbody class="text-surface-500 dark:text-surface-400">
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">@tonejs/midi</td><td class="pr-3">runtime</td><td>MIDI file parsing (Standard MIDI Format)</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">svelte</td><td class="pr-3">dev</td><td>UI framework (v5, runes)</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">@sveltejs/kit</td><td class="pr-3">dev</td><td>Application framework</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">tailwindcss</td><td class="pr-3">dev</td><td>Utility-first CSS (v4)</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">vite</td><td class="pr-3">dev</td><td>Build tool (v6)</td></tr>
						<tr><td class="py-1.5 pr-3 font-mono">typescript</td><td class="pr-3">dev</td><td>Type checking</td></tr>
					</tbody>
				</table>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Dev server</h3>
			<p class="text-sm">
				During development, Vite proxies all <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">/api</code>
				requests to <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">http://localhost:8000</code>
				(the FastAPI backend). SSR is disabled — the app runs entirely client-side.
			</p>
		</section>

		<!-- MIDI Playback Engine -->
		<section id="midi-engine">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">MIDI playback engine</h2>
			<p>
				The <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">MidiPlayer</code>
				class in <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">midi-player.ts</code>
				handles all playback. It is a singleton exported as
				<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">midiPlayer</code>.
			</p>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">How it works</h3>
			<ol class="text-sm mt-2 space-y-2 ml-4 list-decimal">
				<li>
					<strong class="text-surface-700 dark:text-surface-300">Loading:</strong>
					Fetches the MIDI file, parses it with <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">@tonejs/midi</code>,
					and flattens all tracks into a sorted event list (noteOn, noteOff, CC events).
				</li>
				<li>
					<strong class="text-surface-700 dark:text-surface-300">Scheduling:</strong>
					Events are scheduled in 2-second chunks using <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">setTimeout</code>,
					with re-scheduling at half the look-ahead window. Events more than 50ms in the past are skipped.
				</li>
				<li>
					<strong class="text-surface-700 dark:text-surface-300">Output:</strong>
					Raw MIDI messages are sent to all selected <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">MIDIOutput</code>
					devices via the Web MIDI API.
				</li>
				<li>
					<strong class="text-surface-700 dark:text-surface-300">Visualization:</strong>
					Active notes and pedal states are tracked internally and flushed to Svelte stores at ~30fps
					to decouple MIDI timing from rendering.
				</li>
			</ol>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Pedal tracking</h3>
			<p class="text-sm">
				Three MIDI CC messages are tracked for pedal visualization:
			</p>
			<ul class="text-sm mt-2 space-y-1 ml-4 list-disc">
				<li><strong class="text-surface-700 dark:text-surface-300">CC 64</strong> — Sustain (damper) pedal</li>
				<li><strong class="text-surface-700 dark:text-surface-300">CC 66</strong> — Sostenuto pedal</li>
				<li><strong class="text-surface-700 dark:text-surface-300">CC 67</strong> — Soft (una corda) pedal</li>
			</ul>
			<p class="text-sm mt-2">
				Values are 0–127, enabling half-pedaling visualization. The piano keyboard shifts slightly
				right when the una corda pedal is active, mimicking the real hammer mechanism.
			</p>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Tempo control</h3>
			<p class="text-sm">
				Playback speed can be adjusted from 0.25× to 2.0×. Changing tempo mid-playback
				recalculates the start reference time and re-schedules upcoming events without
				interrupting the audio output.
			</p>
		</section>

		<!-- State Management -->
		<section id="stores">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">State management</h2>
			<p class="text-sm">
				Application state lives in Svelte writable stores defined in
				<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">stores.ts</code>.
			</p>
			<div class="mt-3 overflow-x-auto">
				<table class="text-xs w-full border-collapse">
					<thead>
						<tr class="border-b border-surface-200 dark:border-surface-800">
							<th class="text-left py-1.5 pr-3 font-medium text-surface-700 dark:text-surface-300">Store</th>
							<th class="text-left py-1.5 pr-3 font-medium text-surface-700 dark:text-surface-300">Type</th>
							<th class="text-left py-1.5 font-medium text-surface-700 dark:text-surface-300">Purpose</th>
						</tr>
					</thead>
					<tbody class="text-surface-500 dark:text-surface-400">
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">theme</td><td class="pr-3">custom</td><td>Dark/light theme with localStorage persistence</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">currentTrack</td><td class="pr-3">Track | null</td><td>Currently playing track</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">playerState</td><td class="pr-3">'stopped' | 'playing' | 'paused'</td><td>Playback state</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">queue</td><td class="pr-3">Track[]</td><td>Upcoming tracks</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">activeNotes</td><td class="pr-3">Map&lt;number, number&gt;</td><td>Currently sounding notes (MIDI note → velocity)</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">pedalState</td><td class="pr-3">{'{sustain, soft, sostenuto}'}</td><td>Pedal CC values (0–127)</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">showPianoViz</td><td class="pr-3">boolean</td><td>Toggle piano keyboard display</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">showPedalIndicators</td><td class="pr-3">boolean</td><td>Toggle pedal indicator bars</td></tr>
						<tr><td class="py-1.5 pr-3 font-mono">showPedalNames</td><td class="pr-3">boolean</td><td>Toggle pedal name labels (default off)</td></tr>
					</tbody>
				</table>
			</div>
		</section>

		<!-- Testing -->
		<section id="testing">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Testing</h2>
			<p>
				Backend tests use <strong class="text-surface-800 dark:text-surface-200">pytest</strong>
				with <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">pytest-asyncio</code>.
				Tests run against the real dataset CSV.
			</p>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Test suites</h3>
			<div class="space-y-3 text-sm">
				<div>
					<strong class="text-surface-700 dark:text-surface-300">test_filename_parser.py</strong> —
					16 tests covering round/session extraction for all competition years.
					Dedicated suite for 2017's date-based round inference.
				</div>
				<div>
					<strong class="text-surface-700 dark:text-surface-300">test_dataset.py</strong> —
					Tests CSV loading (1,276 tracks, 60 composers, 10 years), search functionality
					(text search, year/composer filtering, sort order), competition structure
					(round/session nesting for 2018), and composer lookups.
				</div>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Running tests</h3>
			<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 font-mono text-xs">
				<pre>cd backend
uv run pytest          # run all tests
uv run pytest -v       # verbose output
uv run pytest -k 2017  # run only 2017-related tests</pre>
			</div>
		</section>

		<!-- Deployment -->
		<section id="deployment">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Deployment</h2>
			<p>
				The app is designed for home-server deployment. A multi-stage
				<strong class="text-surface-800 dark:text-surface-200">Docker</strong> build produces a single
				container serving both the API and the static frontend.
			</p>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Docker build stages</h3>
			<ol class="text-sm mt-2 space-y-2 ml-4 list-decimal">
				<li><strong class="text-surface-700 dark:text-surface-300">frontend-build</strong> — Node 22, runs <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">npm ci && npm run build</code> to produce the static SvelteKit output.</li>
				<li><strong class="text-surface-700 dark:text-surface-300">production</strong> — Python 3.13-slim, installs dependencies with <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">uv</code>, copies backend source and built frontend. Runs uvicorn on port 8000.</li>
			</ol>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">docker-compose.yml</h3>
			<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 font-mono text-xs overflow-x-auto">
				<pre>services:
  maestro:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./MaestroDataset:/data:ro
      - composer-cache:/app/backend/.cache/composer_images
    environment:
      MAESTRO_DATASET_PATH: /data
    restart: unless-stopped

volumes:
  composer-cache:</pre>
			</div>
			<p class="text-sm mt-3">
				The dataset is mounted read-only at <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">/data</code>.
				Composer image cache is persisted across container restarts via a named volume.
			</p>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Running locally (development)</h3>
			<div class="rounded-lg bg-surface-100 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 font-mono text-xs overflow-x-auto">
				<pre># Terminal 1: Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev</pre>
			</div>
			<p class="text-sm mt-3">
				The Vite dev server (default port 5173) proxies <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">/api</code> requests
				to <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">localhost:8000</code>.
			</p>
		</section>

		<!-- Configuration -->
		<section id="configuration">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Configuration</h2>
			<p class="text-sm">
				Backend configuration uses
				<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">pydantic-settings</code>.
				All settings can be overridden via environment variables with the
				<code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">MAESTRO_</code> prefix.
			</p>

			<div class="mt-3 overflow-x-auto">
				<table class="text-xs w-full border-collapse">
					<thead>
						<tr class="border-b border-surface-200 dark:border-surface-800">
							<th class="text-left py-1.5 pr-3 font-medium text-surface-700 dark:text-surface-300">Variable</th>
							<th class="text-left py-1.5 pr-3 font-medium text-surface-700 dark:text-surface-300">Default</th>
							<th class="text-left py-1.5 font-medium text-surface-700 dark:text-surface-300">Description</th>
						</tr>
					</thead>
					<tbody class="text-surface-500 dark:text-surface-400">
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">MAESTRO_DATASET_PATH</td><td class="pr-3 font-mono">../../MaestroDataset</td><td>Path to the MAESTRO dataset directory</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">MAESTRO_IMAGE_CACHE_DIR</td><td class="pr-3 font-mono">.cache/composer_images</td><td>Disk cache for composer portrait images</td></tr>
						<tr class="border-b border-surface-100 dark:border-surface-800/50"><td class="py-1.5 pr-3 font-mono">MAESTRO_HOST</td><td class="pr-3 font-mono">0.0.0.0</td><td>Server bind address</td></tr>
						<tr><td class="py-1.5 pr-3 font-mono">MAESTRO_PORT</td><td class="pr-3 font-mono">8000</td><td>Server port</td></tr>
					</tbody>
				</table>
			</div>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Web MIDI requirements</h3>
			<p class="text-sm">
				The Web MIDI API requires a <strong class="text-surface-700 dark:text-surface-300">secure context</strong>
				(HTTPS or localhost). When accessing over a LAN IP with plain HTTP, browsers will not
				expose the API. Options:
			</p>
			<ul class="text-sm mt-2 space-y-1 ml-4 list-disc">
				<li>Access via <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">localhost</code> on the same machine</li>
				<li>Set up HTTPS with a self-signed certificate</li>
				<li>Use a Chrome flag: <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">chrome://flags/#unsafely-treat-insecure-origin-as-secure</code></li>
			</ul>

			<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mt-5 mb-2">Browser compatibility</h3>
			<p class="text-sm">
				Chromium-based browsers only (Chrome, Edge, Opera, Brave). Firefox and Safari do not
				support the Web MIDI API.
			</p>
		</section>

		<!-- Built with -->
		<section>
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Tech stack</h2>
			<div class="flex flex-wrap gap-2">
				{#each [
					'SvelteKit 2', 'Svelte 5', 'Tailwind CSS 4', 'Vite 6', 'TypeScript',
					'FastAPI', 'Pydantic v2', 'uvicorn', 'uv',
					'Web MIDI API', '@tonejs/midi',
					'Docker', 'pytest'
				] as tech}
					<span class="text-xs px-2.5 py-1 rounded-full bg-surface-100 dark:bg-surface-800
								 text-surface-600 dark:text-surface-400 border border-surface-200 dark:border-surface-700">
						{tech}
					</span>
				{/each}
			</div>
		</section>
	</div>
</article>
