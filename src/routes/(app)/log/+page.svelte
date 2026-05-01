<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';
	import { primaryCurrency, toLocal } from '$lib/stores/exchange';

	type Snapshot = {
		id: number;
		created_at: string;
		total_invoiced_usd: number;
		total_received_usd: number;
	};

	let snapshots = $state<Snapshot[]>([]);
	let loading = $state(true);
	let error = $state('');

	function getToken() {
		return localStorage.getItem('cornea_token');
	}

	onMount(async () => {
		try {
			const token = getToken();
			if (!token) {
				void goto('/auth');
				return;
			}

			const res = await fetch('/api/log', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.status === 401) {
				localStorage.removeItem('cornea_token');
				void goto('/auth');
				return;
			}
			if (!res.ok) throw new Error('Failed to fetch commits.');
			const data = await res.json();
			snapshots = data.snapshots || [];
		} catch (e) {
			console.error(e);
			error = e instanceof Error ? e.message : 'Failed to fetch commits.';
		} finally {
			loading = false;
		}
	});

	async function runMockSync() {
		const token = getToken();
		if (!token) {
			void goto('/auth');
			return;
		}

		try {
			const res = await fetch('/api/sync/mock', {
				method: 'POST',
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.status === 401) {
				localStorage.removeItem('cornea_token');
				void goto('/auth');
				return;
			}
			if (!res.ok) throw new Error('Mock sync failed.');
			location.reload();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Mock sync failed.';
		}
	}

	function formatUsd(value = 0) {
		return `$${value.toFixed(2)}`;
	}

	function snapshotReceivedLocal(snapshot: Snapshot) {
		return toLocal(snapshot.total_received_usd);
	}
</script>

<svelte:head>
	<title>Git Log | Cornea</title>
</svelte:head>

<div class="page-header">
	<h1>log</h1>
	<p class="subtitle">Your version-controlled financial history.</p>
</div>

{#if loading}
	<p class="loading">Fetching commits...</p>
{:else if error}
	<div class="empty-state">
		<p>{error}</p>
	</div>
{:else if snapshots.length === 0}
	<div class="empty-state">
		<p>
			No commits found. Try running a sync first.<br />
			<NeoButton onclick={runMockSync} class="mt-4">Run Mock Sync</NeoButton>
		</p>
	</div>
{:else}
	<div class="timeline">
		{#each snapshots as s}
			<div class="commit-card">
				<div class="commit-header">
					<span class="hash">commit {s.id.toString().padStart(7, '0')}</span>
					<span class="date">{new Date(s.created_at).toLocaleDateString()}</span>
				</div>
				<div class="commit-body">
					<div class="stat-row">
						<span class="label">Invoiced (USD):</span>
						<span class="value">{formatUsd(s.total_invoiced_usd)}</span>
					</div>
					<div class="stat-row">
						<span class="label">Received ({$primaryCurrency}):</span>
						<span class="value local">{snapshotReceivedLocal(s).toFixed(2)} {$primaryCurrency}</span
						>
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	.page-header {
		margin-bottom: 3rem;
	}
	h1 {
		font-size: 3rem;
		margin: 0;
		text-transform: lowercase;
	}
	.subtitle {
		color: var(--theme-muted);
		font-size: 1.2rem;
		margin-top: 0.5rem;
	}
	.timeline {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		border-left: 4px solid var(--theme-line);
		padding-left: 1.75rem;
		margin-left: 1rem;
	}
	.commit-card {
		border: 3px solid var(--theme-line);
		background: var(--theme-paper);
		border-radius: 1rem;
		padding: 1.5rem;
		box-shadow: 6px 6px 0 var(--theme-shadow);
		position: relative;
	}
	.commit-card::before {
		content: '';
		position: absolute;
		left: -2.8rem;
		top: 2rem;
		width: 1.5rem;
		height: 1.5rem;
		background: var(--theme-accent);
		border: 3px solid var(--theme-line);
		border-radius: 50%;
	}
	.commit-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 1rem;
		border-bottom: 2px dashed var(--theme-line);
		padding-bottom: 0.5rem;
	}
	.hash {
		font-family: monospace;
		color: var(--theme-accent);
		font-weight: bold;
	}
	.date {
		color: var(--theme-muted);
	}
	.stat-row {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		font-size: 1.1rem;
	}
	.stat-row .label {
		font-weight: bold;
	}
	.stat-row .local {
		color: var(--theme-accent);
		font-weight: 900;
	}
</style>
