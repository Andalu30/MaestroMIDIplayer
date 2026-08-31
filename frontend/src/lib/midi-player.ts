import { Midi } from '@tonejs/midi';
import { midiFileUrl } from './api';
import { activeNotes, pedalState } from './stores';

interface MidiEvent {
	time: number;       // seconds (at original tempo)
	type: 'noteOn' | 'noteOff' | 'cc';
	channel: number;
	data1: number;      // note number or CC number
	data2: number;      // velocity or CC value
	trackIndex: number; // which source track this event belongs to
}

export interface TrackInfo {
	index: number;
	name: string;
	channel: number;
	instrument: string;
	noteCount: number;
	enabled: boolean;
}

type StateChangeCallback = (state: {
	state: 'playing' | 'paused' | 'stopped';
	position: number;
	duration: number;
}) => void;

export class MidiPlayer {
	private outputs: MIDIOutput[] = [];
	private allEvents: MidiEvent[] = [];   // all events from all tracks
	private events: MidiEvent[] = [];      // filtered by enabled tracks
	private tracks: TrackInfo[] = [];
	private duration = 0;
	private tempo = 1.0;

	// Playback state
	private playing = false;
	private startTime = 0;        // performance.now() when playback started
	private pausedAt = 0;         // elapsed seconds (original tempo) when paused
	private nextEventIndex = 0;
	private scheduledTimers: number[] = [];
	private positionTimer = 0;

	private onStateChange: StateChangeCallback | null = null;

	// Active note tracking — internal Map (note -> velocity) updated on every event,
	// flushed to Svelte store at ~30fps to decouple MIDI timing from rendering
	private _activeNotes = new Map<number, number>();
	private _pedalValues = { sustain: 0, soft: 0, sostenuto: 0 };
	private _notesDirty = false;
	private _notesFlushTimer = 0;

	constructor() {
		// When returning to a visible tab, resync visualization state — in
		// background tabs timers fire in bursts so viz may be slightly stale
		document.addEventListener('visibilitychange', () => {
			if (!document.hidden && this.playing) {
				this.resyncVisualization();
			}
		});
	}

	setStateChangeCallback(cb: StateChangeCallback) {
		this.onStateChange = cb;
	}

	async getMidiOutputs(): Promise<MIDIOutput[]> {
		try {
			const access = await navigator.requestMIDIAccess({ sysex: false });
			return Array.from(access.outputs.values());
		} catch {
			return [];
		}
	}

	setOutput(output: MIDIOutput | null) {
		this.outputs = output ? [output] : [];
	}

	setOutputs(outputs: MIDIOutput[]) {
		this.outputs = [...outputs];
	}

	getOutput(): MIDIOutput | null {
		return this.outputs[0] ?? null;
	}

	getOutputs(): MIDIOutput[] {
		return this.outputs;
	}

	hasOutputs(): boolean {
		return this.outputs.length > 0;
	}

	async load(trackId: number, signal?: AbortSignal): Promise<number> {
		const url = midiFileUrl(trackId);
		const res = await fetch(url, { signal });
		if (!res.ok) throw new Error(`Failed to fetch MIDI: ${res.status}`);
		const buf = await res.arrayBuffer();
		return this.loadFromBuffer(buf);
	}

	loadFromBuffer(buf: ArrayBuffer): number {
		if (buf.byteLength > 50 * 1024 * 1024) {
			throw new Error('MIDI file too large (max 50 MB)');
		}
		const midi = new Midi(buf);

		// Extract track info and build event list
		this.allEvents = [];
		this.tracks = [];

		for (let ti = 0; ti < midi.tracks.length; ti++) {
			const track = midi.tracks[ti];
			const channel = track.channel;

			this.tracks.push({
				index: ti,
				name: track.name || `Track ${ti + 1}`,
				channel,
				instrument: track.instrument?.name || 'unknown',
				noteCount: track.notes.length,
				enabled: true,
			});

			for (const note of track.notes) {
				const velocity = Math.round(note.velocity * 127);
				this.allEvents.push({
					time: note.time,
					type: 'noteOn',
					channel,
					data1: note.midi,
					data2: velocity,
					trackIndex: ti,
				});
				this.allEvents.push({
					time: note.time + note.duration,
					type: 'noteOff',
					channel,
					data1: note.midi,
					data2: 0,
					trackIndex: ti,
				});
			}

			// Include control changes (sustain pedal, etc.)
			if (track.controlChanges) {
				for (const ccNum of Object.keys(track.controlChanges)) {
					const ccEvents = track.controlChanges[ccNum as unknown as number];
					if (ccEvents) {
						for (const cc of ccEvents) {
							this.allEvents.push({
								time: cc.time,
								type: 'cc',
								channel,
								data1: cc.number,
								data2: Math.round(cc.value * 127),
								trackIndex: ti,
							});
						}
					}
				}
			}
		}

		// Sort by time
		this.allEvents.sort((a, b) => a.time - b.time || (a.type === 'noteOff' ? -1 : 1));
		this.rebuildFilteredEvents();
		this.duration = midi.duration;
		this.pausedAt = 0;
		this.nextEventIndex = 0;

		return this.duration;
	}

