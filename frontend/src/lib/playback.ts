import { get } from 'svelte/store';
import { browser } from '$app/env';
import { currentTrack, queue, playHistory, type Track } from './stores';
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
	if (!next) return false;
	queue.set(rest);
	currentTrack.set(next);
	return true;
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
