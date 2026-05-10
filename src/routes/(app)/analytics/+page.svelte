<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import NeoCard from '$lib/components/ui/NeoCard.svelte';
	import { primaryCurrency, toLocal } from '$lib/stores/exchange';

	type MonthlyDatum = {
		month: string;
		month_key?: string;
		invoiced_usd: number;
		received_usd: number;
		effective_rate?: number;
	};

	type ClientDatum = {
		name: string;
		total_usd: number;
		effective_rate: number;
		avg_payment_days: number;
	};

	type ForecastDatum = {
		month: string;
		projected_usd: number;
		confidence_low_usd: number;
		confidence_high_usd: number;
	};

	type TimelineEntry = {
		date: string;
		wait_days: number;
	};

	type TimelineLane = {
		name: string;
		entries: TimelineEntry[];
	};

	type MonthSummary = {
		month: string;
		income_usd: number;
		effective_rate: number;
	} | null;

	type AnalyticsData = {
		period: string;
		total_invoiced_usd: number;
		total_received_usd: number;
		effective_hourly_rate: number;
		total_fees_usd: number;
		monthly: MonthlyDatum[];
		clients: ClientDatum[];
		fee_breakdown: { upwork_pct: number; transfer_pct: number; kept_pct: number };
		inflation_index: { month: string; index_value: number }[];
		forecast: ForecastDatum[];
		timeline: TimelineLane[];
		best_month: MonthSummary;
		worst_month: MonthSummary;
	};

	let selectedView = $state('reality');
	let selectedPeriod = $state('30d');
	let isTransitioning = $state(false);
	let loading = $state(true);
	let error = $state('');

	let data = $state<AnalyticsData>({
		period: '30d',
		total_invoiced_usd: 0,
		total_received_usd: 0,
		effective_hourly_rate: 0,
		total_fees_usd: 0,
		monthly: [],
		clients: [],
		fee_breakdown: { upwork_pct: 0, transfer_pct: 0, kept_pct: 0 },
		inflation_index: [],
		forecast: [],
		timeline: [],
		best_month: null,
		worst_month: null
	});

	const views = [
		{ id: 'reality', label: 'The Reality Check' },
		{ id: 'fees', label: 'Where Your Money Went' },
		{ id: 'clients', label: 'Client Report Card' },
		{ id: 'inflation', label: 'Your Rate vs Inflation' },
		{ id: 'timeline', label: 'Payment Timeline' },
		{ id: 'bestworst', label: 'Best vs Worst' },
		{ id: 'forecast', label: 'Forecast' }
	];

	const periods = [
		{ id: '30d', label: 'Last 30 days' },
		{ id: '3m', label: 'Last 3 months' },
		{ id: 'this_quarter', label: 'This quarter' },
		{ id: '6m', label: 'Last 6 months' },
		{ id: 'this_year', label: 'This year' },
		{ id: '12m', label: 'Last 12 months (rolling)' },
		{ id: 'all_time', label: 'Since I joined Upwork (all time)' }
	];

	function getToken() {
		return localStorage.getItem('cornea_token');
	}

	function handleViewChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const newView = target.value;
		if (newView !== selectedView) {
			isTransitioning = true;
			setTimeout(() => {
				selectedView = newView;
				setTimeout(() => {
					isTransitioning = false;
				}, 150);
			}, 150);
		}
	}

	async function loadAnalytics(period = selectedPeriod) {
		const token = getToken();
		if (!token) {
			void goto(resolve('/auth'));
			return;
		}

		loading = true;
		error = '';
		try {
			const res = await fetch('/api/analytics?period=' + encodeURIComponent(period), {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.status === 401) {
				localStorage.removeItem('cornea_token');
				void goto(resolve('/auth'));
				return;
			}
			if (!res.ok) {
				const body = await res.json().catch(() => ({}));
				throw new Error(body.detail || 'Failed to load analytics.');
			}

			const fetched = (await res.json()) as Partial<AnalyticsData>;
			data = {
				...data,
				...fetched,
				fee_breakdown: { ...data.fee_breakdown, ...fetched.fee_breakdown }
			};
		} catch (caughtError) {
			error = caughtError instanceof Error ? caughtError.message : 'Failed to load analytics.';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		void loadAnalytics();
	});

	function handlePeriodChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		selectedPeriod = target.value;
		void loadAnalytics(selectedPeriod);
	}

	function getMax<T extends Record<string, unknown>>(arr: T[], key: keyof T) {
		return Math.max(...arr.map((d) => Number(d[key]) || 0), 0.1);
	}

	function formatUsd(value: number) {
		return `$${value.toLocaleString(undefined, {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		})}`;
	}

	function formatLocal(valueUsd: number) {
		const currency = $primaryCurrency || 'USD';
		const amount = toLocal(valueUsd);
		return `${amount.toLocaleString(undefined, {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		})} ${currency}`;
	}

	function formatCompactUsd(value: number) {
		return `$${value.toLocaleString(undefined, {
			notation: 'compact',
			maximumFractionDigits: 1
		})}`;
	}

	function formatCompactLocal(valueUsd: number) {
		const currency = $primaryCurrency || 'USD';
		const amount = toLocal(valueUsd);
		return `${amount.toLocaleString(undefined, {
			notation: 'compact',
			maximumFractionDigits: 1
		})} ${currency}`;
	}
