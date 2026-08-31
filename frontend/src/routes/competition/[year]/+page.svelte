<script lang="ts">
	import { page } from '$app/state';
	import { getCompetition } from '$lib/api';
	import { currentTrack, queue } from '$lib/stores';
	import type { CompetitionYear, Track } from '$lib/stores';
	import { formatTotalDuration } from '$lib/utils';
	import TrackList from '../../../components/TrackList.svelte';

	let competition = $state<CompetitionYear | null>(null);
	let loading = $state(true);
	let expandedRounds = $state<Set<number>>(new Set());

	const year = $derived(Number(page.params.year));
	const yearIsValid = $derived(Number.isInteger(year) && year >= 2000 && year <= 2030);

	$effect(() => {
		const currentYear = year; // track dependency
		loading = true;

		if (!yearIsValid) {
			loading = false;
			return;
		}

		getCompetition(currentYear).then((comp) => {
			competition = comp;
			if (competition) {
				expandedRounds = new Set(competition.rounds.map((_, i) => i));
			}
			loading = false;
		});
	});

	function allTracks(): Track[] {
		if (!competition) return [];
		return competition.rounds.flatMap(r => r.sessions.flatMap(s => s.tracks));
	}

	function roundTracks(roundIndex: number): Track[] {
		if (!competition) return [];
		return competition.rounds[roundIndex].sessions.flatMap(s => s.tracks);
	}

	function playAll() {
		const tracks = allTracks();
		if (tracks.length > 0) {
			currentTrack.set(tracks[0]);
			queue.set(tracks.slice(1));
		}
	}

	function playRound(roundIndex: number) {
		const tracks = roundTracks(roundIndex);
		if (tracks.length > 0) {
			currentTrack.set(tracks[0]);
			queue.set(tracks.slice(1));
		}
	}

	function toggleRound(index: number) {
		const next = new Set(expandedRounds);
		if (next.has(index)) {
			next.delete(index);
		} else {
			next.add(index);
		}
		expandedRounds = next;
	}

	function roundDuration(roundIndex: number): number {
		return roundTracks(roundIndex).reduce((sum, t) => sum + t.duration, 0);
	}

	const roundLabels: Record<number, string> = { 1: 'Round 1', 2: 'Round 2', 3: 'Round 3' };
</script>

<svelte:head>
	<title>Competition {year} — Maestro</title>
</svelte:head>

{#if !yearIsValid}
	<div class="flex flex-col items-center py-20 text-surface-500 dark:text-surface-400">
		<p class="text-lg font-medium">Invalid competition year</p>
		<p class="text-sm mt-1">"{page.params.year}" is not a valid year.</p>
	</div>
{:else if loading}
	<div class="flex justify-center py-20">
		<div class="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin"></div>
	</div>
{:else if competition}
	<!-- Header -->
	<section class="mb-10">
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
			<div>
				<h1 class="text-3xl font-bold text-surface-900 dark:text-surface-100">
					<span class="text-accent-500">{competition.year}</span> Competition
				</h1>
				<p class="text-surface-500 dark:text-surface-400 mt-1">
					{competition.track_count} performances · {competition.rounds.length} {competition.rounds.length === 1 ? 'round' : 'rounds'} · {formatTotalDuration(allTracks().reduce((s, t) => s + t.duration, 0))}
				</p>
			</div>
			<button
				onclick={playAll}
				class="inline-flex items-center gap-2 px-5 py-2 rounded-full
					   bg-accent-500 hover:bg-accent-600 text-white text-sm font-medium
					   transition-colors self-start"
			>
				<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
				Play All
			</button>
		</div>
	</section>

	<!-- Rounds -->
	{#each competition.rounds as round, ri (round.round ?? ri)}
		<section class="mb-6">
			<!-- Round header -->
			<div class="flex items-center gap-3 mb-3">
				<button
					onclick={() => toggleRound(ri)}
					class="flex items-center gap-2 group"
				>
					<svg
						class="w-4 h-4 text-surface-400 transition-transform {expandedRounds.has(ri) ? 'rotate-90' : ''}"
						fill="currentColor" viewBox="0 0 24 24"
					>
						<path d="M8 5v14l11-7z"/>
					</svg>
					<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 group-hover:text-accent-500 transition-colors">
						{roundLabels[round.round ?? 0] ?? `Round ${round.round}`}
					</h2>
				</button>
				<span class="text-sm text-surface-400">
					{round.track_count} {round.track_count === 1 ? 'piece' : 'pieces'} · {formatTotalDuration(roundDuration(ri))}
				</span>
				<button
					onclick={() => playRound(ri)}
					class="ml-auto text-xs px-3 py-1 rounded-full
						   border border-accent-500/50 text-accent-500
						   hover:bg-accent-500/10 transition-colors"
				>
					Play Round
				</button>
			</div>

			{#if expandedRounds.has(ri)}
				<!-- Sessions within round -->
				{#each round.sessions as session, si (session.session ?? si)}
					{#if round.sessions.length > 1}
						<div class="ml-4 mb-4">
							<h3 class="text-sm font-medium text-surface-500 dark:text-surface-400 mb-2 ml-4">
								Session {session.session ?? si + 1}
							</h3>
							<TrackList tracks={session.tracks} showComposer={true} />
						</div>
					{:else}
						<div class="ml-4 mb-4">
							<TrackList tracks={session.tracks} showComposer={true} />
						</div>
					{/if}
				{/each}
			{/if}
		</section>
	{/each}
{:else}
	<div class="flex flex-col items-center py-20 text-surface-500 dark:text-surface-400">
		<p class="text-lg font-medium">Competition not found</p>
		<p class="text-sm mt-1">No competition data found for year {year}.</p>
	</div>
