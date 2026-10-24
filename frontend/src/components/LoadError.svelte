<script lang="ts">
	let { message = 'Could not load the library. Is the server reachable?', onretry }: {
		message?: string;
		onretry: () => void;
	} = $props();
</script>

<div class="flex flex-col items-center gap-4 py-20 text-surface-500 dark:text-surface-400" role="alert">
	<p class="text-base">{message}</p>
	<button
		onclick={onretry}
		class="px-4 py-1.5 rounded-full text-sm border border-surface-300 dark:border-surface-600
			   hover:border-accent-500 hover:text-accent-500 transition-colors"
	>Retry</button>
</div>