	getTracks(): TrackInfo[] {
		return this.tracks;
	}

	setTrackEnabled(trackIndex: number, enabled: boolean) {
		const track = this.tracks.find(t => t.index === trackIndex);
		if (!track || track.enabled === enabled) return;
		track.enabled = enabled;

		const wasPlaying = this.playing;
		const pos = wasPlaying ? this.currentPosition() : this.pausedAt;

		if (wasPlaying) {
			this.clearScheduled();
			this.allNotesOff();
			this.clearActiveNotes();
		}

		this.rebuildFilteredEvents();
		this.pausedAt = pos;
		this.nextEventIndex = this.events.findIndex(e => e.time >= pos);
		if (this.nextEventIndex === -1) this.nextEventIndex = this.events.length;

		if (wasPlaying) {
			this.startTime = performance.now() - (pos * 1000 / this.tempo);
			this.scheduleEvents();
		}
	}

	private rebuildFilteredEvents() {
		const enabledSet = new Set(this.tracks.filter(t => t.enabled).map(t => t.index));
		this.events = this.allEvents.filter(e => enabledSet.has(e.trackIndex));
	}

	play() {
		if (this.outputs.length === 0 || this.events.length === 0) return;
		if (this.playing) return;

		this.playing = true;
		this.startTime = performance.now() - (this.pausedAt * 1000 / this.tempo);
		this.scheduleEvents();
		this.startPositionUpdates();
		this.startNotesFlush();
		this.emitState('playing');
	}

	pause() {
		if (!this.playing) return;
		this.pausedAt = this.currentPosition(); // capture position while still playing
		this.playing = false;
		// Reset event index to the pause point so resume doesn't skip
		// the events that were scheduled but cleared by clearScheduled()
		this.nextEventIndex = this.events.findIndex(e => e.time >= this.pausedAt);
		if (this.nextEventIndex === -1) this.nextEventIndex = this.events.length;
		this.clearScheduled();
		this.allNotesOff();
		this.stopPositionUpdates();
		this.stopNotesFlush();
		this.clearActiveNotes();
		this.emitState('paused');
	}

	stop() {
		this.playing = false;
		this.pausedAt = 0;
		this.nextEventIndex = 0;
		this.clearScheduled();
		this.stopPositionUpdates();
		this.stopNotesFlush();
		this.clearActiveNotes();
		this.allNotesOff();
		this.emitState('stopped');
	}

	seek(seconds: number) {
		const wasPlaying = this.playing;
		if (wasPlaying) {
			this.clearScheduled();
			this.allNotesOff();
			this.clearActiveNotes();
		}

		this.pausedAt = Math.max(0, Math.min(seconds, this.duration));
		// Find the next event at or after this position
		this.nextEventIndex = this.events.findIndex(e => e.time >= this.pausedAt);
		if (this.nextEventIndex === -1) this.nextEventIndex = this.events.length;

		if (wasPlaying) {
			this.startTime = performance.now() - (this.pausedAt * 1000 / this.tempo);
			this.scheduleEvents();
		}
		this.emitState(wasPlaying ? 'playing' : 'paused');
	}

	setTempo(tempo: number) {
		const pos = this.playing ? this.currentPosition() : this.pausedAt;
		const wasPlaying = this.playing;

		if (wasPlaying) {
			this.clearScheduled();
		}

		this.tempo = Math.max(0.25, Math.min(2.0, tempo));
		this.pausedAt = pos;

		if (wasPlaying) {
			this.startTime = performance.now() - (this.pausedAt * 1000 / this.tempo);
			this.scheduleEvents();
		}
	}

	getTempo(): number {
		return this.tempo;
	}

	getDuration(): number {
		return this.duration;
	}

	currentPosition(): number {
		if (!this.playing) return this.pausedAt;
		const elapsed = (performance.now() - this.startTime) / 1000;
		return Math.min(elapsed * this.tempo, this.duration);
	}

	isPlaying(): boolean {
		return this.playing;
	}

	destroy() {
		this.stop();
		this.allEvents = [];
		this.events = [];
		this.tracks = [];
		this.outputs = [];
		this.onStateChange = null;
	}

	// --- Private ---

