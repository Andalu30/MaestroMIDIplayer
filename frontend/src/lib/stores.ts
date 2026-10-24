import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function createThemeStore() {
	const initial = browser ? (localStorage.getItem('theme') || 'dark') : 'dark';
	const { subscribe, set, update } = writable(initial);

	return {
		subscribe,
		toggle: () => {
			update(current => {
				const next = current === 'dark' ? 'light' : 'dark';
				if (browser) {
					localStorage.setItem('theme', next);
					document.documentElement.classList.toggle('dark', next === 'dark');
				}
				return next;
			});
		},
		init: () => {
			if (browser) {
				const saved = localStorage.getItem('theme') || 'dark';
				document.documentElement.classList.toggle('dark', saved === 'dark');
				set(saved);
			}
		}
	};
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

/** Map of currently active MIDI note numbers to their velocity (0-127) */
export const activeNotes = writable<Map<number, number>>(new Map());

/** Current state of the three MIDI pedals (0-127 each) */
export const pedalState = writable<{ sustain: number; soft: number; sostenuto: number }>({ sustain: 0, soft: 0, sostenuto: 0 });

/** Whether the piano visualizer is shown */
export const showPianoViz = writable<boolean>(true);

/** Whether pedal indicators are shown */
export const showPedalIndicators = writable<boolean>(true);

/** Whether pedal name labels are shown */
export const showPedalNames = writable<boolean>(false);

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
			update(toasts => [...toasts, { id, message }]);
			setTimeout(() => {
				update(toasts => toasts.filter(t => t.id !== id));
			}, duration);
		},
	};
}

export const toasts = createToastStore();
