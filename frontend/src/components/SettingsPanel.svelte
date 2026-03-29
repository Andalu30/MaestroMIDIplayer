<script lang="ts">
	import { showPianoViz, showPedalIndicators, showPedalNames } from '$lib/stores';
	import { midiPlayer } from '$lib/midi-player';
	import { onMount } from 'svelte';

	let { open = false, onclose }: { open: boolean; onclose: () => void } = $props();

	// Client MIDI state
	let clientOutputs = $state<MIDIOutput[]>([]);
	let clientSelectedId = $state<string>('__all__');
	let midiSupported = $state(true);

	let refreshing = $state(false);

	onMount(() => {
		if (!navigator.requestMIDIAccess) {
			midiSupported = false;
		} else {
			refreshClientPorts();
		}
	});

	async function refreshClientPorts() {
		refreshing = true;
		clientOutputs = await midiPlayer.getMidiOutputs();
		const currentOutputs = midiPlayer.getOutputs();
		if (currentOutputs.length > 1) {
			clientSelectedId = '__all__';
		} else if (currentOutputs.length === 1) {
			const current = currentOutputs[0];
			if (clientOutputs.find(o => o.id === current.id)) {
				clientSelectedId = current.id;
			}
		}
		// Auto-select all outputs if nothing is selected yet
		if (clientOutputs.length > 0 && !midiPlayer.hasOutputs()) {
			selectClientPort('__all__');
		}
		refreshing = false;
	}

	function selectClientPort(id: string) {
		clientSelectedId = id;
		if (id === '__all__') {
			midiPlayer.setOutputs(clientOutputs);
		} else {
			const port = clientOutputs.find(o => o.id === id);
			midiPlayer.setOutput(port ?? null);
		}
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onclose();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="fixed inset-0 z-[60] bg-black/40 backdrop-blur-sm flex items-center justify-center"
		onclick={handleBackdropClick}
		onkeydown={handleKeydown}
		role="dialog"
		aria-modal="true"
		aria-label="Settings"
		tabindex="-1"
	>
		<div class="bg-surface-50 dark:bg-surface-900 rounded-2xl shadow-2xl
					w-full max-w-md mx-4 p-6">
			<div class="flex items-center justify-between mb-6">
				<h2 class="text-lg font-semibold text-surface-900 dark:text-surface-100">Settings</h2>
				<button onclick={onclose} aria-label="Close settings"
					class="p-1.5 rounded-full hover:bg-surface-200 dark:hover:bg-surface-700 text-surface-500">
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>

			<!-- MIDI Output -->
			<div>
				<div class="flex items-center justify-between mb-2">
					<span class="text-sm font-medium text-surface-700 dark:text-surface-300">
						MIDI Output
					</span>
					<button
						onclick={refreshClientPorts}
						class="text-xs text-accent-500 hover:underline
							   {refreshing ? 'opacity-50 pointer-events-none' : ''}"
					>
						{refreshing ? 'Scanning...' : 'Refresh'}
					</button>
				</div>

				{#if !midiSupported}
					<p class="text-sm text-red-400">
						Web MIDI API is not supported in this browser. Use Chrome or Edge.
					</p>
				{:else if clientOutputs.length === 0}
					<p class="text-sm text-surface-500 dark:text-surface-400">
						No MIDI outputs found. Connect a MIDI device and click Refresh.
					</p>
				{:else}
					<div class="space-y-1">
						{#if clientOutputs.length > 1}
							<button
								onclick={() => selectClientPort('__all__')}
								class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
									   {clientSelectedId === '__all__'
										? 'bg-accent-500/15 text-accent-500 font-medium'
										: 'text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800'}"
							>
								All Outputs
								<span class="text-xs text-surface-400 ml-1">({clientOutputs.length} devices)</span>
							</button>
						{/if}
						{#each clientOutputs as port (port.id)}
							<button
								onclick={() => selectClientPort(port.id)}
								class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
									   {clientSelectedId === port.id
										? 'bg-accent-500/15 text-accent-500 font-medium'
										: 'text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800'}"
							>
								{port.name || port.id}
								{#if port.manufacturer}
									<span class="text-xs text-surface-400 ml-1">({port.manufacturer})</span>
								{/if}
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Visualization -->
			<div class="mt-6 pt-6 border-t border-surface-200 dark:border-surface-700">
				<span class="text-sm font-medium text-surface-700 dark:text-surface-300 mb-3 block">
					Visualization
				</span>
				<div class="space-y-3">
					<label class="flex items-center justify-between cursor-pointer">
						<span class="text-sm text-surface-700 dark:text-surface-300">Piano Visualizer</span>
						<button
							onclick={() => showPianoViz.update(v => !v)}
							class="relative w-10 h-6 rounded-full transition-colors
								   {$showPianoViz ? 'bg-accent-500' : 'bg-surface-300 dark:bg-surface-600'}"
							role="switch"
							aria-checked={$showPianoViz}
						>
							<span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform
								   {$showPianoViz ? 'translate-x-4' : 'translate-x-0'}"></span>
						</button>
					</label>
					<label class="flex items-center justify-between cursor-pointer">
						<span class="text-sm text-surface-700 dark:text-surface-300">Pedal Indicators</span>
						<button
							onclick={() => showPedalIndicators.update(v => !v)}
							class="relative w-10 h-6 rounded-full transition-colors
								   {$showPedalIndicators ? 'bg-accent-500' : 'bg-surface-300 dark:bg-surface-600'}"
							role="switch"
							aria-checked={$showPedalIndicators}
						>
							<span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform
								   {$showPedalIndicators ? 'translate-x-4' : 'translate-x-0'}"></span>
						</button>
					</label>
					<label class="flex items-center justify-between cursor-pointer">
						<span class="text-sm text-surface-700 dark:text-surface-300">Pedal Names</span>
						<button
							onclick={() => showPedalNames.update(v => !v)}
							class="relative w-10 h-6 rounded-full transition-colors
								   {$showPedalNames ? 'bg-accent-500' : 'bg-surface-300 dark:bg-surface-600'}"
							role="switch"
							aria-checked={$showPedalNames}
						>
							<span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform
								   {$showPedalNames ? 'translate-x-4' : 'translate-x-0'}"></span>
						</button>
					</label>
				</div>
			</div>
		</div>
	</div>
{/if}
