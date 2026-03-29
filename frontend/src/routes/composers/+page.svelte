<script lang="ts">
	import { onMount } from 'svelte';
	import { getComposers } from '$lib/api';
	import type { Composer } from '$lib/stores';
	import ComposerCard from '../../components/ComposerCard.svelte';

	let composers = $state<Composer[]>([]);
	let loading = $state(true);

	onMount(async () => {
		composers = await getComposers();
		loading = false;
	});
</script>

<svelte:head>
	<title>Composers — maestroMIDIplayer</title>
</svelte:head>

<section>
	<div class="flex items-center justify-between mb-6">
		<h1 class="text-2xl font-bold text-surface-900 dark:text-surface-100">Composers</h1>
		{#if !loading}
			<span class="text-sm text-surface-400">{composers.length} composers</span>
		{/if}
	</div>

	{#if loading}
		<div class="flex justify-center py-20">
			<div class="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin"></div>
		</div>
	{:else}
		<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
			{#each composers as composer (composer.slug)}
				<ComposerCard {composer} />
			{/each}
		</div>
	{/if}
</section>
