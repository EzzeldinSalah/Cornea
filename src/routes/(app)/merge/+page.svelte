<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';
	import NeoCard from '$lib/components/ui/NeoCard.svelte';
	import { primaryCurrency, toLocal } from '$lib/stores/exchange';

	type IncomeSource = {
		id: string;
		platform: string;
		name: string;
		status: 'connected' | 'manual' | 'not connected';
		last_sync?: string;
	};

	type Transaction = {
		id: string;
		date: string;
		source: string;
		client_description: string;
		amount_usd: number;
		amount_local: number;
		platform_fee: number;
		net_received: number;
	};

	type Reconciliation = {
		total_usd: number;
		total_local: number;
		total_fees: number;
		kept_percentage: number;
		sources: { name: string; contribution_usd: number }[];
	};

	let sources = $state<IncomeSource[]>([
		{ id: '1', platform: 'Upwork', name: 'Upwork Global', status: 'connected', last_sync: new Date().toISOString() },
		{ id: '2', platform: 'Freelancer', name: 'Freelancer.com', status: 'not connected' },
		{ id: '3', platform: 'Mostaql', name: 'Mostaql Account', status: 'connected', last_sync: new Date().toISOString() }
	]);
	let transactions = $state<Transaction[]>([
		{ id: 'tx1', date: new Date().toISOString(), source: 'Upwork', client_description: 'Web Development', amount_usd: 850, amount_local: 0, platform_fee: 85, net_received: 765 },
		{ id: 'tx2', date: new Date(Date.now() - 86400000).toISOString(), source: 'Mostaql', client_description: 'UI Design', amount_usd: 300, amount_local: 0, platform_fee: 60, net_received: 240 },
		{ id: 'tx3', date: new Date(Date.now() - 172800000).toISOString(), source: 'Manual', client_description: 'Direct Client', amount_usd: 1200, amount_local: 0, platform_fee: 0, net_received: 1200 }
	]);
	let reconciliation = $state<Reconciliation | null>({
		total_usd: 2350,
		total_local: 0,
		total_fees: 145,
		kept_percentage: 93.8,
		sources: [
			{ name: 'Upwork', contribution_usd: 850 },
			{ name: 'Mostaql', contribution_usd: 300 },
			{ name: 'Manual', contribution_usd: 1200 }
		]
	});
	
	let loadingSources = $state(false);
	let loadingTimeline = $state(false);
	let loadingRecon = $state(false);
	let committing = $state(false);
	
	let commitMessage = $state('');
	let commitError = $state('');

	let currentPage = $state(1);
	const rowsPerPage = 20;

	let manualEntry = $state({
		description: '',
		amount: 0,
		currency: 'USD',
		date: new Date().toISOString().split('T')[0],
		source_label: 'Khamsat'
	});
	let isSubmittingManual = $state(false);

	function getToken() {
		return localStorage.getItem('cornea_token');
	}

	onMount(() => {
		const token = getToken();
		if (!token) {
			void goto('/auth');
			return;
		}
		void fetchSources(token);
		void fetchTimeline(token);
		void fetchReconciliation(token);
	});

	async function fetchSources(token: string) {
		try {
			const res = await fetch('/api/sources', { headers: { Authorization: `Bearer ${token}` } });
			if (res.ok) {
				const data = await res.json();
				if (data && data.length > 0) sources = data;
			}
		} catch (e) {
			console.error('Failed to fetch sources', e);
		} finally {
			loadingSources = false;
		}
	}

	async function fetchTimeline(token: string) {
		try {
			const res = await fetch('/api/merge/timeline', { headers: { Authorization: `Bearer ${token}` } });
			if (res.ok) {
				const data = await res.json();
				if (data && data.length > 0) {
					// Ensure sorting by date desc
					transactions = (data.transactions || data).sort((a: Transaction, b: Transaction) => 
						new Date(b.date).getTime() - new Date(a.date).getTime()
					);
				}
			}
		} catch (e) {
			console.error('Failed to fetch timeline', e);
		} finally {
			loadingTimeline = false;
		}
	}

	async function fetchReconciliation(token: string) {
		try {
			const res = await fetch('/api/merge/reconciliation', { headers: { Authorization: `Bearer ${token}` } });
			if (res.ok) {
				const data = await res.json();
				if (data && data.total_usd !== undefined) {
					reconciliation = data;
				}
			}
		} catch (e) {
			console.error('Failed to fetch reconciliation', e);
		} finally {
			loadingRecon = false;
		}
	}

	async function syncSource(id: string) {
		const token = getToken();
		try {
			await fetch(`/api/sources/${id}/sync`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${token}` }
			});
			void fetchSources(token!);
			void fetchTimeline(token!);
		} catch (e) {
			alert('Sync failed');
		}
	}

	async function submitManualEntry() {
		if (!manualEntry.description || !manualEntry.amount) {
			alert('Please fill out description and amount.');
			return;
		}
		isSubmittingManual = true;
		const token = getToken();
		try {
			const res = await fetch('/api/transactions/manual', {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(manualEntry)
			});
			if (res.ok) {
				manualEntry.description = '';
				manualEntry.amount = 0;
				void fetchTimeline(token!);
				void fetchReconciliation(token!);
			} else {
				alert('Failed to add manual entry');
			}
		} catch (e) {
			console.error(e);
		} finally {
			isSubmittingManual = false;
		}
	}

	async function commitMerge() {
		const token = getToken();
		committing = true;
		commitMessage = '';
		commitError = '';
		try {
			const res = await fetch('/api/merge/commit', {
				method: 'POST',
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				commitMessage = '✅ Snapshot committed — now visible in Log, Diff, Blame, and Analytics';
				void fetchTimeline(token!);
				void fetchReconciliation(token!);
			} else {
				const data = await res.json().catch(() => ({}));
				commitError = data.detail || 'Failed to commit snapshot.';
			}
		} catch (e) {
			commitError = 'Failed to commit snapshot.';
		} finally {
			committing = false;
		}
	}

	function formatUsd(val: number) {
		return `$${(val || 0).toFixed(2)}`;
	}

	function formatLocal(valUsd: number) {
		return `${toLocal(valUsd).toFixed(2)} ${$primaryCurrency}`;
	}

	function getSourceColor(source: string) {
		const s = source.toLowerCase();
		if (s.includes('upwork')) return '#0052cc'; // blue
		if (s.includes('freelancer')) return '#f5a623'; // yellow
		if (s.includes('mostaql')) return '#28a745'; // green
		if (s.includes('khamsat')) return '#fd7e14'; // orange
		return '#6c757d'; // gray for manual/other
	}

	let paginatedTransactions = $derived(
		transactions.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage)
	);
	let totalPages = $derived(Math.ceil(transactions.length / rowsPerPage));
</script>

<svelte:head>
	<title>Merge | Cornea</title>
</svelte:head>

<div class="page-header compact-header">
	<div class="header-title">
		<h1>merge</h1>
		<p class="subtitle">Consolidate all your income sources into a single timeline.</p>
	</div>
	<div class="header-action">
		<NeoButton 
			onclick={commitMerge} 
			disabled={committing || transactions.length === 0}
			class="commit-btn"
		>
			{committing ? 'Committing...' : 'Commit Merge Snapshot'}
		</NeoButton>
	</div>
</div>
{#if commitMessage}
	<div class="success-msg mb-4">{commitMessage}</div>
{/if}
{#if commitError}
	<div class="error-msg mb-4">{commitError}</div>
{/if}

<div class="recon-bar mb-6">
	<div class="recon-stats-inline">
		<div class="stat-inline">
			<span class="label">Total (USD)</span>
			<span class="val">{reconciliation ? formatUsd(reconciliation.total_usd) : '$0.00'}</span>
		</div>
		<div class="stat-inline">
			<span class="label">Total ({$primaryCurrency})</span>
			<span class="val local">{reconciliation ? formatLocal(reconciliation.total_usd) : '0.00'}</span>
		</div>
		<div class="stat-inline">
			<span class="label">Platform Fees</span>
			<span class="val danger">{reconciliation ? formatUsd(reconciliation.total_fees) : '$0.00'}</span>
		</div>
		<div class="stat-inline">
			<span class="label">Kept (%)</span>
			<span class="val success">{reconciliation ? reconciliation.kept_percentage.toFixed(1) : '0.0'}%</span>
		</div>
	</div>
</div>

<div class="main-split">
	<!-- Left Sidebar: Sources & Manual Entry -->
	<div class="sidebar-col">
		<section class="sources-section">
			<h2>Sources</h2>
			{#if loadingSources}
				<p class="loading">Loading sources...</p>
			{:else}
				<div class="compact-source-list">
					{#each sources as source}
						<div class="compact-source-row">
							<div class="source-info">
								<span class="source-name" style="color: {getSourceColor(source.platform)};">
									{source.name}
								</span>
							</div>
							<div class="source-actions">
								<span class="badge {source.status.replace(' ', '-')}">{source.status}</span>
								{#if source.status === 'connected'}
									<NeoButton onclick={() => syncSource(source.id)} class="btn-sm">Sync</NeoButton>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{/if}

			<div class="mt-8">
				<h2>Add Manual Entry</h2>
				<div class="compact-manual-form">
					<input type="text" bind:value={manualEntry.description} placeholder="Description" />
					<div class="flex gap-2">
						<input type="number" bind:value={manualEntry.amount} placeholder="Amount" class="flex-1" />
						<select bind:value={manualEntry.currency} class="w-auto">
							<option value="USD">USD</option>
						</select>
					</div>
					<div class="flex gap-2">
						<input type="date" bind:value={manualEntry.date} class="flex-1" />
						<select bind:value={manualEntry.source_label} class="w-auto">
							<option value="Khamsat">Khamsat</option>
							<option value="Mostaql">Mostaql</option>
							<option value="Other">Other</option>
						</select>
					</div>
					<NeoButton onclick={submitManualEntry} disabled={isSubmittingManual} class="w-full">
						{isSubmittingManual ? 'Adding...' : 'Add'}
					</NeoButton>
				</div>
			</div>
		</section>
	</div>

	<!-- Right Main: Timeline -->
	<div class="timeline-col">
		<section class="timeline-section">
			<div class="flex justify-between items-end mb-4">
				<h2>Merged Timeline</h2>
				<div class="pagination">
					<button disabled={currentPage === 1} onclick={() => currentPage--}>&lt;</button>
					<span>{currentPage} / {Math.max(1, totalPages)}</span>
					<button disabled={currentPage >= totalPages} onclick={() => currentPage++}>&gt;</button>
				</div>
			</div>

			<div class="table-responsive">
				<table class="theme-table">
					<thead>
						<tr>
							<th>Date</th>
							<th>Source</th>
							<th>Client/Description</th>
							<th>Gross (USD)</th>
							<th>Local</th>
							<th>Fee</th>
							<th>Net</th>
						</tr>
					</thead>
					<tbody>
						{#if loadingTimeline}
							<tr><td colspan="7" class="text-center p-4">Loading timeline...</td></tr>
						{:else if paginatedTransactions.length === 0}
							<tr><td colspan="7" class="text-center p-4">No unmerged transactions found.</td></tr>
						{:else}
							{#each paginatedTransactions as t}
								<tr>
									<td class="whitespace-nowrap">{new Date(t.date).toLocaleDateString()}</td>
									<td>
										<span class="source-badge" style="background: {getSourceColor(t.source)};">
											{t.source}
										</span>
									</td>
									<td><strong>{t.client_description}</strong></td>
									<td>{formatUsd(t.amount_usd)}</td>
									<td class="local-val">{t.amount_local > 0 ? t.amount_local.toFixed(2) : toLocal(t.amount_usd).toFixed(2)}</td>
									<td class="danger">-{formatUsd(t.platform_fee)}</td>
									<td class="success">{formatUsd(t.net_received)}</td>
								</tr>
							{/each}
						{/if}
					</tbody>
				</table>
			</div>
		</section>
	</div>
</div>

<style>
	.compact-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	h1 {
		font-size: 2.5rem;
		margin: 0;
		text-transform: lowercase;
		line-height: 1;
	}
	h2 {
		font-size: 1.2rem;
		margin-bottom: 1rem;
		text-transform: uppercase;
		border-bottom: 2px solid var(--theme-line);
		padding-bottom: 0.25rem;
	}
	.subtitle {
		color: var(--theme-muted);
		font-size: 1rem;
		margin-top: 0.25rem;
		margin-bottom: 0;
	}

	.recon-bar {
		background: var(--theme-paper);
		border: 3px solid var(--theme-line);
		border-radius: 0.5rem;
		padding: 1rem;
		box-shadow: 4px 4px 0 var(--theme-shadow);
	}

	.recon-stats-inline {
		display: flex;
		flex-wrap: wrap;
		gap: 2rem;
		justify-content: space-between;
		align-items: center;
	}

	.stat-inline {
		display: flex;
		flex-direction: column;
	}
	.stat-inline .label {
		font-size: 0.75rem;
		color: var(--theme-muted);
		text-transform: uppercase;
		font-weight: bold;
	}
	.stat-inline .val {
		font-size: 1.2rem;
		font-weight: 900;
	}

	.main-split {
		display: grid;
		grid-template-columns: 1fr;
		gap: 2rem;
	}

	@media (min-width: 1024px) {
		.main-split {
			grid-template-columns: 300px 1fr;
		}
	}

	.compact-source-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.compact-source-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: var(--theme-paper);
		border: 2px solid var(--theme-line);
		padding: 0.5rem 0.75rem;
		border-radius: 0.5rem;
	}
	.source-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.source-name {
		font-weight: 800;
		font-size: 0.95rem;
		text-transform: uppercase;
		line-height: 1.2;
	}

	.source-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.badge {
		font-size: 0.65rem;
		padding: 0.15rem 0.4rem;
		border-radius: 999px;
		font-weight: 800;
		text-transform: uppercase;
		border: 2px solid var(--theme-line);
	}
	.badge.connected { background: #d4edda; color: #155724; }
	.badge.manual { background: #e2e3e5; color: #383d41; }
	.badge.not.connected { background: #f8d7da; color: #721c24; }

	:global(.btn-sm) {
		padding: 0.3rem 0.6rem !important;
		font-size: 0.75rem !important;
	}

	.compact-manual-form {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	input, select {
		width: 100%;
		padding: 0.5rem;
		border: 2px solid var(--theme-line);
		border-radius: 0.4rem;
		background: var(--theme-bg);
		color: var(--theme-text);
		font-family: inherit;
		font-size: 0.9rem;
		outline: none;
	}
	input:focus, select:focus {
		box-shadow: 2px 2px 0 var(--theme-accent);
		transform: translate(-1px, -1px);
	}

	.success-msg {
		padding: 0.75rem;
		background: #d4edda;
		color: #155724;
		border: 2px solid #155724;
		border-radius: 0.5rem;
		font-weight: bold;
		font-size: 0.9rem;
	}
	.error-msg {
		padding: 0.75rem;
		background: #f8d7da;
		color: #721c24;
		border: 2px solid #721c24;
		border-radius: 0.5rem;
		font-weight: bold;
		font-size: 0.9rem;
	}

	.pagination {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: bold;
	}
	.pagination button {
		background: var(--theme-paper);
		border: 3px solid var(--theme-line);
		padding: 0.2rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-weight: 900;
		box-shadow: 2px 2px 0 var(--theme-shadow);
	}
	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		box-shadow: none;
		transform: none;
	}
	.pagination button:not(:disabled):hover {
		transform: translate(-1px, -1px);
		box-shadow: 3px 3px 0 var(--theme-shadow);
	}

	.table-responsive {
		width: 100%;
		overflow-x: auto;
		border-radius: 0.5rem;
		box-shadow: 4px 4px 0 var(--theme-shadow);
		border: 3px solid var(--theme-line);
	}

	.theme-table {
		width: 100%;
		border-collapse: collapse;
		background: var(--theme-paper);
	}
	.theme-table th,
	.theme-table td {
		padding: 0.6rem 0.8rem;
		border: 2px solid var(--theme-line);
		text-align: left;
		font-size: 0.9rem;
	}
	.theme-table th {
		background: var(--theme-bg);
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.8rem;
	}
	
	.source-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 800;
		color: white;
		text-transform: uppercase;
		border: 2px solid var(--theme-line);
	}
	
	.local-val {
		font-weight: bold;
		color: var(--theme-accent);
	}
	.whitespace-nowrap {
		white-space: nowrap;
	}
	.text-center {
		text-align: center;
	}
	.w-full { width: 100%; }
	.w-auto { width: auto; }
	.flex-1 { flex: 1; }
	.mt-2 { margin-top: 0.5rem; }
	.mt-8 { margin-top: 2rem; }
	.mb-4 { margin-bottom: 1rem; }
	.mb-6 { margin-bottom: 1.5rem; }
	.p-4 { padding: 1rem; }
	.flex { display: flex; }
	.gap-2 { gap: 0.5rem; }
	.justify-between { justify-content: space-between; }
	.items-end { align-items: flex-end; }
	.val.local { color: var(--theme-accent); }
	.danger { color: #dc3545; }
	.success { color: #28a745; }
</style>
