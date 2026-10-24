import { get } from 'svelte/store';
import { browser } from '$app/env';
import { currentTrack, queue, playHistory, playerState, repeatMode, tempo, velocityScale, sleepTimer, keepScreenOn, toasts, type Track } from './stores';
import { composerImageUrl } from './api';
import { midiPlayer } from './midi-player';

const HISTORY_LIMIT = 100;
let lastTrack: Track | null = null;
let goingBack = false;

// Every track change, whatever caused it, lands in the history for the previous button
if (browser) {
	currentTrack.subscribe((track) => {
		// Negative ids are dropped local files whose data is gone once replaced
		if (lastTrack && lastTrack.id >= 0 && track?.id !== lastTrack.id && !goingBack) {
			const prev = lastTrack;
			playHistory.update((h) => [...h.slice(-(HISTORY_LIMIT - 1)), prev]);
		}
		goingBack = false;
		lastTrack = track;
	});
}

/** Start `tracks[index]` and queue the rest after it. */
export function playList(tracks: Track[], index = 0) {
	if (index < 0 || index >= tracks.length) return;
	currentTrack.set(tracks[index]);
	queue.set(tracks.slice(index + 1));
}

/** Advance to the next queued track. Returns false when the queue is empty. */
export function playNext(): boolean {
	const [next, ...rest] = get(queue);
	const current = get(currentTrack);
	// Repeat all: the queue is a loop, so what just played goes to the back
	if (get(repeatMode) === 'all' && current && current.id >= 0) rest.push(current);
	if (!next) {
		if (rest.length === 0) return false;
		return restartCurrent(); // only track in a repeat-all loop
	}
	queue.set(rest);
	currentTrack.set(next);
	return true;
}

/** Called by the player when a track finishes on its own. */
export function onTrackEnded() {
	if (get(sleepTimer) === 'end-of-track') {
		sleepTimer.set(null);
		toasts.show('Sleep timer: stopped');
		return;
	}
	if (get(repeatMode) === 'one') {
		restartCurrent();
		return;
	}
	playNext();
}

function restartCurrent(): boolean {
	midiPlayer.seek(0);
	midiPlayer.play();
	return true;
}

/** Put tracks right after the current one. */
export function queueNext(tracks: Track[]) {
	if (!get(currentTrack)) return playList(tracks);
	queue.update((q) => [...tracks, ...q]);
	toasts.show(tracks.length === 1 ? 'Playing next' : `${tracks.length} tracks playing next`);
}

/** Append tracks to the end of the queue (or start playing if nothing is). */
export function addToQueue(tracks: Track[]) {
	if (!get(currentTrack)) return playList(tracks);
	queue.update((q) => [...q, ...tracks]);
	toasts.show(tracks.length === 1 ? 'Added to queue' : `Added ${tracks.length} tracks to queue`);
}

export function shuffleQueue() {
	queue.update((q) => {
		const copy = [...q];
		for (let i = copy.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[copy[i], copy[j]] = [copy[j], copy[i]];
		}
		return copy;
	});
}

export function cycleRepeat() {
	repeatMode.update((m) => (m === 'off' ? 'all' : m === 'all' ? 'one' : 'off'));
}

export function setTempo(value: number) {
	const t = Math.round(Math.max(0.25, Math.min(2.0, value)) * 100) / 100;
	tempo.set(t);
	midiPlayer.setTempo(t);
}

export function togglePlayPause() {
	if (get(playerState) === 'playing') midiPlayer.pause();
	else midiPlayer.play();
}

// --- Sleep timer ---
let sleepHandle = 0;

/** Pause after `minutes`, at the end of the current track ('track'), or cancel (null). */
export function setSleepTimer(minutes: number | 'track' | null) {
	window.clearTimeout(sleepHandle);
	if (minutes === null) {
		sleepTimer.set(null);
	} else if (minutes === 'track') {
		sleepTimer.set('end-of-track');
	} else {
		const at = Date.now() + minutes * 60_000;
		sleepTimer.set({ at });
		// Hidden tabs may run this up to a minute late, which is fine for a sleep timer
		sleepHandle = window.setTimeout(() => {
			midiPlayer.pause();
			sleepTimer.set(null);
			toasts.show('Sleep timer: paused');
		}, minutes * 60_000);
	}
}

// --- OS integration: media keys / lock screen (Media Session) and screen wake lock ---
if (browser) {
	velocityScale.subscribe((v) => midiPlayer.setVelocityScale(v));
	setupMediaSession();
	setupWakeLock();
}

