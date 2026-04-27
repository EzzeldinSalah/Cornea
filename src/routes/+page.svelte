<script lang="ts">
	import { resolve } from '$app/paths';
	import Navbar from '$lib/components/Navbar.svelte';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';
	import NeoCard from '$lib/components/ui/NeoCard.svelte';

	const homeHref = resolve('/');
	const appHref = resolve('/log');

	const systemCards = [
		{
			title: 'git log for money',
			description: 'See every Upwork sync as a commit. Track your real EGP income timeline.'
		},
		{ title: 'git diff your months', description: 'See exactly why you made less, even if you invoiced more.' },
		{ title: 'git blame your clients', description: 'Know exactly which client is costing you money using payments or rates.' }
	];

	const buildCards = [
		{ title: '1. Connect Upwork', description: 'One-click OAuth = Zero manual entry.' },
		{ title: '2. Auto Sync', description: 'We pull your invoices, fees, and the daily your local currency.' },
		{ title: '3. Cornea Mind', description: 'Get insights & coaching from your AI Financial advisor based on numbers.' }
	];
</script>

<svelte:head>
	<title>Cornea: Financial Intelligence for Arab Freelancers</title>
	<meta
		name="description"
		content="You invoiced $4,000. What did you actually make? The Git-inspired financial tool for builders."
	/>
</svelte:head>

<main class="landing" lang="en">
	<div class="grid-bg" aria-hidden="true"></div>

	<Navbar />

	<section class="shell hero">
		<div class="hero-copy">
			<h1>Invoiced X USD<br>Your pocket says . . . ?</h1>
			<p class="hero-subtitle">Upwork shows what you billed. Cornea shows what reached your pocket after fees, currency shifts, and inflation.</p>
			<div class="hero-actions">
				<NeoButton href={appHref}>Open Dashboard</NeoButton>
				<NeoButton variant="secondary" href="#system">Explore Features</NeoButton>
			</div>
		</div>
	</section>

	<section id="system" class="shell section">
		<p class="eyebrow">The Mental Model</p>
		<h2>Financial history & Git - Mindset</h2>
		<br>
		<div class="card-grid">
			{#each systemCards as card (card.title)}
				<NeoCard>
					<h3>{card.title}</h3>
					<p>{card.description}</p>
				</NeoCard>
			{/each}
		</div>
	</section>

	<section id="build" class="shell section">
		<p class="eyebrow">Zero Friction</p>
		<h2>No manual spreadsheets</h2>
		<br>
		<div class="card-grid">
			{#each buildCards as card (card.title)}
				<NeoCard>
					<h3>{card.title}</h3>
					<p>{card.description}</p>
				</NeoCard>
			{/each}
		</div>
	</section>

	<section id="launch" class="shell section launch">
		<div class="launch-card">
			<h2>Ready to face the numbers?</h2>
			<div class="hero-actions center">
				<NeoButton href={appHref}>Start Syncing</NeoButton>
				<NeoButton variant="secondary" href="https://github.com/EzzeldinSalah">Explore System</NeoButton>
			</div>
		</div>
	</section>
</main>

<style>
	.landing {
		--bg: var(--theme-bg);
		--paper: var(--theme-paper);
		--line: var(--theme-line);
		--text: var(--theme-text);
		--muted: var(--theme-muted);
		--shadow: var(--theme-shadow);
		--accent: var(--theme-accent);
		--accent-ink: var(--theme-accent-ink);

		position: relative;
		min-height: 100dvh;
		background: var(--bg);
		color: var(--text);
		overflow: clip;
		padding-bottom: 2.25rem;
	}

	.grid-bg {
		position: absolute;
		inset: 0;
		pointer-events: none;
		background:
			repeating-linear-gradient(
				90deg,
				transparent,
				transparent 35px,
				rgba(43, 30, 22, 0.08) 35px,
				rgba(43, 30, 22, 0.08) 36px
			),
			repeating-linear-gradient(
				0deg,
				transparent,
				transparent 35px,
				rgba(43, 30, 22, 0.08) 35px,
				rgba(43, 30, 22, 0.08) 36px
			);
		opacity: 1;
	}

	.shell {
		position: relative;
		z-index: 1;
		width: min(1240px, calc(100% - 2rem));
		margin-inline: auto;
	}

	.hero {
		display: grid;
		gap: 1.25rem;
		padding-block: 3.2rem 1.8rem;
	}

	.hero-copy {
		max-width: 84ch;
	}

	h1 {
		margin: 0;
		font-size: clamp(2.2rem, 6vw, 4.4rem);
		line-height: 1;
		max-width: 24ch;
	}

	.hero-subtitle {
		margin: 0.9rem 0 0;
		max-width: 76ch;
		line-height: 1.75;
		color: var(--muted);
	}

	.eyebrow {
		margin: 0;
		font-size: 0.74rem;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		font-weight: 700;
		color: var(--muted);
	}

	h2 {
		margin: 0.45rem 0 0;
		font-size: clamp(1.7rem, 4vw, 2.5rem);
		line-height: 1.02;
	}

	.section-copy {
		margin: 0.6rem 0 0;
		max-width: 72ch;
		line-height: 1.7;
		color: var(--muted);
	}

	.section-copy.center {
		margin-inline: auto;
		text-align: center;
	}

	.hero-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.65rem;
		margin-top: 1.1rem;
	}

	.hero-actions.center {
		justify-content: center;
	}

	.section {
		margin-top: 2.35rem;
	}

	.card-grid {
		display: grid;
		gap: 0.9rem;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
	}

	h3 {
		margin: 0;
		font-size: 1.15rem;
		margin-bottom: 0.5rem;
	}

	:global(.card p) {
		margin-bottom: 0;
		color: var(--muted);
	}

	.launch {
		margin-bottom: 0.2rem;
	}

	.launch-card {
		border: 3px solid var(--line);
		background: color-mix(in srgb, var(--paper) 86%, var(--accent) 14%);
		border-radius: 1rem;
		box-shadow: 7px 7px 0 var(--shadow);
		padding: 1rem;
	}

	@media (max-width: 640px) {
		/* Adjusted for potentially other local rules */
	}
</style>
