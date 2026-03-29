<script lang="ts">
	import type { CompetitionSummary } from '$lib/stores';

	let { competition }: { competition: CompetitionSummary } = $props();

	const roundLabels: Record<number, string> = { 1: 'R1', 2: 'R2', 3: 'R3' };
</script>

<a
	href="/competition/{competition.year}"
	class="group flex flex-col gap-3 p-5 rounded-2xl
		   bg-surface-100 dark:bg-surface-850
		   hover:bg-surface-200 dark:hover:bg-surface-700
		   transition-colors cursor-pointer"
>
	<div class="flex items-baseline gap-3">
		<span class="text-2xl font-bold text-accent-500">{competition.year}</span>
		<span class="text-sm text-surface-500 dark:text-surface-400">
			{competition.track_count} performances
		</span>
	</div>
	<div class="flex gap-2 flex-wrap">
		{#each competition.rounds as round}
			<span class="px-2.5 py-1 text-xs font-medium rounded-full
						 bg-surface-200 dark:bg-surface-700
						 text-surface-700 dark:text-surface-300">
				{roundLabels[round.round] || `R${round.round}`} · {round.track_count}
			</span>
		{/each}
	</div>
</a>