function setupMediaSession() {
	if (!('mediaSession' in navigator)) return;
	const ms = navigator.mediaSession;
	const handlers: [MediaSessionAction, MediaSessionActionHandler][] = [
		['play', () => midiPlayer.play()],
		['pause', () => midiPlayer.pause()],
		['stop', () => midiPlayer.pause()],
		['nexttrack', () => playNext()],
		['previoustrack', () => playPrevious()],
		['seekto', (d) => d.seekTime != null && midiPlayer.seek(d.seekTime)],
		['seekforward', (d) => midiPlayer.seek(midiPlayer.getPosition() + (d.seekOffset ?? 10))],
		['seekbackward', (d) => midiPlayer.seek(Math.max(0, midiPlayer.getPosition() - (d.seekOffset ?? 10)))],
	];
	for (const [action, handler] of handlers) {
		try {
			ms.setActionHandler(action, handler);
		} catch {
			// action not supported by this browser
		}
	}

	currentTrack.subscribe((track) => {
		if (!track) {
			ms.metadata = null;
			return;
		}
		ms.metadata = new MediaMetadata({
			title: track.title,
			artist: track.composer,
			album: track.year ? `Piano-e-Competition ${track.year}` : '',
			artwork: track.composer_slug
				? [{ src: new URL(composerImageUrl(track.composer_slug), location.href).href, sizes: '512x512' }]
				: [],
		});
	});

	playerState.subscribe((state) => {
		ms.playbackState = state === 'playing' ? 'playing' : state === 'paused' ? 'paused' : 'none';
		silentAudio(state === 'playing');
		updatePositionState();
	});
	tempo.subscribe(() => updatePositionState());
}

/** Keep the lock-screen scrubber in sync (called on play/pause/seek). */
export function updatePositionState() {
	if (!('mediaSession' in navigator) || !navigator.mediaSession.setPositionState) return;
	const duration = midiPlayer.getDuration();
	try {
		if (duration > 0 && get(currentTrack)) {
			navigator.mediaSession.setPositionState({
				duration,
				position: Math.min(midiPlayer.getPosition(), duration),
				playbackRate: midiPlayer.getTempo(),
			});
		} else {
			navigator.mediaSession.setPositionState();
		}
	} catch {
		// inconsistent values mid-transition; next update fixes it
	}
}

// Browsers only route media keys / show lock-screen controls to pages playing
// an <audio> element. MIDI makes no sound in the page, so play inaudible silence.
// On Android this also stops Chrome from freezing the backgrounded tab.
let audio: HTMLAudioElement | null = null;

function silentAudio(on: boolean) {
	if (!on) {
		audio?.pause();
		return;
	}
	if (!audio) {
		audio = new Audio(URL.createObjectURL(silentWav(10)));
		audio.loop = true;
	}
	audio.play().catch(() => {
		// autoplay policy: will start on the next user-initiated play
	});
}

/** A WAV file of `seconds` of silence (8 kHz, 8-bit mono). */
function silentWav(seconds: number): Blob {
	const samples = 8000 * seconds;
	const buf = new ArrayBuffer(44 + samples);
	const v = new DataView(buf);
	const str = (o: number, s: string) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
	str(0, 'RIFF'); v.setUint32(4, 36 + samples, true); str(8, 'WAVE');
	str(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
	v.setUint32(24, 8000, true); v.setUint32(28, 8000, true); v.setUint16(32, 1, true); v.setUint16(34, 8, true);
	str(36, 'data'); v.setUint32(40, samples, true);
	new Uint8Array(buf, 44).fill(128); // 8-bit PCM silence is the midpoint
	return new Blob([buf], { type: 'audio/wav' });
}

function setupWakeLock() {
	if (!('wakeLock' in navigator)) return;
	let lock: WakeLockSentinel | null = null;
	const sync = async () => {
		const want = get(keepScreenOn) && get(playerState) === 'playing' && document.visibilityState === 'visible';
		if (want && !lock) {
			try {
				lock = await navigator.wakeLock.request('screen');
				lock.addEventListener('release', () => (lock = null));
			} catch {
				// denied (e.g. battery saver); nothing to do
			}
		} else if (!want && lock) {
			await lock.release();
			lock = null;
		}
	};
	playerState.subscribe(() => void sync());
	keepScreenOn.subscribe(() => void sync());
	// The browser drops the lock when the tab is hidden; take it back on return
	document.addEventListener('visibilitychange', () => void sync());
}

/** Like a CD player: restart the piece if it's past the first seconds, else go back one track. */
export function playPrevious() {
	const history = get(playHistory);
	const current = get(currentTrack);
	if (midiPlayer.getPosition() > 3 || history.length === 0) {
		midiPlayer.seek(0);
		return;
	}
	const prev = history[history.length - 1];
	playHistory.set(history.slice(0, -1));
	if (current && current.id >= 0) queue.update((q) => [current, ...q]);
	goingBack = true;
	currentTrack.set(prev);
}
