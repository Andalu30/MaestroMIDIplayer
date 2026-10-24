import { writable, type Writable } from 'svelte/store';
import { browser } from '$app/env';

/** Stored choice, else the OS preference (dark unless the OS asks for light). Mirrors the inline script in app.html. */
function initialTheme(): 'dark' | 'light' {
	if (!browser) return 'dark';
	const saved = safeGet('theme');
	if (saved === 'dark' || saved === 'light') return saved;
	return matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function createThemeStore() {
	const { subscribe, set, update } = writable(initialTheme());

	return {
		subscribe,
		toggle: () => {
			update((current) => {
				const next = current === 'dark' ? 'light' : 'dark';
				if (browser) {
					safeSet('theme', next);
					document.documentElement.classList.toggle('dark', next === 'dark');
				}
				return next;
			});
		},
		init: () => {
			if (browser) {
				const current = initialTheme();
				document.documentElement.classList.toggle('dark', current === 'dark');
				set(current);
			}
		}
	};
}

// localStorage throws in some private modes / when storage is blocked
function safeGet(key: string): string | null {
	try {
		return localStorage.getItem(key);
	} catch {
		return null;
	}
}

function safeSet(key: string, value: string) {
	try {
		localStorage.setItem(key, value);
	} catch {
		// not persisted; the in-memory value still works
	}
}

/** A writable store saved to localStorage as JSON. */
export function persisted<T>(key: string, initial: T): Writable<T> {
	let start = initial;
	if (browser) {
		const raw = safeGet(key);
		if (raw !== null) {
			try {
				start = JSON.parse(raw) as T;
			} catch {
				// corrupt value: keep the default
			}
		}
	}
	const store = writable<T>(start);
	if (browser) store.subscribe((value) => safeSet(key, JSON.stringify(value)));
	return store;
}

export const theme = createThemeStore();

export interface Track {
	id: number;
	composer: string;
	title: string;
	split: string;
	year: number;
	midi_filename: string;
	audio_filename: string;
	duration: number;
	duration_formatted: string;
	composer_slug: string;
	round: number | null;
	session: number | null;
	piece_index: number | null;
}

export interface Composer {
	name: string;
	slug: string;
	track_count: number;
	total_duration: number;
	total_duration_formatted: string;
}

export interface CompetitionSummary {
	year: number;
	track_count: number;
	rounds: { round: number; track_count: number; session_count: number }[];
}

export interface CompetitionSession {
	session: number | null;
	tracks: Track[];
}

export interface CompetitionRound {
	round: number | null;
	sessions: CompetitionSession[];
	track_count: number;
}

export interface CompetitionYear {
	year: number;
	track_count: number;
	rounds: CompetitionRound[];
}

export const currentTrack = writable<Track | null>(null);
export const playerState = writable<'stopped' | 'playing' | 'paused'>('stopped');
export const queue = writable<Track[]>([]);
/** Tracks played before the current one, most recent last (for the previous button) */
export const playHistory = writable<Track[]>([]);

/** What happens when a track ends: stop at the end of the queue, cycle the queue, or loop the track */
export const repeatMode = persisted<'off' | 'all' | 'one'>('repeatMode', 'off');

/** Playback speed (0.25–2.0); shared so keyboard shortcuts and both player views agree */
export const tempo = writable<number>(1.0);

/** Note velocity multiplier (0.5–1.5) — softer for late-evening playing, or a little more presence */
export const velocityScale = persisted<number>('velocityScale', 1.0);

/** Pause at this time (ms epoch), at the end of the current track, or never */
export const sleepTimer = writable<{ at: number } | 'end-of-track' | null>(null);

/** Keep the screen awake while playing (phones/tablets next to the piano) */
export const keepScreenOn = persisted<boolean>('keepScreenOn', true);

/** Map of currently active MIDI note numbers to their velocity (0-127) */
export const activeNotes = writable<Map<number, number>>(new Map());

/** Current state of the three MIDI pedals (0-127 each) */
export const pedalState = writable<{ sustain: number; soft: number; sostenuto: number }>({ sustain: 0, soft: 0, sostenuto: 0 });

/** Whether the piano visualizer is shown */
export const showPianoViz = persisted<boolean>('showPianoViz', true);

/** Whether pedal indicators are shown */
export const showPedalIndicators = persisted<boolean>('showPedalIndicators', true);

/** Whether pedal name labels are shown */
export const showPedalNames = persisted<boolean>('showPedalNames', false);

// Simple toast notification store
export interface Toast {
	id: number;
	message: string;
}

function createToastStore() {
	const { subscribe, update } = writable<Toast[]>([]);
	let nextId = 0;
	return {
		subscribe,
		show(message: string, duration = 2500) {
			const id = ++nextId;
			update((toasts) => [...toasts, { id, message }]);
			setTimeout(
				() => {
					update((toasts) => toasts.filter((t) => t.id !== id));
				},
				duration
			);
		}
	};
}

export const toasts = createToastStore();
