<script lang="ts">
	import { currentTrack, playerState, queue, activeNotes, pedalState, showPianoViz, showPedalIndicators, showPedalNames } from '$lib/stores';
	import { midiPlayer } from '$lib/midi-player';
	import { formatDuration } from '$lib/utils';
	import { onMount, onDestroy } from 'svelte';

	let position = $state(0);
	let duration = $state(0);
	let tempo = $state(1.0);
	let loading = $state(false);
	let midiSupported = $state(true);
	let showTempo = $state(false);
	let expanded = $state(false);

	let loadedTrackId = $state<number | null>(null);

	// Drag-to-expand/collapse state
	let dragging = $state(false);
	let dragStartY = 0;
	let dragDeltaY = $state(0);
	const DRAG_THRESHOLD = 60; // px to trigger expand/collapse

	function onDragStart(e: TouchEvent | PointerEvent) {
		const y = 'touches' in e ? e.touches[0].clientY : e.clientY;
		dragStartY = y;
		dragging = true;
		dragDeltaY = 0;
	}

	function onDragMove(e: TouchEvent | PointerEvent) {
		if (!dragging) return;
		const y = 'touches' in e ? e.touches[0].clientY : e.clientY;
		dragDeltaY = y - dragStartY;
	}

	function onDragEnd() {
		if (!dragging) return;
		dragging = false;
		if (expanded) {
			// Dragging down in expanded view → collapse
			if (dragDeltaY > DRAG_THRESHOLD) {
				expanded = false;
			}
		} else {
			// Dragging up in mini bar → expand
			if (dragDeltaY < -DRAG_THRESHOLD) {
				expanded = true;
			}
		}
		dragDeltaY = 0;
	}

	function handleStateUpdate(update: { state: 'playing' | 'paused' | 'stopped'; position: number; duration: number }) {
		playerState.set(update.state);
		position = update.position;
		duration = update.duration;

		// Auto-advance to next track when playback ends
		if (update.state === 'stopped' && loadedTrackId !== null) {
			queue.update(q => {
				if (q.length > 0) {
					const [next, ...rest] = q;
					currentTrack.set(next);
					return rest;
				}
				return q;
			});
		}
	}

	onMount(async () => {
		midiPlayer.setStateChangeCallback(handleStateUpdate);

		if (!navigator.requestMIDIAccess) {
			midiSupported = false;
		} else if (!midiPlayer.hasOutputs()) {
			// Auto-select all MIDI outputs on startup
			const outputs = await midiPlayer.getMidiOutputs();
			if (outputs.length > 0) {
				midiPlayer.setOutputs(outputs);
			}
		}
	});

	onDestroy(() => {
		midiPlayer.setStateChangeCallback(null as unknown as Parameters<typeof midiPlayer.setStateChangeCallback>[0]);
	});

	// React to track changes
	$effect(() => {
		const track = $currentTrack;
		if (track && track.id !== loadedTrackId) {
			loadAndPlay(track.id);
		} else if (!track) {
			midiPlayer.stop();
			loadedTrackId = null;
			expanded = false;
		}
	});

	async function loadAndPlay(trackId: number) {
		loading = true;
		try {
			loadedTrackId = null; // Prevent auto-advance from the stop() below
			midiPlayer.stop();
			if (trackId >= 0) {
				const dur = await midiPlayer.load(trackId);
				duration = dur;
			} else {
				// Negative ID = already loaded via loadFromBuffer (standalone player)
				duration = midiPlayer.getDuration();
			}
			position = 0;
			loadedTrackId = trackId;
			if (midiPlayer.hasOutputs()) {
				midiPlayer.play();
			}
		} catch (e) {
			console.error('Failed to load MIDI:', e);
		} finally {
			loading = false;
		}
	}

	function togglePlay() {
		if ($playerState === 'playing') {
			midiPlayer.pause();
		} else {
			midiPlayer.play();
		}
	}

	function stop() {
		loadedTrackId = null;
		midiPlayer.stop();
		position = 0;
		currentTrack.set(null);
		queue.set([]);
	}

	function nextTrack() {
		queue.update(q => {
			if (q.length > 0) {
				const [next, ...rest] = q;
				currentTrack.set(next);
				return rest;
			}
			return q;
		});
	}

	function prevTrack() {
		if (position > 3) {
			midiPlayer.seek(0);
		}
	}

	function onSeek(e: Event) {
		const input = e.target as HTMLInputElement;
		const sec = parseFloat(input.value);
		midiPlayer.seek(sec);
		position = sec;
	}

	function onTempoChange(e: Event) {
		const input = e.target as HTMLInputElement;
		tempo = parseFloat(input.value);
		midiPlayer.setTempo(tempo);
	}

	function resetTempo() {
		tempo = 1.0;
		midiPlayer.setTempo(1.0);
	}

	let progressPercent = $derived(duration > 0 ? (position / duration) * 100 : 0);
	let nextInQueue = $derived($queue.length > 0 ? $queue[0] : null);

	// Precompute 88-key piano layout (MIDI 21=A0 to 108=C8)
	const BLACK_NOTES = new Set([1, 3, 6, 8, 10]); // note-in-octave positions that are black
	const TOTAL_WHITE = 52;
	const KEY_W = 10; // white key width in px (mini bar)
	const BLACK_W = 6;

	interface PianoKey {
		midi: number;
		isBlack: boolean;
		left: number; // px from left edge of keyboard
	}

	const pianoKeys: PianoKey[] = (() => {
		const keys: PianoKey[] = [];
		let whiteIndex = 0;
		for (let midi = 21; midi <= 108; midi++) {
			const isBlack = BLACK_NOTES.has(midi % 12);
			if (isBlack) {
				keys.push({ midi, isBlack, left: whiteIndex * KEY_W - BLACK_W / 2 });
			} else {
				keys.push({ midi, isBlack, left: whiteIndex * KEY_W });
				whiteIndex++;
			}
		}
		return keys;
	})();

	const keyboardWidth = TOTAL_WHITE * KEY_W;

	// Realistic piano layout for expanded view (percentage-based for responsiveness)
	const REAL_WHITE_W_PCT = 100 / TOTAL_WHITE; // ~1.923%
	const REAL_BLACK_W_PCT = REAL_WHITE_W_PCT * 0.6;

	interface RealPianoKey {
		midi: number;
		isBlack: boolean;
		leftPct: number;
		widthPct: number;
	}

	const realPianoKeys: RealPianoKey[] = (() => {
		const keys: RealPianoKey[] = [];
		let whiteIdx = 0;
		for (let midi = 21; midi <= 108; midi++) {
			const isBlack = BLACK_NOTES.has(midi % 12);
			if (isBlack) {
				keys.push({
					midi,
					isBlack,
					leftPct: whiteIdx * REAL_WHITE_W_PCT - REAL_BLACK_W_PCT / 2,
					widthPct: REAL_BLACK_W_PCT
				});
			} else {
				keys.push({
					midi,
					isBlack,
					leftPct: whiteIdx * REAL_WHITE_W_PCT,
					widthPct: REAL_WHITE_W_PCT
				});
				whiteIdx++;
			}
		}
		return keys;
	})();
