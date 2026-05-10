<script lang="ts">
	import { onMount } from 'svelte';
	import NeoCard from '$lib/components/ui/NeoCard.svelte';

	type ClientBlame = {
		name: string;
		total_billed_usd: number;
		avg_effective_rate: number;
		avg_payment_wait: number;
	};

	let clients = $state<ClientBlame[]>([]);
	let loading = $state(true);
	let error = $state('');

	function getToken() {
		return localStorage.getItem('cornea_token');
	}

	onMount(async () => {
		try {
			const token = getToken();
			const res = await fetch('/api/blame', {
				headers: { Authorization: `Bearer ${token}` }
			});
			let allClients = (await res.json()) as ClientBlame[];
			allClients.sort((a, b) => a.avg_effective_rate - b.avg_effective_rate);
			if (allClients.length > 5) {
				const worst = allClients[0];
				const top4 = allClients.slice(-4);
				clients = [worst, ...top4];
			} else {
				clients = allClients;
			}
		} catch {
			error = 'Failed to load blame data.';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Git Blame | Cornea</title>
</svelte:head>

<div class="page-header">
	<h1>blame</h1>
	<p class="subtitle">Which client is actually costing you money?</p>
</div>

{#if loading}
	<p class="loading">Running analysis...</p>
{:else if error}
	<div class="empty-state">
		<p>{error}</p>
	</div>
{:else if clients.length === 0}
	<div class="empty-state">
		<p>No client data found.</p>
	</div>
{:else}
	<div class="grid">
		{#each clients as c, i (c.name)}
			<NeoCard
				variant={i === 0 ? 'worst' : i === clients.length - 1 ? 'best' : 'default'}
				class="!p-6"
			>
				{#if i === 0}
					<div class="badge worst-badge">WORST CLIENT</div>
				{:else if i === clients.length - 1}
					<div class="badge best-badge">BEST CLIENT</div>
				{/if}

				<h2>{c.name}</h2>
				<div class="stats">
					<div class="stat">
						<span class="label">Total Billed (USD):</span>
						<span class="value">${c.total_billed_usd.toFixed(2)}</span>
					</div>
					<div class="stat">
						<span class="label">True Effective Rate:</span>
						<span class="value">${c.avg_effective_rate.toFixed(2)}/hr</span>
					</div>
					<div class="stat">
						<span class="label">Avg Payment Delay:</span>
						<span class="value">{c.avg_payment_wait.toFixed(0)} days</span>
					</div>
				</div>
			</NeoCard>
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
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 2rem;
	}
	.badge {
		position: absolute;
		top: -15px;
		right: -15px;
		padding: 0.25rem 0.75rem;
		font-weight: 900;
		border: 3px solid var(--theme-line);
		box-shadow: 4px 4px 0 var(--theme-line);
		font-size: 0.8rem;
	}
	.worst-badge {
		background: #cc0000;
		color: white;
		border-radius: 0.75rem;
	}
	.best-badge {
		background: #155724;
		color: white;
		border-radius: 0.75rem;
	}
	h2 {
		margin-top: 0.5rem;
		margin-bottom: 1.5rem;
		font-size: 1.5rem;
	}
	.stat {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		font-size: 1.1rem;
	}
	.stat .label {
		font-weight: bold;
	}
</style>
