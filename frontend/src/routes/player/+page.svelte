<script lang="ts">
	import { midiPlayer } from '$lib/midi-player';
	import { currentTrack, queue } from '$lib/stores';
	import type { Track } from '$lib/stores';
	import { formatDuration } from '$lib/utils';

	let dragOver = $state(false);
	let fileName = $state('');
	let fileDuration = $state(0);
	let error = $state('');
	let fileInputEl: HTMLInputElement;

	async function handleFile(file: File) {
		if (!file.name.toLowerCase().endsWith('.mid') && !file.name.toLowerCase().endsWith('.midi')) {
			error = 'Please drop a MIDI file (.mid or .midi)';
			return;
		}

		error = '';
		try {
			const buf = await file.arrayBuffer();
			const dur = midiPlayer.loadFromBuffer(buf);
			fileName = file.name.replace(/\.(mid|midi)$/i, '');
			fileDuration = dur;

			// Use a negative ID to signal PlayerBar that data is pre-loaded
			const syntheticTrack: Track = {
				id: -1,
				composer: 'Local file',
				title: fileName,
				split: '',
				year: 0,
				midi_filename: file.name,
				audio_filename: '',
				duration: dur,
				duration_formatted: formatDuration(dur),
				composer_slug: '',
				round: null,
				session: null,
				piece_index: null,
			};

			queue.set([]);
			currentTrack.set(syntheticTrack);
		} catch (e) {
			error = 'Could not parse this MIDI file. Make sure it is a valid Standard MIDI file.';
			console.error('MIDI parse error:', e);
		}
	}

	function onDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const file = e.dataTransfer?.files[0];
		if (file) handleFile(file);
	}

	function onDragOver(e: DragEvent) {
		e.preventDefault();
		dragOver = true;
	}

	function onDragLeave() {
		dragOver = false;
	}

	function onFileInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) handleFile(file);
		input.value = '';
	}
</script>

<svelte:head>
	<title>MIDI Player — maestroMIDIplayer</title>
</svelte:head>

<article class="max-w-2xl mx-auto">
	<h1 class="text-3xl font-bold text-surface-900 dark:text-surface-100 mb-2">MIDI Player</h1>
	<p class="text-surface-500 dark:text-surface-400 mb-8">
		Drop any MIDI file to play it on your connected piano. Everything happens in the browser — nothing is uploaded.
	</p>

	<!-- Drop zone -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="relative border-2 border-dashed rounded-2xl p-12 text-center transition-colors cursor-pointer
			   {dragOver
				? 'border-accent-500 bg-accent-500/5'
				: 'border-surface-300 dark:border-surface-700 hover:border-surface-400 dark:hover:border-surface-600'}"
		ondrop={onDrop}
		ondragover={onDragOver}
		ondragleave={onDragLeave}
		onclick={() => fileInputEl.click()}
	>
		<input
			bind:this={fileInputEl}
			type="file"
			accept=".mid,.midi"
			class="hidden"
			onchange={onFileInput}
		/>

		<div class="flex flex-col items-center gap-4">
			<div class="w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-800 flex items-center justify-center
						{dragOver ? 'text-accent-500' : 'text-surface-400'}">
				<svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round"
						  d="M9 8.25H7.5a2.25 2.25 0 0 0-2.25 2.25v9a2.25 2.25 0 0 0 2.25 2.25h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25H15m0-3-3-3m0 0-3 3m3-3V15" />
				</svg>
			</div>
			<div>
				<p class="text-sm font-medium text-surface-700 dark:text-surface-300">
					{dragOver ? 'Drop it here' : 'Drag & drop a MIDI file'}
				</p>
				<p class="text-xs text-surface-400 mt-1">
					or click to browse — .mid / .midi
				</p>
			</div>
		</div>
	</div>

	{#if error}
		<p class="mt-4 text-sm text-red-500">{error}</p>
	{/if}

	{#if fileName}
		<div class="mt-6 p-4 rounded-xl bg-surface-100 dark:bg-surface-800/50
					border border-surface-200 dark:border-surface-700">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-lg bg-accent-500/15 flex items-center justify-center text-accent-500 shrink-0">
					<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
				</div>
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-surface-900 dark:text-surface-100 truncate">{fileName}</p>
					<p class="text-xs text-surface-500 dark:text-surface-400">{formatDuration(fileDuration)}</p>
				</div>
			</div>
		</div>
	{/if}
</article>
