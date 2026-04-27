<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import logo from '$lib/assets/favicon.svg';
	import logIcon from '$lib/assets/log.png';
	import diffIcon from '$lib/assets/diff.png';
	import blameIcon from '$lib/assets/blame.png';
	import coachIcon from '$lib/assets/coach.png';
	import settingIcon from '$lib/assets/setting.png';
</script>

<aside class="sidebar">
	<a href={resolve('/')} class="brand">
		<img class="logo" src={logo} alt="Cornea logo" />
		<span>C O R N E A</span>
	</a>

	<nav class="nav-links">
		<a href={resolve('/log')} class:active={page.url.pathname.includes('/log')}>
			<img class="icon" src={logIcon} alt="Log" /> <span class="text">Log</span>
		</a>
		<a href={resolve('/diff')} class:active={page.url.pathname.includes('/diff')}>
			<img class="icon" src={diffIcon} alt="Diff" /> <span class="text">Diff</span>
		</a>
		<a href={resolve('/blame')} class:active={page.url.pathname.includes('/blame')}>
			<img class="icon" src={blameIcon} alt="Blame" /> <span class="text">Blame</span>
		</a>
		<a href={resolve('/coach')} class:active={page.url.pathname.includes('/coach')}>
			<img class="icon" src={coachIcon} alt="Coach" /> <span class="text">Coach</span>
		</a>
		<a href={resolve('/settings')} class:active={page.url.pathname.includes('/settings')}>
			<img class="icon" src={settingIcon} alt="Settings" /> <span class="text">Settings</span>
		</a>

		<div class="divider"></div>
		<p class="section-label">Coming Soon</p>

		<a href="#" class="disabled">
			<span class="icon emoji">🌿</span> <span class="text">Branch</span>
		</a>
		<a href="#" class="disabled">
			<span class="icon emoji">🔀</span> <span class="text">Merge</span>
		</a>
	</nav>

	<div class="footer">
		<div class="status">● Workspace Synced</div>
	</div>
</aside>

<style>
	.sidebar {
		border-top-right-radius: 2rem;
		border-bottom-right-radius: 2rem;
		width: 250px;
		min-height: 100vh;
		padding: 2rem 1.5rem;
		background: var(--theme-text);
		color: var(--theme-paper);
		border-right: 4px solid var(--theme-line);
		display: flex;
		flex-direction: column;
		box-shadow: 6px 0 0 var(--theme-shadow);
		z-index: 10;
		position: relative;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-family: 'Akira', sans-serif;
		font-size: 1rem;
		text-decoration: none;
		color: var(--theme-paper);
		padding-bottom: 1rem;
	}

	.logo {
		width: 2rem;
		height: 2rem;
	}

	.nav-links {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		flex: 1;
	}

	.nav-links a {
		display: flex;
		align-items: center;
		gap: 1rem;
		text-decoration: none;
		font-weight: 800;
		font-size: 0.95rem;
		color: #ffffff;
		padding: 0.8rem 1rem;
		border: 3px solid transparent;
		transition: all 0.15s ease-out;
		border-radius: 12px;
	}

	.icon {
		width: 1.5rem;
		height: 1.5rem;
		object-fit: contain;
		filter: invert(1) brightness(2);
		transition: filter 0.2s;
	}
	.icon.emoji {
		font-size: 1.3rem;
		filter: grayscale(1) !important;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.text {
		letter-spacing: 0.05em;
	}

	.nav-links a:not(.disabled):not(.active):hover {
		background: #4a2714;
		color: var(--theme-paper);
		transform: translate(2px, -2px);
	}

	.nav-links a.active {
		background: var(--theme-accent);
		color: var(--theme-accent-ink);
		border: 3px solid var(--theme-line);
		box-shadow: 4px 4px 0 var(--theme-line);
		transform: translate(-3px, -3px);
	}

	.nav-links a.active .icon {
		filter: invert(0);
	}

	.nav-links a.disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.divider {
		height: 2px;
		background: #4a2714;
		margin: 1rem 0 0.5rem 0;
		border-radius: 2px;
	}

	.section-label {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: #8a6a50;
		margin-bottom: 0.5rem;
		font-weight: bold;
		padding-left: 1rem;
	}

	.footer {
		padding-top: 1.5rem;
	}

	.status {
		font-family: monospace;
		font-size: 0.8rem;
		color: #88ff88;
		font-weight: bold;
		letter-spacing: 0.05em;
	}
</style>