</script>

<svelte:head>
	<title>Analytics | Cornea</title>
</svelte:head>

<div class="page-header">
	<h1>analytics</h1>
	<p class="subtitle">Deep insights into your freelance business.</p>
</div>

<div class="analytics-page">
	<div class="controls">
		<div class="control-group">
			<label for="view-select">View:</label>
			<select
				id="view-select"
				class="theme-select"
				value={selectedView}
				onchange={handleViewChange}
			>
				{#each views as v (v.id)}
					<option value={v.id}>{v.label}</option>
				{/each}
			</select>
		</div>

		{#if selectedView !== 'timeline'}
			<div class="control-group">
				<label for="period-select">Period:</label>
				<select
					id="period-select"
					class="theme-select"
					value={selectedPeriod}
					onchange={handlePeriodChange}
					disabled={loading}
				>
					{#each periods as p (p.id)}
						<option value={p.id}>{p.label}</option>
					{/each}
				</select>
			</div>
		{/if}
	</div>

	{#if error}
		<div class="notice error-notice">{error}</div>
	{:else if loading}
		<div class="notice">Loading analytics...</div>
	{/if}

	<div class="stat-cards">
		<NeoCard class="stat-card">
			<h3>Total Invoiced</h3>
			<p class="stat-val">{formatUsd(data.total_invoiced_usd)}</p>
		</NeoCard>
		<NeoCard class="stat-card">
			<h3>Real Local Received</h3>
			<p class="stat-val">{formatLocal(data.total_received_usd)}</p>
		</NeoCard>
		<NeoCard class="stat-card">
			<h3>Effective Rate</h3>
			<p class="stat-val">{formatUsd(data.effective_hourly_rate)} /hr</p>
		</NeoCard>
		<NeoCard class="stat-card">
			<h3>Fees Lost</h3>
			<p class="stat-val">{formatUsd(data.total_fees_usd)}</p>
		</NeoCard>
	</div>

	<div class="chart-container" class:faded={isTransitioning}>
		{#if isTransitioning || loading}
			<div class="skeleton"></div>
		{:else if error}
			<div class="chart-wrapper">
				<h3>Analytics unavailable</h3>
				<p class="chart-desc">{error}</p>
			</div>
		{:else if selectedView === 'reality'}
			<div class="chart-wrapper">
				<h3>The Reality Check</h3>
				<p class="chart-desc">What you invoiced vs what you actually received in local currency.</p>
				<div class="bar-chart-mirrored">
					{#each data.monthly as m (m.month_key || m.month)}
						<div class="bar-col">
							<div class="bar-group">
								<div
									class="bar bar-usd"
									style="height: {(m.invoiced_usd / getMax(data.monthly, 'invoiced_usd')) * 100}%;"
								>
									<span class="bar-label">{formatCompactUsd(m.invoiced_usd)}</span>
								</div>
								<div
									class="bar bar-local"
									style="height: {(m.received_usd / getMax(data.monthly, 'received_usd')) * 100}%;"
								>
									<span class="bar-label">{formatCompactLocal(m.received_usd)}</span>
								</div>
							</div>
							<p class="month-label">{m.month}</p>
						</div>
					{/each}
				</div>
				<div class="legend">
					<span class="legend-item"><span class="box box-usd"></span> Invoiced USD</span>
					<span class="legend-item"><span class="box box-local"></span> Received Local</span>
				</div>
			</div>
		{:else if selectedView === 'fees'}
			<div class="chart-wrapper">
				<h3>Where Your Money Went</h3>
				<p class="chart-desc">Fee breakdown flow as a horizontal stack.</p>
				<div class="stacked-bar-container">
					<div class="stacked-bar">
						<div class="segment segment-upwork" style="width: {data.fee_breakdown.upwork_pct}%">
							<span>Upwork ({data.fee_breakdown.upwork_pct}%)</span>
						</div>
						<div class="segment segment-transfer" style="width: {data.fee_breakdown.transfer_pct}%">
							<span>Transfer ({data.fee_breakdown.transfer_pct}%)</span>
						</div>
						<div class="segment segment-kept" style="width: {data.fee_breakdown.kept_pct}%">
							<span>You Kept ({data.fee_breakdown.kept_pct}%)</span>
						</div>
					</div>
					<p class="impact-text">
						Est. Annual Fee Loss: <strong>${(data.total_fees_usd * 12).toFixed(2)}</strong> USD
					</p>
				</div>
			</div>
		{:else if selectedView === 'clients'}
			<div class="chart-wrapper no-center">
				<h3>Client Report Card</h3>
				<p class="chart-desc">Your clients sorted by performance.</p>
				<div class="table-responsive">
					<table class="theme-table">
						<thead>
							<tr>
								<th>Client</th>
								<th>Total Earned (USD)</th>
								<th>Effective Rate</th>
								<th>Avg Payment Wait</th>
								<th>Score</th>
							</tr>
						</thead>
						<tbody>
							{#each data.clients as c (c.name)}
								<tr>
									<td><strong>{c.name}</strong></td>
									<td>{formatUsd(c.total_usd)}</td>
									<td>{formatUsd(c.effective_rate)}/hr</td>
									<td>{c.avg_payment_days} days</td>
									<td>
										{#if c.avg_payment_days <= 7}
											<span class="badge fast">Fast Payer</span>
										{:else if c.avg_payment_days <= 21}
											<span class="badge avg">Average</span>
										{:else}
											<span class="badge slow">Slow</span>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else if selectedView === 'inflation'}
			<div class="chart-wrapper">
				<h3>Your Rate vs Inflation</h3>
				<p class="chart-desc">Your effective rate trend compared to the local inflation index.</p>
				<div class="line-chart">
					<svg viewBox="0 0 100 100" preserveAspectRatio="none" class="svg-chart">
						<g stroke="var(--theme-accent)" stroke-width="2" fill="none">
							<path d="M 0,90 L 33,80 L 66,85 L 100,20" />
						</g>
						<g stroke="var(--theme-line)" stroke-width="2" fill="none" stroke-dasharray="2,2">
							<path d="M 0,50 L 33,60 L 66,55 L 100,45" />
						</g>
					</svg>
				</div>
				<div class="legend">
					<span class="legend-item"><span class="box box-usd"></span> Effective Rate</span>
					<span class="legend-item"
						><span class="box" style="background:var(--theme-line);"></span> Inflation</span
					>
				</div>
			</div>
		{:else if selectedView === 'timeline'}
			<div class="chart-wrapper">
				<h3>Payment Timeline</h3>
				<p class="chart-desc">A Gantt-like view of client payments.</p>
				<div class="timeline-lanes">
					{#each data.clients as c, i (c.name)}
						<div class="timeline-lane">
							<span class="lane-label">{c.name}</span>
							<div class="lane-track">
								<div class="time-block green" style="left: {i * 10}%; width: 15%;"></div>
								<div class="time-block yellow" style="left: {i * 10 + 20}%; width: 10%;"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else if selectedView === 'bestworst'}
			<div class="chart-wrapper no-center">
				<h3>Best vs Worst Month</h3>
				{#if data.best_month && data.worst_month}
					<div class="comparison-grid">
						<NeoCard class="best-card" variant="best">
							<h4>Best Month</h4>
							<p class="comp-stat">Income: {formatUsd(data.best_month.income_usd)}</p>
							<p class="comp-stat">Local: {formatLocal(data.best_month.income_usd)}</p>
							<p class="comp-stat">Effective: {formatUsd(data.best_month.effective_rate)}/hr</p>
						</NeoCard>
						<NeoCard class="worst-card" variant="worst">
							<h4>Worst Month</h4>
							<p class="comp-stat">Income: {formatUsd(data.worst_month.income_usd)}</p>
							<p class="comp-stat">Local: {formatLocal(data.worst_month.income_usd)}</p>
							<p class="comp-stat">Effective: {formatUsd(data.worst_month.effective_rate)}/hr</p>
						</NeoCard>
					</div>
					<div class="insight-box">
						<strong>Insight:</strong> Compare the best and worst months to spot whether volume, rate,
						or collection timing moved the needle.
					</div>
				{:else}
					<p class="chart-desc">Not enough monthly history yet.</p>
				{/if}
			</div>
		{:else if selectedView === 'forecast'}
			<div class="chart-wrapper">
				<h3>Forecast</h3>
				<p class="chart-desc">Projecting next 3 months based on historical pattern.</p>
				<div class="bar-chart-mirrored">
					{#each data.forecast as f (f.month)}
						<div class="bar-col">
							<div class="bar-group">
								<div
									class="bar bar-forecast"
									style="height: {(f.projected_usd / getMax(data.forecast, 'confidence_high_usd')) *
										100}%;"
								>
									<span class="bar-label">{formatCompactLocal(f.projected_usd)}</span>
								</div>
							</div>
							<p class="month-label">{f.month}</p>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

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

	.analytics-page {
		max-width: 1100px;
		margin: 0 auto;
	}

	.controls {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.control-group {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	label {
		font-weight: 700;
		text-transform: uppercase;
		font-size: 0.9rem;
		letter-spacing: 0.05em;
	}

	.theme-select {
		padding: 0.6rem 1rem;
		border: 3px solid var(--theme-line);
		border-radius: 0.5rem;
		background: var(--theme-bg);
		color: var(--theme-text);
		font-family: inherit;
		font-weight: 700;
		font-size: 0.95rem;
		outline: none;
		cursor: pointer;
		box-shadow: 3px 3px 0 var(--theme-shadow);
		transition:
			transform 0.1s,
			box-shadow 0.1s;
	}

	.theme-select:focus {
		transform: translate(-2px, -2px);
		box-shadow: 5px 5px 0 var(--theme-accent);
	}

	.theme-select:disabled {
		cursor: wait;
		opacity: 0.7;
	}

	.notice {
		margin-bottom: 1.5rem;
		padding: 1rem 1.25rem;
		border: 3px solid var(--theme-line);
		background: var(--theme-paper);
		box-shadow: 4px 4px 0 var(--theme-shadow);
		font-weight: 800;
	}

	.error-notice {
		background: #f8d7da;
		color: #721c24;
	}

	.stat-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2.5rem;
	}

	:global(.stat-card) h3 {
		font-family: inherit;
		font-size: 0.8rem;
		text-transform: uppercase;
		color: var(--theme-muted);
		margin-bottom: 0.5rem;
	}

	.stat-val {
		font-size: 1.8rem;
		font-weight: 900;
		color: var(--theme-text);
	}

	.chart-container {
		min-height: 450px;
		transition: opacity 0.15s ease-in-out;
		background: var(--theme-paper);
		border: 4px solid var(--theme-line);
		border-radius: 1rem;
		box-shadow: 6px 6px 0 var(--theme-shadow);
		padding: 2.5rem;
	}

	.chart-container.faded {
		opacity: 0;
	}

	.skeleton {
		width: 100%;
		height: 100%;
		min-height: 350px;
		background: linear-gradient(
			90deg,
			var(--theme-paper) 25%,
			var(--theme-bg) 50%,
			var(--theme-paper) 75%
		);
		background-size: 200% 100%;
		animation: loading 1.5s infinite;
		border-radius: 0.5rem;
	}

	@keyframes loading {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}

	.chart-wrapper {
		display: flex;
		flex-direction: column;
		height: 100%;
		width: 100%;
		align-items: center;
	}
	.chart-wrapper.no-center {
		align-items: flex-start;
	}

	.chart-wrapper h3 {
		font-size: 1.5rem;
		margin-bottom: 0.25rem;
	}

	.chart-desc {
		color: var(--theme-muted);
		margin-bottom: 2rem;
		text-align: center;
	}

	.bar-chart-mirrored {
		display: flex;
		align-items: flex-end;
		justify-content: space-evenly;
		width: 100%;
		height: 250px;
		border-bottom: 3px solid var(--theme-line);
		padding-bottom: 1rem;
		margin-bottom: 1.5rem;
	}

	.bar-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		height: 100%;
		width: 20%;
	}

	.bar-group {
		display: flex;
		gap: 0.5rem;
		align-items: flex-end;
		height: 100%;
		width: 100%;
		justify-content: center;
	}

	.bar {
		width: 30%;
		min-width: 15px;
		border: 2px solid var(--theme-line);
		border-bottom: none;
		border-radius: 4px 4px 0 0;
		position: relative;
		transition: height 0.3s ease;
	}

	.bar-usd {
		background: var(--theme-accent);
	}
	.bar-local {
		background: var(--theme-bg);
		border-style: dashed;
	}
	.bar-forecast {
		background: var(--theme-bg);
		border-style: dashed;
		border-color: var(--theme-line);
	}

	.bar-label {
		position: absolute;
		top: -1.75rem;
		left: 50%;
		transform: translateX(-50%);
		font-size: 0.75rem;
		font-weight: bold;
		white-space: nowrap;
	}

	.month-label {
		margin-top: 0.5rem;
		font-weight: 700;
		text-transform: uppercase;
	}

	.legend {
		display: flex;
		gap: 1.5rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: bold;
		font-size: 0.85rem;
	}

	.box {
		width: 1rem;
		height: 1rem;
		border: 2px solid var(--theme-line);
		border-radius: 2px;
	}
	.box-usd {
		background: var(--theme-accent);
	}
	.box-local {
		background: var(--theme-bg);
		border-style: dashed;
	}

	.stacked-bar-container {
		width: 100%;
		max-width: 700px;
	}

	.stacked-bar {
		display: flex;
		height: 3rem;
		width: 100%;
		border: 3px solid var(--theme-line);
		border-radius: 999px;
		overflow: hidden;
		margin-bottom: 2rem;
		box-shadow: 4px 4px 0 var(--theme-shadow);
	}

	.segment {
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.85rem;
		font-weight: bold;
		color: var(--theme-text);
		white-space: nowrap;
		overflow: hidden;
	}

	.segment-upwork {
		background: #ffcccc;
		border-right: 2px solid var(--theme-line);
	}
	.segment-transfer {
		background: #ffeebb;
		border-right: 2px solid var(--theme-line);
	}
	.segment-kept {
		background: #ccffcc;
	}

	.impact-text {
		text-align: center;
		font-size: 1.25rem;
	}

	.table-responsive {
		width: 100%;
		overflow-x: auto;
	}

	.theme-table {
		width: 100%;
		border-collapse: collapse;
		border: 3px solid var(--theme-line);
	}

	.theme-table th,
	.theme-table td {
		padding: 1rem;
		border: 2px solid var(--theme-line);
		text-align: left;
	}

	.theme-table th {
		background: var(--theme-bg);
		font-weight: 800;
		text-transform: uppercase;
	}

	.badge {
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 800;
		border: 2px solid var(--theme-line);
		text-transform: uppercase;
	}

	.badge.fast {
		background: #ccffcc;
	}
	.badge.avg {
		background: var(--theme-bg);
		border-color: var(--theme-muted);
	}
	.badge.slow {
		background: #ffcccc;
		color: #cc0000;
		border-color: #cc0000;
	}

	.line-chart {
		width: 100%;
		height: 250px;
		border-bottom: 3px solid var(--theme-line);
		border-left: 3px solid var(--theme-line);
		margin-bottom: 1.5rem;
		position: relative;
	}
	.svg-chart {
		width: 100%;
		height: 100%;
	}

	.timeline-lanes {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.timeline-lane {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.lane-label {
		width: 120px;
		font-weight: bold;
		text-align: right;
	}

	.lane-track {
		flex: 1;
		height: 2.5rem;
		background: var(--theme-bg);
		border: 2px solid var(--theme-line);
		border-radius: 4px;
		position: relative;
	}

	.time-block {
		position: absolute;
		top: 0;
		bottom: 0;
		border-right: 2px solid var(--theme-line);
		border-left: 2px solid var(--theme-line);
	}
	.time-block.green {
		background: #ccffcc;
	}
	.time-block.yellow {
		background: #ffeebb;
	}

	.comparison-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		width: 100%;
		margin-bottom: 2rem;
	}

	.comp-stat {
		font-size: 1.1rem;
		font-weight: bold;
		margin: 0.5rem 0;
	}

	.insight-box {
		width: 100%;
		padding: 1.5rem;
		background: var(--theme-bg);
		border: 3px dashed var(--theme-line);
		border-radius: 8px;
		font-size: 1.1rem;
	}
</style>
