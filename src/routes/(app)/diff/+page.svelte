<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';
	import NeoCard from '$lib/components/ui/NeoCard.svelte';
	import { primaryCurrency, toLocal } from '$lib/stores/exchange';

	type Client = { name: string; billed: number; wait_days: number; effective_rate: number };
	type Snapshot = {
		id: number;
		date: string;
		source: string;
		invoiced_usd: number;
		fees_usd: number;
		received_usd: number;
		effective_rate: number;
		avg_payment_wait: number;
		clients: Client[];
	};
	type Delta = {
		invoiced_usd: number;
		fees_usd: number;
		received_usd: number;
		effective_rate: number;
		avg_payment_wait: number;
		client_count: number;
	};
	type DiffResult = {
		base: Snapshot;
		compare: Snapshot;
		delta: Delta;
	};
	type LogSnapshot = {
		id: number;
		created_at: string;
		source: string;
		total_invoiced_usd: number;
	};

	let snapshots = $state<LogSnapshot[]>([]);
	let baseId = $state<number | null>(null);
	let compareId = $state<number | null>(null);

	let diff = $state<DiffResult | null>(null);
	let insight = $state<string | null>(null);
	
	let loadingSnapshots = $state(true);
	let loadingDiff = $state(false);
	let loadingInsight = $state(false);
	let error = $state<string | null>(null);

	function getToken() { return localStorage.getItem('cornea_token'); }

	onMount(async () => {
		try {
			const token = getToken();
			if (!token) {
				void goto('/auth');
				return;
			}
			const res = await fetch('/api/log', { headers: { Authorization: `Bearer ${token}` } });
			if (res.status === 401) {
				localStorage.removeItem('cornea_token');
				void goto('/auth');
				return;
			}
			const data = await res.json();
			if (data.snapshots) {
				snapshots = data.snapshots;
				if (snapshots.length >= 2) {
					compareId = snapshots[0].id; // newest
					baseId = snapshots[1].id; // older
				}
			}
		} catch (e) {
			error = 'Failed to load snapshots.';
		} finally {
			loadingSnapshots = false;
		}
	});

	async function runMockSync() {
		const token = getToken();
		await fetch('/api/sync/mock', { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
		location.reload();
	}

	async function runDiff() {
		if (!baseId || !compareId) return;
		if (baseId === compareId) {
			alert("Select two different snapshots.");
			return;
		}

		loadingDiff = true;
		diff = null;
		insight = null;
		error = null;

		const token = getToken();
		try {
			const res = await fetch(`/api/diff?base=${baseId}&compare=${compareId}`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			const data = await res.json();
			if (data.error) throw new Error(data.error);
			diff = data;
			
			fetchInsight(data);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to run diff.';
		} finally {
			loadingDiff = false;
		}
	}

	async function fetchInsight(diffData: DiffResult) {
		loadingInsight = true;
		try {
			const token = getToken();
			const res = await fetch('/api/diff/insight', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
				body: JSON.stringify(diffData)
			});
			const data = await res.json();
			insight = data.insight;
		} catch (e) {
			insight = "Coach unavailable — read the numbers yourself.";
		} finally {
			loadingInsight = false;
		}
	}

	function formatLabel(s: LogSnapshot) {
		const date = new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
		const idStr = String(s.id).padStart(5, '0');
		return `commit ${idStr} · ${date} · $${s.total_invoiced_usd.toFixed(0)} · ${s.source}`;
	}

	function fmtUsd(v: number) { return `$${Math.abs(v).toFixed(2)}`; }
	function fmtLocal(vUsd: number) { return `${Math.abs(toLocal(vUsd)).toFixed(2)}`; }
	function sign(v: number) { return v > 0 ? '+' : v < 0 ? '-' : ''; }
	function pct(oldV: number, newV: number) {
		if (oldV === 0) return 0;
		return ((newV - oldV) / oldV) * 100;
	}
	function fmtPct(v: number) {
		const prefix = v > 0 ? '↑' : v < 0 ? '↓' : '';
		return `${prefix}${Math.abs(v).toFixed(1)}%`;
	}

	function getClientStatus(name: string, isBase: boolean) {
		if (!diff) return 'none';
		const inBase = diff.base.clients.some(c => c.name === name);
		const inCompare = diff.compare.clients.some(c => c.name === name);
		if (inBase && inCompare) return 'both';
		if (inBase && !inCompare && isBase) return 'gone';
		if (!inBase && inCompare && !isBase) return 'new';
		return 'none';
	}
	
	let localRateBase = $derived(toLocal(1));
</script>

<svelte:head>
	<title>Git Diff | Cornea</title>
</svelte:head>

<div class="page-header compact-header">
	<div class="header-title">
		<h1>diff</h1>
		<p class="subtitle">Comparing current income vs past reality.</p>
	</div>
</div>

{#if loadingSnapshots}
	<p class="loading">Loading snapshots...</p>
{:else if snapshots.length < 2}
	<div class="empty-state">
		<p>You need at least 2 syncs to run a diff.</p>
		<NeoButton onclick={runMockSync} class="mt-4">Run Mock Sync</NeoButton>
	</div>
{:else}
	<!-- TOP BAR: Selectors -->
	<NeoCard class="diff-controls-card mb-6">
		<div class="selectors-row">
			<div class="selector-group">
				<label for="base">Base Snapshot</label>
				<select id="base" bind:value={baseId}>
					{#each snapshots as s}
						<option value={s.id}>{formatLabel(s)}</option>
					{/each}
				</select>
			</div>
			<div class="arrow-icon">→</div>
			<div class="selector-group">
				<label for="compare">Compare Snapshot</label>
				<select id="compare" bind:value={compareId}>
					{#each snapshots as s}
						<option value={s.id}>{formatLabel(s)}</option>
					{/each}
				</select>
			</div>
			<NeoButton onclick={runDiff} disabled={loadingDiff} class="run-btn">
				{loadingDiff ? 'Running...' : 'Run Diff'}
			</NeoButton>
		</div>
	</NeoCard>

	{#if error}
		<div class="error-msg mb-4">{error}</div>
	{/if}

	{#if diff}
		<!-- SECTION 1: STAT DIFF CARDS -->
		<div class="stat-cards-grid mb-8">
			<!-- Invoiced USD -->
			<NeoCard class="stat-card">
				<div class="stat-label">Invoiced USD</div>
				<div class="stat-values">
					<span class="old">{fmtUsd(diff.base.invoiced_usd)}</span> → 
					<span class="new">{fmtUsd(diff.compare.invoiced_usd)}</span>
				</div>
				<div class="stat-delta {diff.delta.invoiced_usd >= 0 ? 'good' : 'bad'}">
					{sign(diff.delta.invoiced_usd)}{fmtUsd(diff.delta.invoiced_usd)} 
					<span class="pct">{fmtPct(pct(diff.base.invoiced_usd, diff.compare.invoiced_usd))}</span>
				</div>
			</NeoCard>

			<!-- Real Local -->
			<NeoCard class="stat-card">
				<div class="stat-label">Real Local Received</div>
				<div class="stat-values">
					<span class="old">{fmtLocal(diff.base.received_usd)}</span> → 
					<span class="new">{fmtLocal(diff.compare.received_usd)}</span>
				</div>
				<div class="stat-delta {diff.delta.received_usd >= 0 ? 'good' : 'bad'}">
					{sign(diff.delta.received_usd)}{fmtLocal(diff.delta.received_usd)} {$primaryCurrency}
					<span class="pct">{fmtPct(pct(diff.base.received_usd, diff.compare.received_usd))}</span>
				</div>
			</NeoCard>

			<!-- Effective Hourly Rate -->
			<NeoCard class="stat-card">
				<div class="stat-label">Effective Hourly Rate</div>
				<div class="stat-values">
					<span class="old">${diff.base.effective_rate.toFixed(2)}/hr</span> → 
					<span class="new">${diff.compare.effective_rate.toFixed(2)}/hr</span>
				</div>
				<div class="stat-delta {diff.delta.effective_rate >= 0 ? 'good' : 'bad'}">
					{sign(diff.delta.effective_rate)}${Math.abs(diff.delta.effective_rate).toFixed(2)}
					<span class="pct">{fmtPct(pct(diff.base.effective_rate, diff.compare.effective_rate))}</span>
				</div>
			</NeoCard>

			<!-- Fees Lost -->
			<NeoCard class="stat-card">
				<div class="stat-label">Fees Lost</div>
				<div class="stat-values">
					<span class="old">{fmtUsd(diff.base.fees_usd)}</span> → 
					<span class="new">{fmtUsd(diff.compare.fees_usd)}</span>
				</div>
				<!-- Fees are bad if they go UP, so delta > 0 is 'bad' -->
				<div class="stat-delta {diff.delta.fees_usd > 0 ? 'bad' : 'good'}">
					{sign(diff.delta.fees_usd)}{fmtUsd(diff.delta.fees_usd)}
					<span class="pct">{fmtPct(pct(diff.base.fees_usd, diff.compare.fees_usd))}</span>
				</div>
			</NeoCard>
		</div>

		<!-- SECTION 2: THE DIFF TABLE -->
		<h2 class="section-title">Git Diff breakdown</h2>
		<div class="diff-table-container mb-8">
			<table class="git-diff-table">
				<thead>
					<tr>
						<th>METRIC</th>
						<th>BASE</th>
						<th>COMPARE</th>
						<th>DELTA</th>
					</tr>
				</thead>
				<tbody>
					<tr class={diff.delta.invoiced_usd > 0 ? 'line-add' : diff.delta.invoiced_usd < 0 ? 'line-rm' : 'line-neutral'}>
						<td>{sign(diff.delta.invoiced_usd) || '~'} Invoiced USD</td>
						<td>{fmtUsd(diff.base.invoiced_usd)}</td>
						<td>{fmtUsd(diff.compare.invoiced_usd)}</td>
						<td>{sign(diff.delta.invoiced_usd)}{fmtUsd(diff.delta.invoiced_usd)} {fmtPct(pct(diff.base.invoiced_usd, diff.compare.invoiced_usd))}</td>
					</tr>
					<tr class={diff.delta.received_usd > 0 ? 'line-add' : diff.delta.received_usd < 0 ? 'line-rm' : 'line-neutral'}>
						<td>{sign(diff.delta.received_usd) || '~'} Net USD</td>
						<td>{fmtUsd(diff.base.received_usd)}</td>
						<td>{fmtUsd(diff.compare.received_usd)}</td>
						<td>{sign(diff.delta.received_usd)}{fmtUsd(diff.delta.received_usd)} {fmtPct(pct(diff.base.received_usd, diff.compare.received_usd))}</td>
					</tr>
					<!-- Fees invert the color logic: increase is bad (red) -->
					<tr class={diff.delta.fees_usd < 0 ? 'line-add' : diff.delta.fees_usd > 0 ? 'line-rm' : 'line-neutral'}>
						<td>{sign(diff.delta.fees_usd) || '~'} Fees USD</td>
						<td>{fmtUsd(diff.base.fees_usd)}</td>
						<td>{fmtUsd(diff.compare.fees_usd)}</td>
						<td>{sign(diff.delta.fees_usd)}{fmtUsd(diff.delta.fees_usd)}</td>
					</tr>
					<!-- Highlight row if USD jumped but Local barely moved due to exchange rate -->
					<tr class={diff.delta.received_usd > 0 ? 'line-add' : diff.delta.received_usd < 0 ? 'line-rm' : 'line-neutral'}>
						<td>{sign(diff.delta.received_usd) || '~'} Real Local</td>
						<td>{fmtLocal(diff.base.received_usd)}</td>
						<td>{fmtLocal(diff.compare.received_usd)}</td>
						<td>{sign(diff.delta.received_usd)}{fmtLocal(diff.delta.received_usd)}</td>
					</tr>
					<!-- Wait days: lower is better -->
					<tr class={diff.delta.avg_payment_wait < 0 ? 'line-add' : diff.delta.avg_payment_wait > 0 ? 'line-rm' : 'line-neutral'}>
						<td>{sign(diff.delta.avg_payment_wait) || '~'} Avg Payment Wait</td>
						<td>{diff.base.avg_payment_wait} days</td>
						<td>{diff.compare.avg_payment_wait} days</td>
						<td>{sign(diff.delta.avg_payment_wait)}{Math.abs(diff.delta.avg_payment_wait)} days</td>
					</tr>
					<tr class={diff.delta.client_count > 0 ? 'line-add' : diff.delta.client_count < 0 ? 'line-rm' : 'line-neutral'}>
						<td>{sign(diff.delta.client_count) || '~'} Active Clients</td>
						<td>{diff.base.clients.length}</td>
						<td>{diff.compare.clients.length}</td>
						<td>{sign(diff.delta.client_count)}{Math.abs(diff.delta.client_count)}</td>
					</tr>
					<tr class="line-neutral">
						<td>~ Exchange Rate</td>
						<td>{localRateBase.toFixed(2)}</td>
						<td>{localRateBase.toFixed(2)}</td>
						<td>~0.00</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- SECTION 3: CLIENT DIFF -->
		{#if diff.base.clients.length > 0 || diff.compare.clients.length > 0}
			<h2 class="section-title">Client Roster Changes</h2>
			<div class="client-diff-grid mb-8">
				<div class="client-col">
					<h3>Base Clients</h3>
					{#each diff.base.clients as client}
						<div class="client-row {getClientStatus(client.name, true)}">
							<div class="client-name">
								{client.name}
								{#if getClientStatus(client.name, true) === 'gone'}
									<span class="badge gone">GONE</span>
								{/if}
							</div>
							<div class="client-meta">{fmtUsd(client.billed)} | {client.wait_days}d wait</div>
						</div>
					{/each}
				</div>
				<div class="client-col">
					<h3>Compare Clients</h3>
					{#each diff.compare.clients as client}
						<div class="client-row {getClientStatus(client.name, false)}">
							<div class="client-name">
								{client.name}
								{#if getClientStatus(client.name, false) === 'new'}
									<span class="badge new">NEW</span>
								{/if}
							</div>
							<div class="client-meta">{fmtUsd(client.billed)} | {client.wait_days}d wait</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- SECTION 4: AI COACH INSIGHT -->
		<h2 class="section-title">AI Coach Insight</h2>
		<NeoCard class="insight-card">
			{#if loadingInsight}
				<div class="skeleton-text"></div>
				<div class="skeleton-text short"></div>
			{:else if insight}
				<p class="insight-text">{insight}</p>
			{:else}
				<p class="insight-text text-muted">No insight available.</p>
			{/if}
		</NeoCard>
	{/if}
{/if}

<style>
	.compact-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	h1 {
		font-size: 2.5rem;
		margin: 0;
		text-transform: lowercase;
		line-height: 1;
	}
	.subtitle {
		color: var(--theme-muted);
		font-size: 1rem;
		margin-top: 0.25rem;
		margin-bottom: 0;
	}
	.section-title {
		font-size: 1.2rem;
		text-transform: uppercase;
		border-bottom: 2px solid var(--theme-line);
		padding-bottom: 0.25rem;
		margin-bottom: 1rem;
	}

	:global(.diff-controls-card) {
		padding: 1rem !important;
		height: auto !important;
	}
	.selectors-row {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
	}
	.selector-group {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 200px;
	}
	.selector-group label {
		font-size: 0.8rem;
		text-transform: uppercase;
		font-weight: bold;
		margin-bottom: 0.25rem;
	}
	select {
		padding: 0.5rem;
		border: 2px solid var(--theme-line);
		border-radius: 0.4rem;
		background: var(--theme-bg);
		font-family: inherit;
		font-size: 0.9rem;
	}
	.arrow-icon {
		font-size: 1.5rem;
		font-weight: bold;
		color: var(--theme-muted);
		margin-top: 1rem;
	}
	.run-btn {
		margin-top: 1.2rem;
	}

	.stat-cards-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}
	:global(.stat-card) {
		padding: 1rem !important;
		height: auto !important;
	}
	.stat-label {
		font-size: 0.8rem;
		text-transform: uppercase;
		font-weight: bold;
		color: var(--theme-muted);
		margin-bottom: 0.5rem;
	}
	.stat-values {
		font-size: 1.1rem;
		font-weight: 800;
		margin-bottom: 0.5rem;
	}
	.stat-values .old { color: var(--theme-muted); text-decoration: line-through; }
	.stat-delta {
		font-size: 1rem;
		font-weight: 900;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.stat-delta.good { color: #28a745; }
	.stat-delta.bad { color: #dc3545; }
	.stat-delta .pct {
		font-size: 0.8rem;
		padding: 0.1rem 0.3rem;
		border-radius: 4px;
		background: rgba(0,0,0,0.05);
	}

	.diff-table-container {
		background: var(--theme-paper);
		border: 3px solid var(--theme-line);
		border-radius: 0.5rem;
		box-shadow: 4px 4px 0 var(--theme-shadow);
		overflow-x: auto;
	}
	.git-diff-table {
		width: 100%;
		border-collapse: collapse;
		font-family: monospace;
		font-size: 0.95rem;
	}
	.git-diff-table th, .git-diff-table td {
		padding: 0.5rem 1rem;
		text-align: left;
		border-bottom: 1px solid rgba(0,0,0,0.1);
	}
	.git-diff-table th {
		background: var(--theme-bg);
		font-family: inherit;
		text-transform: uppercase;
		font-size: 0.85rem;
		border-bottom: 2px solid var(--theme-line);
	}
	.line-add { background: #d4edda; color: #155724; }
	.line-rm { background: #f8d7da; color: #721c24; }
	.line-neutral { background: transparent; color: var(--theme-text); }
	
	.client-diff-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}
	@media (max-width: 768px) {
		.client-diff-grid { grid-template-columns: 1fr; }
	}
	.client-col h3 {
		font-size: 1rem;
		margin-bottom: 0.5rem;
		text-transform: uppercase;
	}
	.client-row {
		padding: 0.75rem;
		border: 2px solid var(--theme-line);
		border-radius: 0.4rem;
		margin-bottom: 0.5rem;
		background: var(--theme-paper);
		height: auto;
	}
	.client-row.gone { border-color: #dc3545; background: #fdf2f2; }
	.client-row.new { border-color: #28a745; background: #f2fdf2; }
	.client-row.both { border-style: dashed; }
	.client-name {
		font-weight: bold;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.client-meta {
		font-size: 0.85rem;
		color: var(--theme-muted);
		margin-top: 0.2rem;
	}
	.badge {
		font-size: 0.65rem;
		padding: 0.15rem 0.4rem;
		border-radius: 999px;
		font-weight: 800;
	}
	.badge.gone { background: #dc3545; color: white; }
	.badge.new { background: #28a745; color: white; }

	.insight-text {
		font-size: 1.1rem;
		line-height: 1.5;
		font-weight: 500;
	}
	.skeleton-text {
		height: 1rem;
		background: #e2e3e5;
		border-radius: 4px;
		margin-bottom: 0.5rem;
		animation: pulse 1.5s infinite;
	}
	.skeleton-text.short { width: 60%; }
	@keyframes pulse {
		0% { opacity: 0.6; }
		50% { opacity: 0.3; }
		100% { opacity: 0.6; }
	}
	.mb-4 { margin-bottom: 1rem; }
	.mb-6 { margin-bottom: 1.5rem; }
	.mb-8 { margin-bottom: 2rem; }
	.mt-4 { margin-top: 1rem; }
	.text-muted { color: var(--theme-muted); }
	.error-msg {
		padding: 0.75rem;
		background: #f8d7da;
		color: #721c24;
		border: 2px solid #721c24;
		border-radius: 0.5rem;
		font-weight: bold;
		font-size: 0.9rem;
	}
</style>
