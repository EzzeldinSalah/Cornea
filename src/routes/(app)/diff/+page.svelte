<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';
	import NeoCard from '$lib/components/ui/NeoCard.svelte';
	import { primaryCurrency, toLocal } from '$lib/stores/exchange';

	type Diff = {
		diff_invoiced_usd: number;
		diff_fees_usd: number;
		diff_received_usd: number;
		now_received_usd: number;
		past_received_usd: number;
	};

	let diff = $state<Diff | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

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

			const res = await fetch('/api/diff', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.status === 401) {
				localStorage.removeItem('cornea_token');
				void goto('/auth');
				return;
			}
			if (!res.ok) throw new Error('Failed to compute diff.');
			const data = await res.json();
			if (!data) throw new Error('Need at least two snapshots to compute a diff.');
			if (data.error) throw new Error(data.error);
			diff = data;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to compute diff.';
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

	function formatDelta(val: number) {
		const prefix = val > 0 ? '+' : '';
		return prefix + val.toFixed(2);
	}

	function formatLocalDelta(valueUsd: number) {
		const currency = $primaryCurrency || 'USD';
		const localValue = toLocal(valueUsd);
		return `${formatDelta(localValue)} ${currency}`;
	}
</script>

<svelte:head>
	<title>Git Diff | Cornea</title>
</svelte:head>

<div class="page-header">
	<h1>diff</h1>
	<p class="subtitle">Comparing current income vs past reality.</p>
</div>

{#if loading}
	<p class="loading">Computing variations...</p>
{:else if error}
	<div class="empty-state">
		<p>{error} Try running a sync first to generate more data.</p>
		<NeoButton onclick={runMockSync} class="mt-4">Run Mock Sync</NeoButton>
	</div>
{:else if diff}
	<NeoCard class="diff-card !p-0">
		<div class="diff-header">@@ -1,3 +1,3 @@</div>
		<div class="diff-body">
			<div class="diff-line {diff.diff_received_usd >= 0 ? 'add' : 'remove'}">
				<span class="sign">{diff.diff_received_usd >= 0 ? '+' : '-'}</span>
				<span class="text">USD Received Change: {formatDelta(diff.diff_received_usd)}</span>
			</div>
			<div class="diff-line {diff.diff_invoiced_usd >= 0 ? 'add' : 'remove'}">
				<span class="sign">{diff.diff_invoiced_usd >= 0 ? '+' : '-'}</span>
				<span class="text">USD Invoiced Change: {formatDelta(diff.diff_invoiced_usd)}</span>
			</div>
			<div class="diff-line neutral">
				<span class="sign">~</span>
				<span class="text">Local Received Change: {formatLocalDelta(diff.diff_received_usd)}</span>
			</div>
		</div>
	</NeoCard>
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
	:global(.diff-card) {
		font-family: monospace;
		font-size: 1.2rem;
		overflow: hidden;
	}
	.diff-header {
		background: var(--theme-bg);
		padding: 1rem;
		border-bottom: 3px solid var(--theme-line);
		color: var(--theme-muted);
	}
	.diff-line {
		padding: 1rem;
		display: flex;
		gap: 1rem;
		border-bottom: 1px solid var(--theme-line);
	}
	.diff-line:last-child {
		border-bottom: none;
	}
	.diff-line.add {
		background: #d4edda;
		color: #155724;
	}
	.diff-line.remove {
		background: #f8d7da;
		color: #721c24;
	}
	.diff-line.neutral {
		background: #e2e3e5;
		color: #383d41;
	}
</style>
