<script lang="ts">
	import type { Track } from '$lib/stores';
	import { currentTrack, queue } from '$lib/stores';
	import { formatDuration } from '$lib/utils';

	interface TrackGroup {
		title: string;
		tracks: Track[];
		isMulti: boolean;
		avgDuration: string;
	}

	let { tracks, showComposer = false, showYear = false, allowGrouping = false }: {
		tracks: Track[];
		showComposer?: boolean;
		showYear?: boolean;
		allowGrouping?: boolean;
	} = $props();

	let sortField = $state<'title' | 'duration' | 'year' | 'composer'>('title');
	let sortAsc = $state(true);
	let viewMode = $state<'grouped' | 'flat'>(allowGrouping ? 'grouped' : 'flat');
	let expandedGroups = $state<Set<string>>(new Set());

	let sorted = $derived.by(() => {
		const copy = [...tracks];
		copy.sort((a, b) => {
			let cmp: number;
			switch (sortField) {
				case 'title': cmp = a.title.localeCompare(b.title); break;
				case 'duration': cmp = a.duration - b.duration; break;
				case 'year': cmp = a.year - b.year; break;
				case 'composer': cmp = a.composer.localeCompare(b.composer); break;
				default: cmp = 0;
			}
			return sortAsc ? cmp : -cmp;
		});
		return copy;
	});

	let groups = $derived.by(() => {
		const map = new Map<string, Track[]>();
		for (const track of tracks) {
			const existing = map.get(track.title);
			if (existing) {
				existing.push(track);
			} else {
				map.set(track.title, [track]);
			}
		}

		const result: TrackGroup[] = [];
		for (const [title, groupTracks] of map) {
			groupTracks.sort((a, b) => a.year - b.year);
			const avg = groupTracks.reduce((sum, t) => sum + t.duration, 0) / groupTracks.length;
			result.push({
				title,
				tracks: groupTracks,
				isMulti: groupTracks.length > 1,
				avgDuration: `~${formatDuration(Math.round(avg))}`,
			});
		}

		result.sort((a, b) => a.title.localeCompare(b.title));
		return result;
	});

	let flatFromGroups = $derived.by(() => {
		return groups.flatMap(g => g.tracks);
	});

	// Auto-expand group when navigating via hash (e.g. from search)
	$effect(() => {
		if (viewMode !== 'grouped') return;
		const hash = typeof window !== 'undefined' ? window.location.hash : '';
		if (!hash.startsWith('#track-')) return;
		const targetId = parseInt(hash.slice(7), 10);
		if (isNaN(targetId)) return;

		for (const group of groups) {
			if (group.isMulti && group.tracks.some(t => t.id === targetId)) {
				if (!expandedGroups.has(group.title)) {
					expandedGroups = new Set([...expandedGroups, group.title]);
				}
				break;
			}
		}
	});

	function toggleSort(field: typeof sortField) {
		if (sortField === field) {
			sortAsc = !sortAsc;
		} else {
			sortField = field;
			sortAsc = true;
		}
	}

	function playTrack(track: Track) {
		currentTrack.set(track);
		const source = viewMode === 'grouped' ? flatFromGroups : sorted;
		const index = source.findIndex(t => t.id === track.id);
		queue.set(index >= 0 ? source.slice(index + 1) : []);
	}

	function playGroup(group: TrackGroup) {
		// Play the latest performance (highest year)
		const latest = group.tracks[group.tracks.length - 1];
		playTrack(latest);
	}

	function toggleGroup(title: string) {
		const next = new Set(expandedGroups);
		if (next.has(title)) {
			next.delete(title);
		} else {
			next.add(title);
		}
		expandedGroups = next;
	}

	function sortIndicator(field: typeof sortField): string {
		if (sortField !== field) return '';
		return sortAsc ? ' \u2191' : ' \u2193';
	}
</script>

