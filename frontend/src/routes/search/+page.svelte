<script lang="ts">
	import { page } from '$app/state';
	import { getTracks } from '#lib/api.js';
	import type { Track } from '#lib/stores.js';
	import { playList } from '#lib/playback.js';
	import TrackList from '../../components/TrackList.svelte';
	import LoadError from '../../components/LoadError.svelte';

	const q = $derived(page.url.searchParams.get('q')?.trim() ?? '');
	const year = $derived(Number(page.url.searchParams.get('year')) || undefined);

	let tracks = $state<Track[]>([]);
	let total = $state(0);
	let loading = $state(true);
	let failed = $state(false);

	async function load(query: string, y: number | undefined) {
		loading = true;
		failed = false;
		try {
			const res = await getTracks({ q: query || undefined, year: y, limit: 500 });
			tracks = res.items;
			total = res.total;
		} catch {
			failed = true;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		load(q, year);
	});
</script>

<svelte:head>
	<title>{q ? `“${q}”` : 'Search'} — maestroMIDIplayer</title>
</svelte:head>

<section>
	<div class="flex flex-wrap items-end justify-between gap-4 mb-6">
		<div>
			<h1 class="text-2xl font-bold text-surface-900 dark:text-surface-100">
				{#if q}Results for “{q}”{:else}All performances{/if}
				{#if year}<span class="text-surface-400 font-normal"> in {year}</span>{/if}
			</h1>
			{#if !loading && !failed}
				<p class="text-sm text-surface-500 dark:text-surface-400 mt-1">
					{total} {total === 1 ? 'performance' : 'performances'}{#if total > tracks.length} (showing first {tracks.length}){/if}
				</p>
			{/if}
		</div>
		{#if tracks.length > 0}
			<button
				onclick={() => playList(tracks)}
				class="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-accent-500 hover:bg-accent-600 text-white text-sm font-medium transition-colors"
			>
				<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
				Play all
			</button>
		{/if}
	</div>

	{#if loading}
		<div class="flex justify-center py-20">
			<div class="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin"></div>
		</div>
	{:else if failed}
		<LoadError message="Search failed. Is the server reachable?" onretry={() => load(q, year)} />
	{:else if tracks.length === 0}
		<p class="py-20 text-center text-surface-500 dark:text-surface-400">No performances match. Try a composer's surname or a piece like “ballade”.</p>
	{:else}
		<TrackList {tracks} showComposer={true} showYear={true} keepOrder={true} />
	{/if}
</section>