</script>

{#if $currentTrack}
	<!-- ===================== MINI PLAYER BAR ===================== -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="fixed bottom-0 left-0 right-0 z-50
				bg-surface-100/95 dark:bg-surface-900/95 backdrop-blur-sm
				border-t border-surface-200 dark:border-surface-800
				transition-transform duration-300 ease-out
				{expanded ? 'translate-y-full' : 'translate-y-0'}"
		 style={dragging && !expanded && dragDeltaY < 0 ? `transform: translateY(${Math.max(dragDeltaY, -80)}px)` : ''}
		 ontouchstart={onDragStart}
		 ontouchmove={onDragMove}
		 ontouchend={onDragEnd}
		 onpointerdown={(e) => { if (e.pointerType !== 'touch') onDragStart(e); }}
		 onpointermove={(e) => { if (e.pointerType !== 'touch') onDragMove(e); }}
		 onpointerup={(e) => { if (e.pointerType !== 'touch') onDragEnd(); }}
	>
		<!-- Piano keyboard visualization -->
		{#if $showPianoViz}
		<div class="absolute inset-0 flex items-end justify-center pointer-events-none overflow-hidden" aria-hidden="true">
			<div class="relative" style="width: {keyboardWidth}px; height: 100%">
				{#each pianoKeys.filter(k => !k.isBlack) as key (key.midi)}
					{@const vel = $activeNotes.get(key.midi)}
					<div
						class="absolute bottom-0 rounded-t-[1px] transition-all duration-75
							   {vel !== undefined
								? 'bg-surface-400/60 dark:bg-surface-400/40'
								: 'bg-surface-200/20 dark:bg-surface-700/15'}"
						style="left: {key.left}px; width: {KEY_W - 1}px; height: {vel !== undefined ? 12 + (vel / 127) * 16 : 12}px"
					></div>
				{/each}
				{#each pianoKeys.filter(k => k.isBlack) as key (key.midi)}
					{@const vel = $activeNotes.get(key.midi)}
					<div
						class="absolute bottom-0 z-10 rounded-t-[1px] transition-all duration-75
							   {vel !== undefined
								? 'bg-surface-500/70 dark:bg-surface-300/50'
								: 'bg-surface-300/20 dark:bg-surface-600/15'}"
						style="left: {key.left}px; width: {BLACK_W}px; height: {vel !== undefined ? 8 + (vel / 127) * 12 : 8}px"
					></div>
				{/each}
			</div>
		</div>
		{/if}

		<!-- Progress bar (thin, clickable) -->
		<div class="relative w-full h-1 bg-surface-200 dark:bg-surface-800 group cursor-pointer">
			<div
				class="absolute left-0 top-0 h-full bg-accent-500 transition-[width] duration-200"
				style="width: {progressPercent}%"
			></div>
			<div
				class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-accent-500
					   shadow-sm opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none
					   scale-75 group-hover:scale-100"
				style="left: {progressPercent}%"
			></div>
			<input
				type="range"
				min="0"
				max={duration}
				step="0.1"
				value={position}
				oninput={onSeek}
				class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
				aria-label="Seek"
			/>
		</div>

		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="max-w-6xl mx-auto px-2 sm:px-4 py-2.5 flex items-center gap-2 sm:gap-3 relative z-10"
			 onclick={() => expanded = true}>
			<!-- Transport -->
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="flex items-center gap-1" onclick={(e) => e.stopPropagation()}>
				<button onclick={prevTrack} aria-label="Previous track"
					class="p-1.5 rounded-full hover:bg-surface-200 dark:hover:bg-surface-700 text-surface-600 dark:text-surface-400">
					<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
				</button>
				<button onclick={togglePlay} aria-label={$playerState === 'playing' ? 'Pause' : 'Play'}
					class="p-2 rounded-full bg-accent-500 hover:bg-accent-600 text-white
						   {loading ? 'opacity-50 pointer-events-none' : ''}">
					{#if loading}
						<div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
					{:else if $playerState === 'playing'}
						<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
					{:else}
						<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
					{/if}
				</button>
				<button onclick={stop} aria-label="Stop"
					class="p-1.5 rounded-full hover:bg-surface-200 dark:hover:bg-surface-700 text-surface-600 dark:text-surface-400">
					<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12"/></svg>
				</button>
				<button onclick={nextTrack} aria-label="Next track"
					class="p-1.5 rounded-full hover:bg-surface-200 dark:hover:bg-surface-700 text-surface-600 dark:text-surface-400">
					<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
				</button>
			</div>

			<!-- Time -->
			<span class="text-xs text-surface-500 dark:text-surface-400 tabular-nums shrink-0 w-20 text-center hidden sm:block">
				{formatDuration(position)} / {formatDuration(duration)}
			</span>

			<!-- Track info -->
			<div class="flex-1 min-w-0 cursor-pointer">
				<p class="text-sm font-medium text-surface-900 dark:text-surface-100 truncate">
					{$currentTrack.title}
				</p>
				<p class="text-xs text-surface-500 dark:text-surface-400 truncate">
					{$currentTrack.composer}
				</p>
			</div>

			<!-- Expand chevron -->
			<button
				onclick={(e) => { e.stopPropagation(); expanded = true; }}
				aria-label="Expand player"
				class="p-1.5 rounded-full hover:bg-surface-200 dark:hover:bg-surface-700
					   text-surface-500 dark:text-surface-400 shrink-0"
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path d="M5 15l7-7 7 7"/>
				</svg>
			</button>

			<!-- Tempo -->
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="relative shrink-0 hidden sm:block" onclick={(e) => e.stopPropagation()}>
				<button
					onclick={() => showTempo = !showTempo}
					class="text-xs px-2 py-1 rounded-md
						   {tempo !== 1.0 ? 'bg-accent-500/15 text-accent-500' : 'text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200'}
						   transition-colors tabular-nums"
					aria-label="Tempo"
				>
					{tempo.toFixed(2)}x
				</button>
				{#if showTempo}
					<div class="absolute bottom-full right-0 mb-2 p-3 rounded-xl
								bg-surface-50 dark:bg-surface-850
								border border-surface-200 dark:border-surface-700
								shadow-xl w-48">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs text-surface-500">Tempo</span>
							<button onclick={resetTempo} class="text-xs text-accent-500 hover:underline">Reset</button>
						</div>
						<input
							type="range"
							min="0.25"
							max="2.0"
							step="0.05"
							value={tempo}
							oninput={onTempoChange}
							class="w-full accent-accent-500"
							aria-label="Tempo slider"
						/>
						<div class="relative text-xs text-surface-400 mt-1">
							<span class="absolute left-0">0.25x</span>
							<span class="absolute left-[42.86%] -translate-x-1/2">1x</span>
							<span class="absolute right-0">2x</span>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- ===================== EXPANDED PLAYER VIEW ===================== -->
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[55] bg-black/50 transition-opacity duration-300
			   {expanded ? 'opacity-100' : 'opacity-0 pointer-events-none'}"
		onclick={() => expanded = false}
	></div>

	<!-- Panel -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[60] flex flex-col
			   bg-surface-50 dark:bg-surface-950
			   transition-transform duration-300 ease-out
			   {expanded ? 'translate-y-0' : 'translate-y-full'}"
		style={dragging && expanded && dragDeltaY > 0 ? `transform: translateY(${Math.min(dragDeltaY, 200)}px)` : ''}
	>
		<!-- Drag handle + header -->
		<div class="shrink-0"
			 ontouchstart={onDragStart}
			 ontouchmove={onDragMove}
			 ontouchend={onDragEnd}
			 onpointerdown={(e) => { if (e.pointerType !== 'touch') onDragStart(e); }}
			 onpointermove={(e) => { if (e.pointerType !== 'touch') onDragMove(e); }}
			 onpointerup={(e) => { if (e.pointerType !== 'touch') onDragEnd(); }}
		>
			<!-- Handle bar -->
			<div class="flex justify-center pt-3 pb-1 cursor-grab active:cursor-grabbing">
				<div class="w-10 h-1 rounded-full bg-surface-300 dark:bg-surface-600"></div>
			</div>

			<div class="flex items-center justify-between px-4 sm:px-6 pb-2">
				<button
					onclick={() => expanded = false}
					aria-label="Collapse player"
					class="p-2 -ml-2 rounded-full hover:bg-surface-200 dark:hover:bg-surface-800
						   text-surface-500 dark:text-surface-400 transition-colors"
				>
					<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path d="M19 9l-7 7-7-7"/>
					</svg>
				</button>
				<span class="text-xs font-medium uppercase tracking-widest text-surface-400">Now Playing</span>
				<div class="w-10"></div>
			</div>
		</div>

		<!-- Main content area -->
		<div class="flex-1 flex flex-col items-center justify-center px-4 sm:px-8 overflow-hidden">
			<!-- Realistic piano keyboard -->
			{#if $showPianoViz}
			<div class="w-full max-w-2xl mb-8 sm:mb-12" aria-hidden="true">
				<div class="relative w-full transition-transform duration-200 ease-out"
					style="height: 100px; {$pedalState.soft > 0 ? `transform: translateX(${$pedalState.soft / 127 * 3}px)` : ''}">
					<!-- White keys -->
					{#each realPianoKeys.filter(k => !k.isBlack) as key (key.midi)}
						{@const vel = $activeNotes.get(key.midi)}
						<div
							class="absolute top-0 bottom-0 rounded-b-[3px] border transition-colors duration-75
								   {vel !== undefined
									? 'bg-accent-400 dark:bg-accent-500 border-accent-500 dark:border-accent-600'
									: 'bg-white dark:bg-surface-200 border-surface-300 dark:border-surface-400'}"
							style="left: {key.leftPct}%; width: calc({key.widthPct}% - 1px)"
						></div>
					{/each}
					<!-- Black keys -->
					{#each realPianoKeys.filter(k => k.isBlack) as key (key.midi)}
						{@const vel = $activeNotes.get(key.midi)}
						<div
							class="absolute top-0 z-10 rounded-b-[3px] transition-colors duration-75
								   {vel !== undefined
									? 'bg-accent-600 dark:bg-accent-400'
									: 'bg-surface-900 dark:bg-surface-950'}"
							style="left: {key.leftPct}%; width: {key.widthPct}%; height: 62%"
						></div>
					{/each}
				</div>

				<!-- Pedal indicators -->
				{#if $showPedalIndicators}
				<div class="flex items-center justify-center gap-4 mt-4">
					<div class="flex items-center gap-1.5">
						<div class="w-6 h-1.5 rounded-full transition-all duration-100 bg-accent-500/70 dark:bg-accent-400/60"
							style="opacity: {$pedalState.soft > 0 ? Math.max(0.15, $pedalState.soft / 127) : 0.12}; {$pedalState.soft === 0 ? 'background: var(--color-surface-300)' : ''}"></div>
						{#if $showPedalNames}<span class="text-[10px] uppercase tracking-wider text-surface-400">una corda</span>{/if}
					</div>
					<div class="flex items-center gap-1.5">
						<div class="w-6 h-1.5 rounded-full transition-all duration-100 bg-accent-500/70 dark:bg-accent-400/60"
							style="opacity: {$pedalState.sostenuto > 0 ? Math.max(0.15, $pedalState.sostenuto / 127) : 0.12}; {$pedalState.sostenuto === 0 ? 'background: var(--color-surface-300)' : ''}"></div>
						{#if $showPedalNames}<span class="text-[10px] uppercase tracking-wider text-surface-400">sostenuto</span>{/if}
					</div>
					<div class="flex items-center gap-1.5">
						<div class="w-6 h-1.5 rounded-full transition-all duration-100 bg-accent-500 dark:bg-accent-400"
							style="opacity: {$pedalState.sustain > 0 ? Math.max(0.15, $pedalState.sustain / 127) : 0.12}; {$pedalState.sustain === 0 ? 'background: var(--color-surface-300)' : ''}"></div>
						{#if $showPedalNames}<span class="text-[10px] uppercase tracking-wider text-surface-400">sustain</span>{/if}
					</div>
				</div>
				{/if}
			</div>
			{/if}

			<!-- Track info -->
			<div class="text-center mb-8 sm:mb-10 max-w-md w-full">
				<h2 class="text-xl sm:text-2xl font-bold text-surface-900 dark:text-surface-100 mb-2 line-clamp-2">
					{$currentTrack.title}
				</h2>
				<p class="text-base sm:text-lg text-surface-500 dark:text-surface-400">
					{$currentTrack.composer}
				</p>
				<div class="flex items-center justify-center gap-2 mt-2 text-xs text-surface-400">
					<span>{$currentTrack.year}</span>
					{#if $currentTrack.round}
						<span class="w-1 h-1 rounded-full bg-surface-400"></span>
						<span>Round {$currentTrack.round}</span>
					{/if}
					{#if $currentTrack.session}
						<span class="w-1 h-1 rounded-full bg-surface-400"></span>
						<span>Session {$currentTrack.session}</span>
					{/if}
				</div>
			</div>

			<!-- Progress bar -->
			<div class="w-full max-w-md mb-6 sm:mb-8">
				<div class="relative w-full h-1.5 bg-surface-200 dark:bg-surface-800 rounded-full group cursor-pointer">
					<div
						class="absolute left-0 top-0 h-full bg-accent-500 rounded-full transition-[width] duration-200"
						style="width: {progressPercent}%"
					></div>
					<div
						class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-accent-500
							   shadow-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
						style="left: {progressPercent}%"
					></div>
					<input
						type="range"
						min="0"
						max={duration}
						step="0.1"
						value={position}
						oninput={onSeek}
						class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
						aria-label="Seek"
					/>
				</div>
				<div class="flex justify-between mt-2 text-xs text-surface-400 tabular-nums">
					<span>{formatDuration(position)}</span>
					<span>{formatDuration(duration)}</span>
				</div>
			</div>

			<!-- Transport controls (large) -->
			<div class="flex items-center justify-center gap-4 sm:gap-6 mb-6 sm:mb-8">
				<button onclick={prevTrack} aria-label="Previous track"
					class="p-3 rounded-full hover:bg-surface-200 dark:hover:bg-surface-800
						   text-surface-600 dark:text-surface-400 transition-colors">
					<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
				</button>
				<button onclick={togglePlay} aria-label={$playerState === 'playing' ? 'Pause' : 'Play'}
					class="p-4 rounded-full bg-accent-500 hover:bg-accent-600 text-white shadow-lg
						   {loading ? 'opacity-50 pointer-events-none' : ''} transition-colors">
					{#if loading}
						<div class="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
					{:else if $playerState === 'playing'}
						<svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
					{:else}
						<svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
					{/if}
				</button>
				<button onclick={stop} aria-label="Stop"
					class="p-3 rounded-full hover:bg-surface-200 dark:hover:bg-surface-800
						   text-surface-600 dark:text-surface-400 transition-colors">
					<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12"/></svg>
				</button>
				<button onclick={nextTrack} aria-label="Next track"
					class="p-3 rounded-full hover:bg-surface-200 dark:hover:bg-surface-800
						   text-surface-600 dark:text-surface-400 transition-colors">
					<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
				</button>
			</div>

			<!-- Tempo control (always visible) -->
			<div class="w-full max-w-xs mb-6 sm:mb-8">
				<div class="flex items-center justify-between mb-2">
					<span class="text-xs text-surface-500 dark:text-surface-400">Tempo</span>
					<div class="flex items-center gap-2">
						<span class="text-xs tabular-nums text-surface-500 dark:text-surface-400">{tempo.toFixed(2)}x</span>
						{#if tempo !== 1.0}
							<button onclick={resetTempo} class="text-xs text-accent-500 hover:underline">Reset</button>
						{/if}
					</div>
				</div>
				<input
					type="range"
					min="0.25"
					max="2.0"
					step="0.05"
					value={tempo}
					oninput={onTempoChange}
					class="w-full accent-accent-500"
					aria-label="Tempo slider"
				/>
				<div class="relative text-xs text-surface-400 mt-1 h-4">
					<span class="absolute left-0">0.25x</span>
					<span class="absolute left-[42.86%] -translate-x-1/2">1x</span>
					<span class="absolute right-0">2x</span>
				</div>
			</div>
		</div>

		<!-- Up next -->
		{#if nextInQueue}
			<div class="shrink-0 px-6 sm:px-8 pb-6 sm:pb-8">
				<div class="max-w-md mx-auto p-3 rounded-xl bg-surface-100 dark:bg-surface-900
							border border-surface-200 dark:border-surface-800">
					<p class="text-xs text-surface-400 mb-1 uppercase tracking-wider">Up next</p>
					<p class="text-sm font-medium text-surface-900 dark:text-surface-100 truncate">{nextInQueue.title}</p>
					<p class="text-xs text-surface-500 dark:text-surface-400 truncate">{nextInQueue.composer}</p>
				</div>
			</div>
		{/if}
	</div>
{/if}