<div class="space-y-1">
	{#if viewMode === 'grouped'}
		<!-- Grouped header -->
		<div class="flex items-center gap-4 px-4 py-2 text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wide">
			<span class="w-8 shrink-0"></span>
			<span class="flex-1">Piece</span>
			<span class="w-16 shrink-0 text-right">Time</span>
		</div>

		<!-- Grouped rows -->
		{#each groups as group (group.title)}
			{#if group.isMulti}
				<!-- Multi-performance group header -->
				<div class="flex items-center gap-4 px-4 py-2.5 rounded-lg
						   transition-colors hover:bg-surface-100 dark:hover:bg-surface-850">
					<button
						class="w-8 shrink-0 flex items-center justify-center text-surface-400"
						onclick={() => toggleGroup(group.title)}
						aria-label="{expandedGroups.has(group.title) ? 'Collapse' : 'Expand'} {group.title}"
					>
						<svg class="w-3.5 h-3.5 transition-transform {expandedGroups.has(group.title) ? 'rotate-90' : ''}"
							 fill="currentColor" viewBox="0 0 24 24">
							<path d="M8 5v14l11-7z"/>
						</svg>
					</button>
					<button
						class="flex-1 min-w-0 flex items-center gap-2 text-left"
						onclick={() => playGroup(group)}
					>
						<p class="text-sm truncate text-surface-900 dark:text-surface-100">
							{group.title}
						</p>
						<span class="text-[10px] px-1.5 py-0.5 rounded-full
									 bg-accent-500/15 text-accent-500
									 tabular-nums shrink-0 font-medium">
							&times;{group.tracks.length}
						</span>
					</button>
					<span class="w-16 shrink-0 text-sm text-surface-500 dark:text-surface-400 tabular-nums text-right">
						{group.avgDuration}
					</span>
				</div>

				<!-- Expanded sub-rows -->
				{#if expandedGroups.has(group.title)}
					{#each group.tracks as track (track.id)}
						{@const isPlaying = $currentTrack?.id === track.id}
						<button
							id="track-{track.id}"
							class="w-full flex items-center gap-4 pl-12 pr-4 py-2 rounded-lg
								   text-left transition-colors
								   {isPlaying
									? 'bg-accent-500/10 dark:bg-accent-500/15'
									: 'hover:bg-surface-100 dark:hover:bg-surface-850'}"
							onclick={() => playTrack(track)}
						>
							<span class="w-8 shrink-0 text-sm tabular-nums {isPlaying ? 'text-accent-500 font-medium' : 'text-surface-400'}">
								{#if isPlaying}
									<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
								{:else}
									{track.year}
								{/if}
							</span>
							<div class="flex-1 min-w-0">
								<p class="text-xs text-surface-500 dark:text-surface-400 truncate">
									{track.year} performance{#if track.round} · Round {track.round}{/if}
								</p>
							</div>
							<span class="w-16 shrink-0 text-sm text-surface-500 dark:text-surface-400 tabular-nums text-right">
								{track.duration_formatted}
							</span>
						</button>
					{/each}
				{/if}
			{:else}
				<!-- Single-performance row -->
				{@const track = group.tracks[0]}
				{@const isPlaying = $currentTrack?.id === track.id}
				<button
					id="track-{track.id}"
					class="w-full flex items-center gap-4 px-4 py-2.5 rounded-lg text-left
						   transition-colors group
						   {isPlaying
							? 'bg-accent-500/10 dark:bg-accent-500/15'
							: 'hover:bg-surface-100 dark:hover:bg-surface-850'}"
					onclick={() => playTrack(track)}
				>
					<span class="w-8 shrink-0 text-sm {isPlaying ? 'text-accent-500 font-medium' : 'text-surface-300 dark:text-surface-600'} flex items-center justify-center">
						{#if isPlaying}
							<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
						{:else}
							·
						{/if}
					</span>
					<div class="flex-1 min-w-0">
						<p class="text-sm truncate {isPlaying ? 'text-accent-500 font-medium' : 'text-surface-900 dark:text-surface-100'}">
							{track.title}
						</p>
						<p class="text-xs text-surface-500 dark:text-surface-400">
							{track.year}{#if track.round} · Round {track.round}{/if}
						</p>
					</div>
					<span class="w-16 shrink-0 text-sm text-surface-500 dark:text-surface-400 tabular-nums text-right">
						{track.duration_formatted}
					</span>
				</button>
			{/if}
		{/each}
	{:else}
		<!-- Flat view: sort header -->
		<div class="flex items-center gap-4 px-4 py-2 text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wide">
			<span class="w-8 shrink-0">#</span>
			<button class="flex-1 text-left hover:text-accent-500 transition-colors" onclick={() => toggleSort('title')}>
				Title{sortIndicator('title')}
			</button>
			{#if showComposer}
				<button class="w-40 shrink-0 text-left hover:text-accent-500 transition-colors hidden sm:block" onclick={() => toggleSort('composer')}>
					Composer{sortIndicator('composer')}
				</button>
			{/if}
			{#if showYear}
				<button class="w-16 shrink-0 text-left hover:text-accent-500 transition-colors hidden md:block" onclick={() => toggleSort('year')}>
					Year{sortIndicator('year')}
				</button>
			{/if}
			<button class="w-16 shrink-0 text-right hover:text-accent-500 transition-colors" onclick={() => toggleSort('duration')}>
				Time{sortIndicator('duration')}
			</button>
		</div>

		<!-- Flat view: track rows -->
		{#each sorted as track, i (track.id)}
			{@const isPlaying = $currentTrack?.id === track.id}
			<button
				id="track-{track.id}"
				class="w-full flex items-center gap-4 px-4 py-2.5 rounded-lg text-left
					   transition-colors group
					   {isPlaying
						? 'bg-accent-500/10 dark:bg-accent-500/15'
						: 'hover:bg-surface-100 dark:hover:bg-surface-850'}"
				onclick={() => playTrack(track)}
			>
				<span class="w-8 shrink-0 text-sm tabular-nums {isPlaying ? 'text-accent-500 font-medium' : 'text-surface-400'}">
					{#if isPlaying}
						<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
					{:else}
						{i + 1}
					{/if}
				</span>
				<div class="flex-1 min-w-0">
					<p class="text-sm truncate {isPlaying ? 'text-accent-500 font-medium' : 'text-surface-900 dark:text-surface-100'}">
						{track.title}
					</p>
					{#if showComposer}
						<p class="text-xs text-surface-500 dark:text-surface-400 truncate sm:hidden">
							{track.composer}
						</p>
					{/if}
				</div>
				{#if showComposer}
					<span class="w-40 shrink-0 text-sm text-surface-600 dark:text-surface-400 truncate hidden sm:block">
						{track.composer}
					</span>
				{/if}
				{#if showYear}
					<span class="w-16 shrink-0 text-sm text-surface-500 dark:text-surface-400 tabular-nums hidden md:block">
						{track.year}
					</span>
				{/if}
				<span class="w-16 shrink-0 text-sm text-surface-500 dark:text-surface-400 tabular-nums text-right">
					{track.duration_formatted}
				</span>
			</button>
		{/each}
	{/if}

	<!-- View mode toggle -->
	{#if allowGrouping}
		<div class="flex justify-end px-4 pt-2">
			<button
				onclick={() => viewMode = viewMode === 'grouped' ? 'flat' : 'grouped'}
				class="text-[11px] px-2.5 py-1 rounded-md
					   border border-surface-300 dark:border-surface-600
					   text-surface-500 dark:text-surface-400
					   hover:border-accent-500 hover:text-accent-500
					   transition-colors"
			>
				{viewMode === 'grouped' ? 'Show as flat list' : 'Group by piece'}
			</button>
		</div>
	{/if}
</div>
