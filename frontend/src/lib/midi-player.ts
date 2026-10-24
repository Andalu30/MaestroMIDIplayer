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
	private nextEventIndex = 0;   // next event not yet handed to the MIDI output
	// Events already sent with a future timestamp (Web MIDI can't reliably unsend them)
	private pending: { at: number; event: MidiEvent }[] = [];
	private clock: { start(): void; stop(): void } | null = null;
	private positionTimer = 0;

	private onStateChange: StateChangeCallback | null = null;
	private midiAccess: MIDIAccess | null = null;
	private outputListeners = new Set<(available: MIDIOutput[]) => void>();

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
		// Closing/reloading the tab mid-piece must not leave keys or pedal held
		window.addEventListener('pagehide', () => this.allNotesOff());
	}

	setStateChangeCallback(cb: StateChangeCallback) {
		this.onStateChange = cb;
	}

	async getMidiOutputs(): Promise<MIDIOutput[]> {
		try {
			return Array.from((await this.getAccess()).outputs.values());
		} catch {
			return [];
		}
	}

	/** Notified with the available outputs whenever a MIDI device connects/disconnects. */
	onOutputsChange(listener: (available: MIDIOutput[]) => void): () => void {
		this.outputListeners.add(listener);
		return () => this.outputListeners.delete(listener);
	}

	private async getAccess(): Promise<MIDIAccess> {
		if (!this.midiAccess) {
			const access = await navigator.requestMIDIAccess({ sysex: false });
			// e.g. a Bluetooth piano paired after the page loaded
			access.addEventListener('statechange', (e) => this.handlePortChange(e as MIDIConnectionEvent));
			this.midiAccess = access;
		}
		return this.midiAccess;
	}

	private handlePortChange(e: MIDIConnectionEvent) {
		const port = e.port;
		if (!port || port.type !== 'output' || !this.midiAccess) return;
		const available = Array.from(this.midiAccess.outputs.values()).filter((o) => o.state === 'connected');
		if (port.state === 'disconnected') {
			this.outputs = this.outputs.filter((o) => o.id !== port.id);
		} else if (this.outputs.length === 0 || (port.name && port.name === this.getPreferredOutput())) {
			// e.g. the preferred piano came back: switch to it from the all-outputs fallback
			this.outputs = this.pickOutputs(available);
		}
		for (const listener of this.outputListeners) listener(available);
	}

	/** Name of the output chosen in Settings, or null for "all outputs". Remembered across visits. */
	getPreferredOutput(): string | null {
		try {
			return localStorage.getItem('midiOutput');
		} catch {
			return null;
		}
	}

	setPreferredOutput(name: string | null) {
		try {
			if (name) localStorage.setItem('midiOutput', name);
			else localStorage.removeItem('midiOutput');
		} catch {
			// not remembered; the current selection still applies
		}
	}

	/** The preferred output if it's connected, otherwise all of them. */
	pickOutputs(available: MIDIOutput[]): MIDIOutput[] {
		const preferred = this.getPreferredOutput();
		const match = preferred ? available.filter((o) => o.name === preferred) : [];
		return match.length > 0 ? match.slice(0, 1) : available;
	}

	/** Select outputs per the saved preference (used at startup and on Refresh). */
	async autoSelectOutputs(): Promise<MIDIOutput[]> {
		const available = await this.getMidiOutputs();
		this.outputs = this.pickOutputs(available);
		return available;
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
			this.startScheduling();
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
		this.startScheduling();
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
			this.startScheduling();
		}
		this.emitState(wasPlaying ? 'playing' : 'paused');
	}

	setTempo(tempo: number) {
		const pos = this.playing ? this.currentPosition() : this.pausedAt;
		this.tempo = Math.max(0.25, Math.min(2.0, tempo));
		this.pausedAt = pos;
		// Events already sent (≤ one look-ahead window) play out at the old tempo;
		// everything from nextEventIndex on is timed against the new startTime
		if (this.playing) {
			this.startTime = performance.now() - (pos * 1000 / this.tempo);
		}
	}

	getTempo(): number {
		return this.tempo;
	}

	getDuration(): number {
		return this.duration;
	}

	getPosition(): number {
		return this.currentPosition();
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

	private startScheduling() {
		this.pump();
		this.getClock().start();
	}

	// Ticks come from a Web Worker: page timers in hidden tabs are throttled to
	// ~1/min by Chrome after 5 minutes, worker timers are not.
	private getClock() {
		if (!this.clock) {
			const tick = () => this.pump();
			try {
				const src = 'let t=0;onmessage=e=>{clearInterval(t);if(e.data==="start")t=setInterval(()=>postMessage(0),25)}';
				const worker = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
				worker.onmessage = tick;
				this.clock = { start: () => worker.postMessage('start'), stop: () => worker.postMessage('stop') };
			} catch {
				let timer = 0; // no Worker support: main-thread fallback
				this.clock = {
					start: () => { window.clearInterval(timer); timer = window.setInterval(tick, 25); },
					stop: () => window.clearInterval(timer),
				};
			}
		}
		return this.clock;
	}

	/** Send everything due within the look-ahead window, timestamped for exact timing. */
	private pump() {
		if (!this.playing) return;
		const now = performance.now();
		// Short window so pause/seek feel instant; longer when hidden to absorb
		// late worker messages on a backgrounded main thread
		const horizon = now + (document.hidden ? 1000 : 150);

		while (this.nextEventIndex < this.events.length) {
			const event = this.events[this.nextEventIndex];
			const at = this.startTime + (event.time / this.tempo) * 1000;
			if (at > horizon) break;
			this.sendMidi(event, Math.max(at, now));
			this.pending.push({ at, event });
			this.nextEventIndex++;
		}

		// Visualization follows what is actually sounding now
		while (this.pending.length && this.pending[0].at <= now) {
			this.updateVisualization(this.pending.shift()!.event);
		}

		const last = this.events[this.events.length - 1];
		if (this.nextEventIndex >= this.events.length && (!last || now >= this.startTime + (last.time / this.tempo) * 1000 + 300)) {
			this.finish();
		}
	}

	private finish() {
		this.getClock().stop();
		this.pending = [];
		this.allNotesOff(); // release anything still held (e.g. sustain pedal)
		this.playing = false;
		this.pausedAt = 0;
		this.nextEventIndex = 0;
		this.stopPositionUpdates();
		this.stopNotesFlush();
		this.clearActiveNotes();
		this.emitState('stopped');
	}

	private sendMidi(event: MidiEvent, timestamp?: number) {
		if (this.outputs.length === 0) return;
		const status = (() => {
			switch (event.type) {
				case 'noteOn':  return 0x90 | (event.channel & 0x0f);
				case 'noteOff': return 0x80 | (event.channel & 0x0f);
				case 'cc':      return 0xB0 | (event.channel & 0x0f);
			}
		})();
		for (const out of this.outputs) {
			out.send([status, event.data1, event.data2], timestamp);
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

	/**
	 * Stop the clock and neutralise events already queued in the output with a
	 * future timestamp: each queued note-on / pedal-down gets a matching release
	 * right after it, so nothing is left sounding after pause/seek/stop.
	 */
	private clearScheduled() {
		this.clock?.stop();
		const now = performance.now();
		for (const out of this.outputs) {
			(out as MIDIOutput & { clear?: () => void }).clear?.();
			for (const { at, event } of this.pending) {
				if (at <= now) continue;
				const ch = event.channel & 0x0f;
				if (event.type === 'noteOn' && event.data2 > 0) out.send([0x80 | ch, event.data1, 0], at + 1);
				else if (event.type === 'cc' && [64, 66, 67].includes(event.data1) && event.data2 > 0) out.send([0xB0 | ch, event.data1, 0], at + 1);
			}
		}
		this.pending = [];
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
