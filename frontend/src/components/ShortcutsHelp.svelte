<script lang="ts">
	let { open = false, onclose }: { open: boolean; onclose: () => void } = $props();

	const shortcuts: [string[], string][] = [
		[['Space'], 'Play / pause'],
		[['←', '→'], 'Seek 5 seconds'],
		[['N'], 'Next track'],
		[['P'], 'Previous track (or restart)'],
		[['[', ']'], 'Tempo − / +'],
		[['\\'], 'Reset tempo'],
		[['R'], 'Repeat: off → queue → track'],
		[['?'], 'Show / hide this help'],
	];
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="fixed inset-0 z-[70] bg-black/40 backdrop-blur-sm flex items-center justify-center"
		onclick={(e) => { if (e.target === e.currentTarget) onclose(); }}
		onkeydown={(e) => { if (e.key === 'Escape') onclose(); }}
		role="dialog"
		aria-modal="true"
		aria-label="Keyboard shortcuts"
		tabindex="-1"
	>
		<div class="bg-surface-50 dark:bg-surface-900 rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-lg font-semibold text-surface-900 dark:text-surface-100">Keyboard shortcuts</h2>
				<button onclick={onclose} aria-label="Close"
					class="p-1.5 rounded-full hover:bg-surface-200 dark:hover:bg-surface-700 text-surface-500">
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M6 18L18 6M6 6l12 12"/></svg>
				</button>
			</div>
			<dl class="space-y-2">
				{#each shortcuts as [keys, label] (label)}
					<div class="flex items-center justify-between gap-4">
						<dt class="flex gap-1">
							{#each keys as key (key)}
								<kbd class="min-w-7 px-1.5 py-0.5 text-center text-xs font-mono rounded-md
											bg-surface-200 dark:bg-surface-800 border border-surface-300 dark:border-surface-700
											text-surface-700 dark:text-surface-300">{key}</kbd>
							{/each}
						</dt>
						<dd class="text-sm text-surface-600 dark:text-surface-400 text-right">{label}</dd>
					</div>
				{/each}
			</dl>
			<p class="mt-4 text-xs text-surface-400">Media keys and headset buttons also work while a piece is playing.</p>
		</div>
	</div>
{/if}
