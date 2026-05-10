<script lang="ts">
	import { resolve } from '$app/paths';
	import logo from '$lib/assets/favicon.svg';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';

	const homeHref = resolve('/');
	const appHref = resolve('/log');
	const authHref = resolve('/auth');
</script>

<header class="shell nav-shell">
	<div class="nav-bar">
		<a href={homeHref} class="brand">
			<img class="logo" src={logo} alt="Cornea logo" />
			<span>CORNEA</span>
		</a>

		<nav class="nav-links" aria-label="Primary navigation">
			<a href="#system">Features</a>
			<a href="#build">Model</a>
			<a href={appHref} target="_blank">Dashboard</a>
		</nav>
		<a href={authHref} target="_blank">
			<NeoButton variant="secondary" class="!px-4 !py-2 !text-sm">Login</NeoButton>
		</a>
	</div>
</header>

<style>
	.shell {
		position: relative;
		z-index: 1;
		width: min(1240px, calc(100% - 2rem));
		margin-inline: auto;
	}

	.nav-shell {
		position: sticky;
		top: 0.65rem;
		padding-top: 0.65rem;
		z-index: 30;
	}

	.nav-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.55rem 0.85rem;
		border: 3px solid var(--theme-line);
		border-radius: 999px;
		background: var(--theme-paper);
		box-shadow: 6px 6px 0 var(--theme-shadow);
	}

	.brand {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		font-family: 'Akira', sans-serif;
		font-size: 0.7rem;
		letter-spacing: 0.2em;
		color: var(--theme-text);
		text-decoration: none;
	}

	.logo {
		width: 2rem;
		height: 2rem;
	}

	.nav-links {
		display: none;
		gap: 3rem;
	}

	.nav-links a {
		text-decoration: none;
		color: var(--theme-muted);
		font-size: 0.9rem;
		font-weight: 600;
		transition: color 0.15s;
	}

	.nav-links a:hover {
		color: var(--theme-text);
	}

	@media (min-width: 850px) {
		.nav-links {
			display: inline-flex;
		}
	}

	@media (max-width: 640px) {
		.brand span {
			display: none;
		}

		.nav-bar {
			border-radius: 1rem;
			padding: 0.5rem 0.62rem;
		}
	}
</style>
