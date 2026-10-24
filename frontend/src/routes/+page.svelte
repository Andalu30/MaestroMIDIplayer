<script lang="ts">
	import { onMount } from 'svelte';
	import { resolve } from '$app/paths';
	import { getComposers, getCompetitions, getRandomTrack } from '#lib/api.js';
	import { recentlyPlayed, toasts } from '#lib/stores.js';
	import { playList } from '#lib/playback.js';
	import TrackList from '../components/TrackList.svelte';
	import type { Composer, CompetitionSummary } from '#lib/stores.js';
	import ComposerCard from '../components/ComposerCard.svelte';
	import CompetitionCard from '../components/CompetitionCard.svelte';
	import SearchBar from '../components/SearchBar.svelte';
	import LoadError from '../components/LoadError.svelte';

	let composers = $state<Composer[]>([]);
	let competitions = $state<CompetitionSummary[]>([]);
	let loading = $state(true);
	let failed = $state(false);

	async function load() {
		loading = true;
		failed = false;
		try {
			const [c, comp] = await Promise.all([getComposers(), getCompetitions()]);
			composers = c;
			competitions = comp;
		} catch {
			failed = true;
		} finally {
			loading = false;
		}
	}

	onMount(load);

	async function surpriseMe() {
		try {
			const track = await getRandomTrack();
			playList([track]);
			toasts.show(`${track.composer} — ${track.title}`, 4000);
		} catch {
			toasts.show('Could not pick a piece. Is the server reachable?');
		}
	}
</script>

<svelte:head>
	<title>MaestroMIDIplayer</title>
</svelte:head>

<!-- Hero -->
<section class="relative py-10 sm:py-16 mb-8 sm:mb-12 text-center">

	<div class="relative z-10">
		<h1 class="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight mb-3">
			<span class="text-accent-500">MaestroMIDIplayer</span>
		</h1>
		<p class="text-base sm:text-lg text-surface-500 dark:text-surface-400 max-w-xl mx-auto">
			1,276 piano masterworks from the <br class="hidden sm:inline">International Piano-e-Competition
		</p>
		{#if !loading && !failed}
			<div class="flex items-center justify-center gap-6 mt-4 text-sm text-surface-400">
				<span>{composers.length} composers</span>
				<span class="w-1 h-1 rounded-full bg-surface-300 dark:bg-surface-600"></span>
				<span>{competitions.length} competition years</span>
			</div>
		{/if}
		<div class="mt-6 max-w-md mx-auto">
			<SearchBar size="lg" />
		</div>
		<button
			onclick={surpriseMe}
			class="mt-4 inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm
				   border border-surface-300 dark:border-surface-700 text-surface-600 dark:text-surface-300
				   hover:border-accent-500 hover:text-accent-500 transition-colors"
		>
			<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.2" fill="currentColor"/><circle cx="16" cy="16" r="1.2" fill="currentColor"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/>
			</svg>
			Surprise me
		</button>
	</div>
</section>

{#if loading}
	<div class="flex justify-center py-20">
		<div class="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin"></div>
	</div>
{:else if failed}
	<LoadError onretry={load} />
{:else}
	{#if $recentlyPlayed.length > 0}
		<section class="mb-14">
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-lg font-semibold text-surface-700 dark:text-surface-300">Recently played</h2>
				<a href={resolve('/library')} class="text-sm text-accent-500 hover:underline">Library</a>
			</div>
			<TrackList tracks={$recentlyPlayed.slice(0, 5)} showComposer={true} keepOrder={true} />
		</section>
	{/if}

	<!-- Composers -->
	<section class="mb-14">
		<div class="flex items-center justify-between mb-5">
			<h2 class="text-lg font-semibold text-surface-700 dark:text-surface-300">Composers</h2>
			<a href={resolve('/composers')} class="text-sm text-accent-500 hover:underline">View all {composers.length}</a>
		</div>
		<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
			{#each composers.slice(0, 12) as composer (composer.slug)}
				<ComposerCard {composer} />
			{/each}
		</div>
	</section>

	<!-- Competitions -->
	<section class="mb-14">
		<h2 class="text-lg font-semibold mb-5 text-surface-700 dark:text-surface-300">Competitions</h2>
		<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
			{#each competitions as competition (competition.year)}
				<CompetitionCard {competition} />
			{/each}
		</div>
	</section>
{/if}
