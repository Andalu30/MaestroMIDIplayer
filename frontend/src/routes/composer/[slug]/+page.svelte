<script lang="ts">
	import { page } from '$app/state';
	import { tick } from 'svelte';
	import { getComposer, getComposerTracks, composerImageUrl } from '$lib/api';
	import { currentTrack, queue, toasts } from '$lib/stores';
	import type { Composer, Track } from '$lib/stores';
	import { formatTotalDuration } from '$lib/utils';
	import TrackList from '../../../components/TrackList.svelte';

	let composer = $state<Composer | null>(null);
	let tracks = $state<Track[]>([]);
	let loading = $state(true);
	let imgError = $state(false);
	let error = $state<string | null>(null);

	const slug = $derived(page.params.slug);

	$effect(() => {
		const currentSlug = slug; // track dependency
		loading = true;
		imgError = false;
		error = null;

		Promise.all([
			getComposer(currentSlug),
			getComposerTracks(currentSlug)
		]).then(async ([c, t]) => {
			composer = c;
			tracks = t;
			loading = false;

			// Scroll to track if hash is present (e.g. from search).
			// Validate the hash strictly: only allow #track-{integer} format.
			const hashMatch = window.location.hash.match(/^#track-(\d+)$/);
			if (hashMatch) {
				await tick();
				const el = document.getElementById(`track-${hashMatch[1]}`);
				if (el) {
					el.scrollIntoView({ behavior: 'smooth', block: 'center' });
					el.classList.add('search-highlight');
					setTimeout(() => el.classList.remove('search-highlight'), 2000);
				}
			}
		}).catch((e: Error) => {
			error = e.message.includes('404') ? 'Composer not found.' : 'Failed to load composer. Please try again.';
			loading = false;
		});
	});

	function initials(name: string): string {
		return name.split(' ').map(w => w[0]).filter(Boolean).slice(0, 2).join('').toUpperCase();
	}

	function playAll() {
		if (tracks.length > 0) {
			currentTrack.set(tracks[0]);
			queue.set(tracks.slice(1));
			toasts.show(`Queued ${tracks.length} track${tracks.length === 1 ? '' : 's'}`);
		}
	}
</script>

<svelte:head>
	<title>{composer?.name ?? 'Composer'} — Maestro</title>
</svelte:head>

{#if loading}
	<!-- Skeleton screen -->
	<section class="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-10 animate-pulse">
		<div class="w-32 h-32 rounded-full bg-surface-200 dark:bg-surface-700 shrink-0"></div>
		<div class="flex-1 space-y-3">
			<div class="h-8 w-48 bg-surface-200 dark:bg-surface-700 rounded"></div>
			<div class="h-4 w-32 bg-surface-200 dark:bg-surface-700 rounded"></div>
			<div class="h-9 w-28 bg-surface-200 dark:bg-surface-700 rounded-full"></div>
		</div>
	</section>
	<div class="space-y-2 animate-pulse">
		{#each Array(8) as _}
			<div class="h-12 bg-surface-200 dark:bg-surface-700 rounded-lg"></div>
		{/each}
	</div>
{:else if error}
	<div class="flex flex-col items-center py-20 text-surface-500 dark:text-surface-400">
		<p class="text-lg font-medium">{error}</p>
	</div>
{:else if composer}
	<!-- Header -->
	<section class="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-10">
		<div class="w-32 h-32 rounded-full overflow-hidden bg-surface-300 dark:bg-surface-700 shrink-0">
			{#if !imgError}
				<img
					src={composerImageUrl(composer.slug)}
					alt={composer.name}
					class="w-full h-full object-cover"
					onerror={() => imgError = true}
				/>
			{:else}
				<div class="w-full h-full flex items-center justify-center text-4xl font-serif text-surface-500 dark:text-surface-400">
					{initials(composer.name)}
				</div>
			{/if}
		</div>
		<div class="text-center sm:text-left">
			<h1 class="text-3xl font-bold text-surface-900 dark:text-surface-100">
				{composer.name}
			</h1>
			<p class="text-surface-500 dark:text-surface-400 mt-1">
				{composer.track_count} {composer.track_count === 1 ? 'piece' : 'pieces'} · {composer.total_duration_formatted}
			</p>
			<button
				onclick={playAll}
				class="mt-4 inline-flex items-center gap-2 px-5 py-2 rounded-full
					   bg-accent-500 hover:bg-accent-600 text-white text-sm font-medium
					   transition-colors"
			>
				<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
				Play All
			</button>
		</div>
	</section>

	<!-- Track list -->
	<section>
		<TrackList {tracks} showYear={true} allowGrouping={true} />
	</section>
{/if}
