<script lang="ts">
	import '../app.css';
	import { theme } from '$lib/stores';
	import { midiPlayer } from '$lib/midi-player';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import ThemeToggle from '../components/ThemeToggle.svelte';
	import SearchBar from '../components/SearchBar.svelte';
	import PlayerBar from '../components/PlayerBar.svelte';
	import SettingsPanel from '../components/SettingsPanel.svelte';

	let { children } = $props();
	let settingsOpen = $state(false);
	let mobileMenuOpen = $state(false);
	let hasMidiOutputs = $state(true); // assume true until checked

	let isHome = $derived(page.url.pathname === '/');

	// Close mobile menu on navigation
	$effect(() => {
		page.url.pathname;
		mobileMenuOpen = false;
	});

	onMount(async () => {
		theme.init();
		// Check if MIDI outputs are available
		if (!navigator.requestMIDIAccess) {
			hasMidiOutputs = false;
		} else {
			const outputs = await midiPlayer.getMidiOutputs();
			hasMidiOutputs = outputs.length > 0;
		}
	});
</script>

<div class="min-h-screen overflow-x-hidden bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 transition-colors">
	<!-- Top nav -->
	<header class="sticky top-0 z-40 bg-surface-50/90 dark:bg-surface-950/90 backdrop-blur-sm
					border-b border-surface-200 dark:border-surface-800">
		<nav class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-3">
			<a href="/" class="flex items-center gap-2 shrink-0">
				<span class="text-xl font-bold tracking-wider text-accent-500">MMp</span>
			</a>

			<!-- Desktop nav links -->
			<div class="hidden md:flex items-center gap-1 ml-1">
				<a href="/"
					class="px-3 py-1.5 rounded-lg text-sm transition-colors
						   {page.url.pathname === '/'
							? 'text-accent-500 font-medium'
							: 'text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-100'}"
				>Home</a>
				<a href="/player"
					class="px-3 py-1.5 rounded-lg text-sm transition-colors
						   {page.url.pathname === '/player'
							? 'text-accent-500 font-medium'
							: 'text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-100'}"
				>Standalone Player</a>
				<a href="/about"
					class="px-3 py-1.5 rounded-lg text-sm transition-colors
						   {page.url.pathname === '/about'
							? 'text-accent-500 font-medium'
							: 'text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-100'}"
				>About</a>
				<a href="/docs"
					class="px-3 py-1.5 rounded-lg text-sm transition-colors
						   {page.url.pathname === '/docs'
							? 'text-accent-500 font-medium'
							: 'text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-100'}"
				>Technical Documentation</a>
			</div>

			<div class="flex-1"></div>

			<!-- Desktop search -->
			{#if !isHome}
				<div class="hidden md:block">
					<SearchBar />
				</div>
			{/if}
			<ThemeToggle />
			<button
				onclick={() => settingsOpen = true}
				aria-label="Settings"
				class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-sm transition-colors
					   {hasMidiOutputs
						? 'text-surface-600 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700'
						: 'text-accent-500 bg-accent-500/10 hover:bg-accent-500/20'}"
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
					<circle cx="12" cy="12" r="3"/>
				</svg>
				<span class="hidden sm:inline">{hasMidiOutputs ? 'Settings' : 'Connect MIDI'}</span>
				{#if !hasMidiOutputs}
					<span class="w-2 h-2 rounded-full bg-accent-500 animate-pulse"></span>
				{/if}
			</button>

			<!-- Hamburger button (mobile) -->
			<button
				onclick={() => mobileMenuOpen = !mobileMenuOpen}
				aria-label="Toggle menu"
				class="md:hidden p-1.5 rounded-lg text-surface-600 dark:text-surface-400
					   hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors"
			>
				{#if mobileMenuOpen}
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path d="M6 18L18 6M6 6l12 12"/>
					</svg>
				{:else}
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path d="M4 6h16M4 12h16M4 18h16"/>
					</svg>
				{/if}
			</button>
		</nav>

		<!-- Mobile menu -->
		{#if mobileMenuOpen}
			<div class="md:hidden border-t border-surface-200 dark:border-surface-800
						bg-surface-50/95 dark:bg-surface-950/95 backdrop-blur-sm">
				<div class="max-w-6xl mx-auto px-4 py-3 flex flex-col gap-1">
					{#if !isHome}
						<div class="pb-2">
							<SearchBar />
						</div>
					{/if}
					<a href="/"
						class="px-3 py-2 rounded-lg text-sm transition-colors
							   {page.url.pathname === '/'
								? 'text-accent-500 font-medium bg-accent-500/10'
								: 'text-surface-600 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700'}"
					>Home</a>
					<a href="/player"
						class="px-3 py-2 rounded-lg text-sm transition-colors
							   {page.url.pathname === '/player'
								? 'text-accent-500 font-medium bg-accent-500/10'
								: 'text-surface-600 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700'}"
					>Standalone Player</a>
					<a href="/about"
						class="px-3 py-2 rounded-lg text-sm transition-colors
							   {page.url.pathname === '/about'
								? 'text-accent-500 font-medium bg-accent-500/10'
								: 'text-surface-600 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700'}"
					>About</a>
					<a href="/docs"
						class="px-3 py-2 rounded-lg text-sm transition-colors
							   {page.url.pathname === '/docs'
								? 'text-accent-500 font-medium bg-accent-500/10'
								: 'text-surface-600 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700'}"
					>Technical Documentation</a>
				</div>
			</div>
		{/if}
	</header>

	<!-- Content -->
	<main class="max-w-6xl mx-auto px-4 py-8 pb-24">
		{@render children()}
	</main>

	<!-- Footer -->
	<footer class="border-t border-surface-200 dark:border-surface-800 pb-24">
		<div class="max-w-6xl mx-auto px-4 py-6 flex flex-col items-center gap-4 text-xs text-surface-400">
			<div class="flex flex-col sm:flex-row items-center justify-between gap-3 w-full">
				<span>MaestroMIDIplayer</span>
				<span>This app is entirely vibecoded, check out the <a class="text-accent-500 transition-colors" href="/about#how-it-was-made">About page</a> for more info.</span>
				<span><a href="https://magenta.tensorflow.org/datasets/maestro" target="_blank" rel="noopener" class="hover:text-accent-500 transition-colors">MAESTRO v3.0.0</a> (CC BY-NC-SA 4.0)</span>
			</div>
			<div class="flex items-center gap-2">
				<a href="https://github.com/andalu30" target="_blank" rel="noopener"
					class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
						   border border-surface-200 dark:border-surface-700
						   hover:border-accent-500 hover:text-accent-500 transition-colors">
					<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="none"/>
						<path d="M2 12h20M12 2c2.5 3 4 6.5 4 10s-1.5 7-4 10c-2.5-3-4-6.5-4-10s1.5-7 4-10z" fill="none"/>
					</svg>
					Website
				</a>
				<a href="https://github.com/andalu30" target="_blank" rel="noopener"
					class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
						   border border-surface-200 dark:border-surface-700
						   hover:border-accent-500 hover:text-accent-500 transition-colors">
					<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
						<path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836a9.59 9.59 0 012.504.337c1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
					</svg>
					GitHub
				</a>
			</div>
		</div>
	</footer>

	<!-- Player -->
	<PlayerBar />

	<!-- Settings -->
	<SettingsPanel open={settingsOpen} onclose={() => settingsOpen = false} />
</div>
