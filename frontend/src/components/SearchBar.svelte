<script lang="ts">
	import { getTracks } from '$lib/api';
	import type { Track } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { tick } from 'svelte';

	let { size = 'sm' }: { size?: 'sm' | 'lg' } = $props();

	let query = $state('');
	let results = $state<Track[]>([]);
	let open = $state(false);
	let searchError = $state(false);
	let selectedIndex = $state(-1);
	let timer: ReturnType<typeof setTimeout>;
	let containerEl: HTMLDivElement;
	let dropdownStyle = $state('');

	function onInput() {
		clearTimeout(timer);
		selectedIndex = -1;
		searchError = false;
		if (query.length < 2) {
			results = [];
			open = false;
			return;
		}
		timer = setTimeout(async () => {
			try {
				const data = await getTracks({ q: query, limit: 8 });
				results = data.items;
				open = results.length > 0 || searchError;
				selectedIndex = -1;
				if (open) {
					await tick();
					updateDropdownPosition();
				}
			} catch {
				results = [];
				searchError = true;
				open = true;
				await tick();
				updateDropdownPosition();
			}
		}, 400);
	}

	function updateDropdownPosition() {
		if (!containerEl) return;
		const rect = containerEl.getBoundingClientRect();
		dropdownStyle = `top: ${rect.bottom + 8}px; left: ${rect.left}px; min-width: ${Math.max(rect.width, 320)}px;`;
	}

	function select(track: Track) {
		open = false;
		query = '';
		results = [];
		selectedIndex = -1;
		goto(`/composer/${track.composer_slug}#track-${track.id}`);
	}

	function onKeydown(e: KeyboardEvent) {
		if (!open || results.length === 0) return;

		if (e.key === 'ArrowDown') {
			e.preventDefault();
			selectedIndex = (selectedIndex + 1) % results.length;
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			selectedIndex = selectedIndex <= 0 ? results.length - 1 : selectedIndex - 1;
		} else if (e.key === 'Enter' && selectedIndex >= 0) {
			e.preventDefault();
			select(results[selectedIndex]);
		} else if (e.key === 'Escape') {
			open = false;
			selectedIndex = -1;
		}
	}

	function onBlur(e: FocusEvent) {
		const related = e.relatedTarget as HTMLElement | null;
		if (related?.closest('.search-results')) return;
		open = false;
		selectedIndex = -1;
	}
</script>

<div class="relative" bind:this={containerEl}>
	<div class="flex items-center gap-2 rounded-xl
				bg-surface-100 dark:bg-surface-800
				border border-surface-200 dark:border-surface-700
				focus-within:border-accent-500 transition-colors
				{size === 'lg' ? 'px-4 py-3' : 'px-3 py-2'}">
		<svg class="shrink-0 text-surface-400 {size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
			<circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
		</svg>
		<input
			type="text"
			bind:value={query}
			oninput={onInput}
			onkeydown={onKeydown}
			onfocusout={onBlur}
			placeholder="Search composers & pieces..."
			class="bg-transparent border-none outline-none w-full
				   text-surface-900 dark:text-surface-100
				   placeholder:text-surface-400
				   {size === 'lg' ? 'text-base' : 'text-sm'}"
			role="combobox"
			aria-expanded={open}
			aria-autocomplete="list"
		/>
	</div>

	{#if open}
		<div class="search-results fixed z-[100]
					bg-surface-50 dark:bg-surface-850
					border border-surface-200 dark:border-surface-700
					rounded-xl shadow-xl overflow-hidden"
			 style={dropdownStyle}
			 role="listbox">
			{#if searchError}
				<div class="px-4 py-3 text-sm text-surface-500 dark:text-surface-400">
					Search unavailable. Please try again.
				</div>
			{:else}
				{#each results as track, i}
					<button
						class="w-full text-left px-4 py-2.5
							   transition-colors flex items-center gap-3
							   {i === selectedIndex
								? 'bg-surface-100 dark:bg-surface-700'
								: 'hover:bg-surface-100 dark:hover:bg-surface-700'}"
						onclick={() => select(track)}
						tabindex="-1"
						role="option"
						aria-selected={i === selectedIndex}
					>
						<div class="min-w-0 flex-1">
							<p class="text-sm font-medium text-surface-900 dark:text-surface-100 truncate">{track.title}</p>
							<p class="text-xs text-surface-500 dark:text-surface-400">{track.composer} · {track.year}</p>
						</div>
						<span class="text-xs text-surface-400 tabular-nums shrink-0">{track.duration_formatted}</span>
					</button>
				{/each}
			{/if}
		</div>
	{/if}
</div>