	private scheduleEvents() {
		// Look-ahead window: 3s is enough to survive background-tab throttling
		// (timers fire at ~1fps), while keeping the buffer small enough that
		// clearTimeout reliably cancels everything on stop/seek/change-piece.
		const SCHEDULE_AHEAD_MS = 3000;
		const now = performance.now();

		for (let i = this.nextEventIndex; i < this.events.length; i++) {
			const event = this.events[i];
			const eventRealTime = this.startTime + (event.time / this.tempo * 1000);
			const aheadMs = eventRealTime - now;

			if (aheadMs > SCHEDULE_AHEAD_MS) {
				// Re-schedule at half the look-ahead so we refill before running dry
				this.nextEventIndex = i;
				const timer = window.setTimeout(() => {
					if (this.playing) this.scheduleEvents();
				}, SCHEDULE_AHEAD_MS / 2);
				this.scheduledTimers.push(timer);
				return;
			}

			// Events in the past (background tab catch-up) fire immediately
			// rather than being skipped — a burst of notes is better than dropped notes
			const delay = Math.max(0, aheadMs);
			const timer = window.setTimeout(() => {
				if (!this.playing) return;
				this.sendMidiNow(event);
				this.updateVisualization(event);
			}, delay);
			this.scheduledTimers.push(timer);
		}

		// All events in the track have been scheduled — detect end of playback
		this.nextEventIndex = this.events.length;
		const lastEvent = this.events[this.events.length - 1];
		if (lastEvent) {
			const lastRealTime = this.startTime + (lastEvent.time / this.tempo * 1000);
			const remainingMs = lastRealTime - now + 300;
			const timer = window.setTimeout(() => {
				if (this.playing) {
					this.playing = false;
					this.pausedAt = 0;
					this.nextEventIndex = 0;
					this.stopPositionUpdates();
					this.stopNotesFlush();
					this.clearActiveNotes();
					this.emitState('stopped');
				}
			}, Math.max(0, remainingMs));
			this.scheduledTimers.push(timer);
		}
	}

	private sendMidiNow(event: MidiEvent) {
		if (this.outputs.length === 0) return;
		const status = (() => {
			switch (event.type) {
				case 'noteOn':  return 0x90 | (event.channel & 0x0f);
				case 'noteOff': return 0x80 | (event.channel & 0x0f);
				case 'cc':      return 0xB0 | (event.channel & 0x0f);
			}
		})();
		for (const out of this.outputs) {
			out.send([status, event.data1, event.data2]);
		}
	}

	private updateVisualization(event: MidiEvent) {
		if (event.type === 'noteOn' && event.data2 > 0) {
			this._activeNotes.set(event.data1, event.data2);
			this._notesDirty = true;
		} else if (event.type === 'noteOff' || (event.type === 'noteOn' && event.data2 === 0)) {
			this._activeNotes.delete(event.data1);
			this._notesDirty = true;
		} else if (event.type === 'cc') {
			if (event.data1 === 64) {
				this._pedalValues.sustain = event.data2;
				this._notesDirty = true;
			} else if (event.data1 === 66) {
				this._pedalValues.sostenuto = event.data2;
				this._notesDirty = true;
			} else if (event.data1 === 67) {
				this._pedalValues.soft = event.data2;
				this._notesDirty = true;
			}
		}
	}

	// Re-derive visualization state by replaying all events up to currentPosition().
	// Called when returning to a visible tab after being hidden.
	private resyncVisualization() {
		const pos = this.currentPosition();
		this._activeNotes.clear();
		this._pedalValues = { sustain: 0, soft: 0, sostenuto: 0 };
		for (const event of this.events) {
			if (event.time > pos) break;
			this.updateVisualization(event);
		}
		activeNotes.set(new Map(this._activeNotes));
		pedalState.set({ ...this._pedalValues });
		this._notesDirty = false;
	}

	private allNotesOff() {
		if (this.outputs.length === 0) return;
		// Send all-notes-off CC (123) and reset all controllers (121) on all channels
		for (const out of this.outputs) {
			for (let ch = 0; ch < 16; ch++) {
				out.send([0xB0 | ch, 123, 0]); // All Notes Off
				out.send([0xB0 | ch, 121, 0]); // Reset All Controllers
			}
		}
	}

	private clearScheduled() {
		for (const t of this.scheduledTimers) {
			window.clearTimeout(t);
		}
		this.scheduledTimers = [];
	}

	private startPositionUpdates() {
		this.stopPositionUpdates();
		this.positionTimer = window.setInterval(() => {
			if (this.playing) {
				this.emitState('playing');
			}
		}, 250); // 4Hz updates
	}

	private stopPositionUpdates() {
		if (this.positionTimer) {
			window.clearInterval(this.positionTimer);
			this.positionTimer = 0;
		}
	}

	private emitState(state: 'playing' | 'paused' | 'stopped') {
		this.onStateChange?.({
			state,
			position: this.currentPosition(),
			duration: this.duration,
		});
	}

	private startNotesFlush() {
		this.stopNotesFlush();
		this._notesFlushTimer = window.setInterval(() => {
			if (this._notesDirty) {
				this._notesDirty = false;
				activeNotes.set(new Map(this._activeNotes));
				pedalState.set({ ...this._pedalValues });
			}
		}, 33); // ~30fps
	}

	private stopNotesFlush() {
		if (this._notesFlushTimer) {
			window.clearInterval(this._notesFlushTimer);
			this._notesFlushTimer = 0;
		}
	}

	private clearActiveNotes() {
		this._activeNotes.clear();
		this._pedalValues = { sustain: 0, soft: 0, sostenuto: 0 };
		this._notesDirty = false;
		activeNotes.set(new Map());
		pedalState.set({ sustain: 0, soft: 0, sostenuto: 0 });
	}
}

// Singleton instance
export const midiPlayer = new MidiPlayer();
