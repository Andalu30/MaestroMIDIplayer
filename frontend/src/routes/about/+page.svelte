<svelte:head>
	<title>About — maestroMIDIplayer</title>
</svelte:head>

<article class="max-w-2xl mx-auto">
	<h1 class="text-3xl font-bold text-surface-900 dark:text-surface-100 mb-8">About</h1>

	<div class="space-y-8 text-surface-600 dark:text-surface-400 leading-relaxed">


		<div class="space-y-3">
			<p>
				<strong class="text-surface-900 dark:text-surface-100">maestroMIDIplayer</strong> is a web app
				for browsing and playing piano performances from the
				<a href="https://magenta.tensorflow.org/datasets/maestro" target="_blank" rel="noopener"
					class="text-accent-500 hover:underline">MAESTRO</a> dataset — a collection of 1,276 MIDI
				recordings captured from the International Piano-e-Competition between 2004 and 2018.
			</p>
			<p>
				The idea is simple: connect a digital piano, pick a piece, and hear it played back on your
				own instrument. Every note, every nuance of timing and velocity, exactly as it was performed
				by the competition participants.
			</p>
		</div>


		<nav class="rounded-xl border border-surface-200 dark:border-surface-800 p-5 bg-surface-100/50 dark:bg-surface-900/50">
			<h2 class="text-sm font-semibold text-surface-800 dark:text-surface-200 mb-3 uppercase tracking-wider">Contents</h2>
			<ol class="columns-2 gap-8 text-sm space-y-1.5">
				<li><a href="#how-it-works" class="text-accent-500 hover:underline">How it works</a></li>
				<li><a href="#connecting" class="text-accent-500 hover:underline">Connecting your piano</a></li>
				<li><a href="#standalone" class="text-accent-500 hover:underline">Standalone player</a></li>
				<li><a href="#dataset" class="text-accent-500 hover:underline">The dataset</a></li>
				<li><a href="#competition" class="text-accent-500 hover:underline">The competition</a></li>
				<li><a href="#how-it-was-made" class="text-accent-500 hover:underline">How this was made</a></li>
				<li><a href="#whats-the-point" class="text-accent-500 hover:underline">What's the point?</a></li>
			</ol>
		</nav>

		<section id="how-it-works">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">How it works</h2>
			<p>
				The app sends MIDI data directly to your piano through the
				<a href="https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API" target="_blank" rel="noopener"
					class="text-accent-500 hover:underline">Web MIDI API</a>.
				Connect via Bluetooth or USB, and the notes play on your instrument's own sound engine — no
				speakers or software synthesizers involved. You hear each performance through the character
				of your own piano.
			</p>
			<p class="mt-3">
				Playback happens entirely in the browser. A lightweight Python backend serves the dataset
				and composer images, but once a MIDI file is loaded, it never touches the server again.
				Tempo can be adjusted from 0.25× to 2×, and the queue system lets you chain a whole
				composer's catalogue or competition round in one go.
			</p>
		</section>

		<section id="connecting">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Connecting your piano</h2>
			<div class="space-y-4">
				<div>
					<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mb-1">Via USB</h3>
					<p class="text-sm">
						Connect your piano's USB-MIDI port to your computer with a USB cable. Most digital pianos
						from Roland, Yamaha, Kawai, and others are supported out of the box — no drivers needed
						on modern operating systems.
					</p>
				</div>

				<div>
					<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mb-1">Via Bluetooth MIDI</h3>
					<p class="text-sm">
						If your piano supports Bluetooth MIDI (BLE MIDI), pair it through your system's Bluetooth
						settings. On macOS, you may need to open <em>Audio MIDI Setup</em> and click
						"Bluetooth Configuration…" to activate the paired device. On Windows, system pairing
						is usually sufficient.
					</p>
				</div>

				<div>
					<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mb-1">Selecting your device</h3>
					<p class="text-sm">
						Once connected, click the <strong class="text-surface-800 dark:text-surface-200">Settings</strong>
						button in the top-right corner. Your piano will appear under MIDI outputs. By default
						the app sends to all connected outputs simultaneously — useful if you have more than one
						device without needing to choose.
					</p>
				</div>

				<div>
					<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mb-1">Browser compatibility</h3>
					<p class="text-sm">
						The Web MIDI API is currently only supported in Chromium-based browsers (Chrome, Edge,
						Opera, Brave…). Firefox and Safari do not support it. If you open the app in an
						unsupported browser, playback will not work.
					</p>
				</div>

				<div>
					<h3 class="text-sm font-medium text-surface-800 dark:text-surface-200 mb-1">No piano?</h3>
					<p class="text-sm">
						You can still browse the collection. If you want to hear the performances, any software
						synthesizer that exposes a virtual MIDI port will work — <em>FluidSynth</em>,
						<em>Pianoteq</em>, your DAW...
				</div>
			</div>
		</section>

		<section id="standalone">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Standalone player</h2>
			<p>
				The <a href="/player" class="text-accent-500 hover:underline">Standalone Player</a> page
				lets you play any MIDI file from your computer — not just the MAESTRO dataset. Drag and
				drop a <code class="text-xs px-1 py-0.5 rounded bg-surface-100 dark:bg-surface-800">.mid</code> file
				onto the page and it loads and plays through your connected piano using the same engine
				as the rest of the app.
			</p>
			<p class="mt-3">
				Everything happens in the browser. The file is never uploaded anywhere. This makes it
				useful as a general-purpose MIDI player for sheet music files, personal arrangements, or
				anything else in Standard MIDI format.
			</p>
		</section>
		<hr>
		<section id="dataset">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">The dataset</h2>
			<p>
				MAESTRO (MIDI and Audio Edited for Synchronous TRacks and Organization) was created by
				Google's Magenta team. It pairs high-quality MIDI data with aligned audio recordings from
				Yamaha Disklaviers — pianos that capture every keystroke as precise MIDI events. The result
				is a uniquely detailed record of live piano performance.
			</p>
			<p class="mt-3">
				The collection spans 60 composers, from Bach to Prokofiev, across 10 years of competition.
				Some pieces appear multiple times, performed by different pianists in different years —
				making it possible to compare interpretations side by side.
			</p>
			<p class="mt-3">
				One thing the dataset does not include is performer attribution. The competition ran preliminary
				rounds under anonymized conditions — judges evaluated recordings without knowing who played them —
				and the dataset reflects that: there are no names attached to individual performances. The app
				organizes around composers because that is the only attribution the data provides. The pianists
				who made these recordings remain anonymous.
			</p>
		</section>

		<section id="competition">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">The International Piano-e-Competition</h2>
			<p>
				The International Piano-e-Competition is the source of every recording in this dataset.
				Founded in 2002 by pianist Alexander Braginsky at the University of Minnesota, the "e"
				stood for electronic — a reference to the Yamaha Disklavier concert grands used throughout
				the competition. These are acoustic instruments equipped with a high-precision MIDI capture
				system that records every note, velocity, and pedal movement in real time.
			</p>
			<p class="mt-3">
				This technology served a practical purpose beyond archiving. Preliminary round recordings
				could be transmitted to judges anywhere in the world and reproduced on a remote Disklavier —
				the judges heard a genuine acoustic piano performance, not a recording. It effectively
				removed geography from early round evaluation, broadening access for contestants around the world.
			</p>
			<p class="mt-3">
				Each year's competition is divided into rounds — typically covering preliminary auditions,
				semi-finalist sessions, and final rounds — and the dataset preserves that structure.
				Browsing by competition year in this app reflects those divisions, letting you follow
				the arc of a single year's contest from first performances through to the final stage.
			</p>
			<p class="mt-3">
				The competition ran for roughly two decades before quietly disappearing after its 2021 edition, which
				was held in an adapted format due to COVID-19. No official announcement or explanation was
				ever published — the website eventually went dark, and no further edition was ever announced.
				Outside the classical piano world, where it had been reasonably well regarded for its
				innovative format, it is now largely forgotten. For most people in machine learning and music
				AI research, it is known at all only because of the MAESTRO dataset — which is perhaps an
				odd kind of afterlife for a competition that tried to do something genuinely interesting.
			</p>
		</section>
		<section id="how-it-was-made">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">How this was made</h2>
			<p>
				This app was entirely vibecoded — written through conversation with a large language model. Special attention was paid to guiding it toward correct decisions and making sure the decisions were at least reasonable. No line of code was typed by hand other than obvious adjustments to fix things that were clearly wrong or did not work at all. 
			</p>
			<p class="mt-3">
				That has some implications worth being honest about. The code works, but it has
				not been reviewed the way hand-written code would be. There probably are edge cases neither
				the author nor the model thought to check and while the architecture made sense at the time of
				each decision, it may be inconsistent just for the pure nature of how it was built. It is likely that there are some security issues, performance bottlenecks, and other things that would have been caught and fixed in a normal development process. The code is not meant to be an example of good practices or a reference for how to build something like this — it is what it is, a proof of concept built in a very specific way.<br>
				All of that to say that this might all break if you look at it funny or try to play a Touhou MIDI or something<br>
				It is not production quality code by any stretch of the imagination, but it is good enough for a fun demo and to show what can be done with the tools we have today so please keep that in mind if you decide to peek under the hood.
			</p>
			<p class="mt-3">
				Because of this, maintenance is likely to be minimal/non-existent.<br>
				At least it works, it does what it is supposed to do, and the result is visually better than what could have been produced manually in the same amount of time. <br>
				Whether services like this are something to feel proud and think fondly of is left as an exercise to the reader, for the author they are not. This is nothing more than a fun experiment with an old idea.<br>
				Sometimes we need a bit of fun to remember why we love our craft and new technologies might help with that, but consider this for what it really is — not a project that was meant to be taken seriously in any way just a playground for exploring what can be done with AI-assisted development.
			</p>
		</section>
		<section id="whats-the-point">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">What's the point then?</h2>
			<p class="mt-3">
				Then, why build something like this at all? The world does not need another MIDI player, and the
				MAESTRO dataset is already available for anyone to download and use in their own projects.
				The app does not do anything that could not be done with other solutions or a DAW. It is
				not a research contribution, it is not a commercial product, and it is not something the
				author expects anyone to use beyond maybe showing it to a friend once.
			</p>
			<p class="mt-3">
				That said, it is a fun demonstration of what can be done with the tools we have today. A reminder that we can build things that are genuinely useful and enjoyable with very little effort, if only one knows what to ask for and how to steer the process.<br>
				It is a celebration of the creativity that coding enables, and of the new possibilities that AI-assisted development opens up. 	
			</p>
			<p class="mt-3">
				Sometimes a PoC is more than enough and we don't need a full engineering effort to make something worth making. This is one of those times I guess.
			</p>
		</section>
		<section id="built-with">
			<h2 class="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-3">Built with</h2>
			<div class="flex flex-wrap gap-2">
				{#each ['SvelteKit', 'Tailwind CSS 4', 'FastAPI', 'Web MIDI API', '@tonejs/midi', 'Claude Code'] as tech}
					<span class="text-xs px-2.5 py-1 rounded-full bg-surface-100 dark:bg-surface-800
								 text-surface-600 dark:text-surface-400 border border-surface-200 dark:border-surface-700">
						{tech}
					</span>
				{/each}
			</div>
		</section>

		<p class="text-sm text-surface-500 pt-4 border-t border-surface-200 dark:border-surface-800">
			The MAESTRO dataset is released under
			<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="noopener"
				class="text-accent-500 hover:underline">CC BY-NC-SA 4.0</a>
			by Google and the International Piano-e-Competition.
		</p>
	</div>
</article>
