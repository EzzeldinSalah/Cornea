<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';
	import { PUBLIC_GOOGLE_CLIENT_ID } from '$env/static/public';

	type GoogleCredentialResponse = {
		credential: string;
	};

	type GoogleAccounts = {
		accounts: {
			id: {
				initialize: (config: {
					client_id: string;
					callback: (response: GoogleCredentialResponse) => void;
				}) => void;
				renderButton: (container: HTMLElement, options: Record<string, unknown>) => void;
			};
		};
	};

	type GoogleWindow = Window & typeof globalThis & { google?: GoogleAccounts };

	let isLogin = $state(true);
	let email = $state('');
	let password = $state('');
	let googleBtnContainer: HTMLDivElement | undefined;

	function renderGoogleButton() {
		const google = (window as GoogleWindow).google;
		if (google && googleBtnContainer) {
			google.accounts.id.initialize({
				client_id: PUBLIC_GOOGLE_CLIENT_ID,
				callback: handleGoogleResponse
			});
			google.accounts.id.renderButton(googleBtnContainer, {
				theme: 'outline',
				size: 'large',
				width: 320,
				text: isLogin ? 'signin_with' : 'signup_with',
				shape: 'rectangular'
			});
		}
	}

	onMount(() => {
		const checkGoogle = setInterval(() => {
			if ((window as GoogleWindow).google) {
				clearInterval(checkGoogle);
				renderGoogleButton();
			}
		}, 100);
		return () => clearInterval(checkGoogle);
	});

	$effect(() => {
		renderGoogleButton();
	});

	async function handleGoogleResponse(response: GoogleCredentialResponse) {
		try {
			const res = await fetch('/api/auth/google', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ credential: response.credential })
			});
			const data = await res.json();
			if (res.ok && data.token) {
				localStorage.setItem('cornea_token', data.token);
				void goto(resolve('/log'));
			} else {
				alert(data.detail || 'Google auth failed');
			}
		} catch {
			alert('Error with Google login');
		}
	}

	async function handleManualAuth(event: SubmitEvent) {
		event.preventDefault();
		const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
		try {
			const res = await fetch(endpoint, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});
			const data = await res.json();
			if (res.ok && data.token) {
				localStorage.setItem('cornea_token', data.token);
				void goto(resolve('/log'));
			} else {
				alert(data.detail || 'Authentication failed');
			}
		} catch {
			alert('Error authenticating');
		}
	}
</script>

<svelte:head>
	<script src="https://accounts.google.com/gsi/client" async defer></script>
	<title>{isLogin ? 'Sign In' : 'Sign Up'} | Cornea</title>
</svelte:head>

<main class="auth-page" lang="en">
	<div class="grid-bg" aria-hidden="true"></div>
	<div class="auth-container shell">
		<div class="auth-header">
			<h1>{isLogin ? 'Welcome Back' : 'Join Cornea'}</h1>
			<p class="subtitle">Financial intelligence for the bold.</p>
		</div>

		<div class="auth-card">
			<div class="toggle-group">
				<button class="toggle-btn" class:active={isLogin} onclick={() => (isLogin = true)}
					>Sign In</button
				>
				<button class="toggle-btn" class:active={!isLogin} onclick={() => (isLogin = false)}
					>Sign Up</button
				>
			</div>

			<form onsubmit={handleManualAuth} class="auth-form">
				<div class="input-group">
					<label for="email">Email</label>
					<input
						type="email"
						id="email"
						bind:value={email}
						required
						placeholder="you@example.com"
					/>
				</div>
				<div class="input-group">
					<label for="password">Password</label>
					<input
						type="password"
						id="password"
						bind:value={password}
						required
						placeholder="••••••••"
					/>
				</div>
				<NeoButton type="submit" class="mt-4 w-full">
					{isLogin ? 'Sign In' : 'Sign Up'}
				</NeoButton>
			</form>

			<div class="divider">
				<span>OR</span>
			</div>

			<div class="google-btn-wrapper" bind:this={googleBtnContainer}></div>
		</div>
	</div>
</main>

<style>
	.auth-page {
		--bg: var(--theme-bg);
		--paper: var(--theme-paper);
		--line: var(--theme-line);
		--text: var(--theme-text);
		--muted: var(--theme-muted);
		--shadow: var(--theme-shadow);
		--accent: var(--theme-accent);

		position: relative;
		min-height: 100vh;
		background: var(--bg);
		color: var(--text);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		overflow: hidden;
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
		z-index: 0;
	}

	.auth-container {
		position: relative;
		z-index: 1;
		width: 100%;
		max-width: 440px;
	}

	.auth-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 3rem;
		margin: 0;
		text-transform: lowercase;
		line-height: 1.1;
	}

	.subtitle {
		color: var(--muted);
		font-size: 1.1rem;
		margin-top: 0.5rem;
	}

	.auth-card {
		background: var(--paper);
		border: 4px solid var(--line);
		border-radius: 1.25rem;
		box-shadow: 8px 8px 0 var(--shadow);
		padding: 2rem;
	}

	.toggle-group {
		display: flex;
		border: 3px solid var(--line);
		border-radius: 0.75rem;
		overflow: hidden;
		margin-bottom: 1.5rem;
		background: var(--bg);
	}

	.toggle-btn {
		flex: 1;
		padding: 0.75rem;
		background: transparent;
		border: none;
		font-weight: 800;
		font-size: 1rem;
		font-family: inherit;
		color: var(--text);
		cursor: pointer;
		transition:
			background 0.2s,
			color 0.2s;
	}

	.toggle-btn.active {
		background: var(--accent);
		color: var(--theme-accent-ink);
		border-bottom: none;
	}

	.toggle-btn:not(.active):hover {
		background: rgba(0, 0, 0, 0.05);
	}

	.auth-form {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.input-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	label {
		font-weight: 700;
		font-size: 0.95rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	input {
		padding: 0.8rem;
		border: 3px solid var(--line);
		border-radius: 0.5rem;
		background: var(--bg);
		color: var(--text);
		font-family: inherit;
		font-size: 1rem;
		outline: none;
		transition:
			box-shadow 0.2s,
			transform 0.1s;
	}

	input:focus {
		box-shadow: 4px 4px 0 var(--accent);
		transform: translate(-2px, -2px);
	}

	.divider {
		display: flex;
		align-items: center;
		text-align: center;
		margin: 1.5rem 0;
		color: var(--muted);
		font-weight: 800;
		font-family: monospace;
	}

	.divider::before,
	.divider::after {
		content: '';
		flex: 1;
		border-bottom: 3px dashed var(--line);
		opacity: 0.5;
	}

	.divider span {
		padding: 0 1rem;
	}

	.google-btn-wrapper {
		display: flex;
		justify-content: center;
		padding: 0.5rem;
		border: 3px solid var(--line);
		border-radius: 0.75rem;
		background: white;
		box-shadow: 4px 4px 0 var(--shadow);
		transition:
			transform 0.2s,
			box-shadow 0.2s;
	}

	.google-btn-wrapper:hover {
		transform: translate(-2px, -2px);
		box-shadow: 6px 6px 0 var(--shadow);
	}
</style>
