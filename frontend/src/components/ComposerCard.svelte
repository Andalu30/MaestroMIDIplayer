<script lang="ts">
	import type { Composer } from '$lib/stores';
	import { composerImageUrl } from '$lib/api';

	let { composer }: { composer: Composer } = $props();

	let imgError = $state(false);

	function initials(name: string): string {
		return name.split(' ').map(w => w[0]).filter(Boolean).slice(0, 2).join('').toUpperCase();
	}
</script>

<a
	href="/composer/{composer.slug}"
	class="group flex flex-col items-center gap-3 p-4 rounded-2xl
		   bg-surface-100 dark:bg-surface-850
		   hover:bg-surface-200 dark:hover:bg-surface-700
		   transition-colors cursor-pointer min-w-[140px]"
>
	<div class="relative w-24 h-24 rounded-full overflow-hidden bg-surface-300 dark:bg-surface-700 shrink-0">
		{#if !imgError}
			<img
				src={composerImageUrl(composer.slug)}
				alt={composer.name}
				loading="lazy"
				class="w-full h-full object-cover"
				onerror={() => imgError = true}
			/>
		{:else}
			<div class="w-full h-full flex items-center justify-center text-2xl font-serif text-surface-500 dark:text-surface-400">
				{initials(composer.name)}
			</div>
		{/if}
	</div>
	<div class="text-center">
		<p class="font-medium text-sm text-surface-900 dark:text-surface-100 group-hover:text-accent-500 transition-colors">
			{composer.name}
		</p>
		<p class="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
			{composer.track_count} {composer.track_count === 1 ? 'piece' : 'pieces'}
		</p>
	</div>
</a>
