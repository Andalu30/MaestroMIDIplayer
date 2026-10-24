<script lang="ts">
	import { favorites, recentlyPlayed } from '#lib/stores.js';
	import { playList } from '#lib/playback.js';
	import TrackList from '../../components/TrackList.svelte';

	let tab = $state<'favorites' | 'recent'>($favorites.length === 0 && $recentlyPlayed.length > 0 ? 'recent' : 'favorites');
	let tracks = $derived(tab === 'favorites' ? $favorites : $recentlyPlayed);
</script>

<svelte:head>
	<title>Library — maestroMIDIplayer</title>
</svelte:head>

<section>
	<div class="flex flex-wrap items-center justify-between gap-4 mb-6">
		<h1 class="text-2xl font-bold text-surface-900 dark:text-surface-100">Library</h1>
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

	<div class="flex items-center gap-2 mb-4" role="tablist">
		{#each [['favorites', `Favourites (${$favorites.length})`], ['recent', `Recently played (${$recentlyPlayed.length})`]] as [id, label] (id)}
			<button
				role="tab"
				aria-selected={tab === id}
				onclick={() => (tab = id as typeof tab)}
				class="px-3 py-1.5 rounded-full text-sm transition-colors
					   {tab === id ? 'bg-accent-500/15 text-accent-500 font-medium' : 'text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-800'}"
			>{label}</button>
		{/each}
		<div class="flex-1"></div>
		{#if tab === 'recent' && $recentlyPlayed.length > 0}
			<button onclick={() => recentlyPlayed.set([])} class="text-xs text-surface-400 hover:text-accent-500">Clear history</button>
		{/if}
	</div>

	{#if tracks.length === 0}
		<p class="py-16 text-center text-surface-500 dark:text-surface-400">
			{tab === 'favorites'
				? 'No favourites yet. Hover a track and tap the heart to keep it here.'
				: 'Nothing played yet on this browser.'}
		</p>
	{:else}
		{#key tab}
			<TrackList {tracks} showComposer={true} showYear={true} keepOrder={true} />
		{/key}
	{/if}
	<p class="mt-8 text-xs text-surface-400">Saved in this browser only.</p>
</section>
