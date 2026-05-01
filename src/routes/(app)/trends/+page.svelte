<script lang="ts">
	import { onMount } from 'svelte';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';

	// --- Form state ---
	let roles = $state([]);
	let countries = $state([]);
	let expBrackets = $state([]);

	let selectedRole = $state('');
	let selectedExp = $state('');
	let selectedCountry = $state('egypt');
	let currentRate = $state('');

	// --- Report state ---
	let report = $state(null);
	let loading = $state(false);
	let metaLoading = $state(true);
	let error = $state('');

	// --- Load dropdown options from /api/pulse/meta on mount ---
	onMount(async () => {
		try {
			const res = await fetch('/api/pulse/meta');
			const data = await res.json();
			roles = data.roles || [];
			countries = data.countries || [];
			expBrackets = data.experience_brackets || [];

			// Pre-select first role and first bracket so form is never blank
			if (roles.length) selectedRole = roles[0].key;
			if (expBrackets.length) selectedExp = expBrackets[0];
		} catch (e) {
			error = 'Failed to load options. Is the backend running?';
		} finally {
			metaLoading = false;
		}
	});

	async function runPulse() {
		if (!selectedRole || !selectedExp || !selectedCountry) return;
		loading = true;
		error = '';
		report = null;

		try {
			const token = localStorage.getItem('token');
			const headers: Record<string, string> = { 'Content-Type': 'application/json' };
			if (token) headers['Authorization'] = `Bearer ${token}`;

			const body: Record<string, unknown> = {
				job_title: selectedRole,
				years_experience: selectedExp,
				country: selectedCountry
			};
			if (currentRate) body.current_rate = parseFloat(currentRate);

			const res = await fetch('/api/pulse', {
				method: 'POST',
				headers,
				body: JSON.stringify(body)
			});

			if (!res.ok) {
				const err = await res.json();
				throw new Error(err.detail || 'Request failed');
			}

			report = await res.json();
		} catch (e: any) {
			error = e.message || 'Something went wrong.';
		} finally {
			loading = false;
		}
	}

	// Position indicator colours
	function positionColour(status: string | null) {
		if (status === 'Underpriced') return 'var(--theme-danger, #e53e3e)';
		if (status === 'Premium') return 'var(--theme-success, #38a169)';
		return 'var(--theme-accent)';
	}

	// Timing signal colours
	function timingColour(signal: string) {
		if (signal === 'Act Now') return 'var(--theme-success, #38a169)';
		if (signal === 'Caution') return 'var(--theme-danger, #e53e3e)';
		return 'var(--theme-muted)';
	}

	function fmt(n: number | null, decimals = 0) {
		if (n === null || n === undefined) return '—';
		return n.toLocaleString(undefined, { maximumFractionDigits: decimals });
	}
</script>

<svelte:head>
	<title>Pulse | Cornea</title>
</svelte:head>

<!-- ── Page Header ── -->
<div class="page-header">
	<h1>pulse</h1>
	<p class="subtitle">Where do you stand in the market — right now?</p>
</div>

<!-- ── Input Form ── -->
<div class="form-card">
	{#if metaLoading}
		<p class="loading">Loading options...</p>
	{:else}
		<div class="form-grid">
			<div class="field">
				<label for="role">Job Title</label>
				<select id="role" bind:value={selectedRole}>
					{#each roles as r}
						<option value={r.key}>{r.label}</option>
					{/each}
				</select>
			</div>

			<div class="field">
				<label for="exp">Years of Experience</label>
				<select id="exp" bind:value={selectedExp}>
					{#each expBrackets as b}
						<option value={b}>{b} years</option>
					{/each}
				</select>
			</div>

			<div class="field">
				<label for="country">Country</label>
				<select id="country" bind:value={selectedCountry}>
					{#each countries as c}
						<option value={c.key}>{c.label}</option>
					{/each}
				</select>
			</div>

			<div class="field">
				<label for="rate">Current Rate (USD/hr) <span class="optional">optional</span></label>
				<input id="rate" type="number" min="1" placeholder="e.g. 18" bind:value={currentRate} />
			</div>
		</div>

		<div class="form-action">
			<NeoButton onclick={runPulse} disabled={loading}>
				{loading ? 'Reading the market...' : 'Run Pulse'}
			</NeoButton>
		</div>

		{#if error}
			<p class="error">{error}</p>
		{/if}
	{/if}
</div>

<!-- ── Loading skeleton ── -->
{#if loading}
	<div class="skeleton-grid">
		{#each [1, 2, 3, 4] as _}
			<div class="skeleton-card"></div>
		{/each}
	</div>
{/if}

<!-- ── Report ── -->
{#if report && !loading}
	<div class="report">
		<!-- 1. Position Indicator -->
		{#if report.position_indicator.status}
			<div class="report-card position-card">
				<span class="card-label">Your Position</span>
				<div
					class="position-badge"
					style="border-color: {positionColour(
						report.position_indicator.status
					)}; color: {positionColour(report.position_indicator.status)};"
				>
					{report.position_indicator.status}
				</div>
				<p class="position-detail">
					You are charging
					<strong>${report.position_indicator.current_rate}/hr</strong>
					— the market median for a
					<strong>{report.inputs.job_title_label}</strong>
					at your level is
					<strong>${report.position_indicator.median}/hr</strong>
					({report.position_indicator.gap_pct > 0 ? '+' : ''}{report.position_indicator.gap_pct}%).
				</p>
			</div>
		{/if}

		<!-- 2. Rate Ranges -->
		<div class="report-card">
			<span class="card-label">Suggested Rate Range</span>
			<div class="rate-row">
				<div class="rate-tier">
					<span class="tier-name">Floor</span>
					<span class="tier-usd">${report.rate_ranges.floor.usd}/hr</span>
					{#if report.rate_ranges.floor.local !== null}
						<span class="tier-local">
							{fmt(report.rate_ranges.floor.local)}
							{report.inputs.currency}/hr
						</span>
					{/if}
				</div>
				<div class="rate-tier accent">
					<span class="tier-name">Median</span>
					<span class="tier-usd">${report.rate_ranges.median.usd}/hr</span>
					{#if report.rate_ranges.median.local !== null}
						<span class="tier-local">
							{fmt(report.rate_ranges.median.local)}
							{report.inputs.currency}/hr
						</span>
					{/if}
				</div>
				<div class="rate-tier">
					<span class="tier-name">Target</span>
					<span class="tier-usd">${report.rate_ranges.target.usd}/hr</span>
					{#if report.rate_ranges.target.local !== null}
						<span class="tier-local">
							{fmt(report.rate_ranges.target.local)}
							{report.inputs.currency}/hr
						</span>
					{/if}
				</div>
			</div>
		</div>

		<!-- 3. Market Demand + Competitor Density (side by side on wide screens) -->
		<div class="two-col">
			<div class="report-card">
				<span class="card-label">Market Demand</span>
				<span class="signal-badge demand-{report.market_demand.level.toLowerCase()}">
					{report.market_demand.level}
				</span>
				<p class="ai-text">{report.market_demand.explanation}</p>
			</div>

			<div class="report-card">
				<span class="card-label">Competing Freelancer Density</span>
				<span class="signal-badge saturation-{report.competitor_density.saturation.toLowerCase()}">
					{report.competitor_density.saturation} Saturation
				</span>
				<p class="ai-text">{report.competitor_density.specialization_pivots}</p>
			</div>
		</div>

		<!-- 4. Purchasing Power -->
		<div class="report-card">
			<span class="card-label">
				Purchasing Power in {report.inputs.country_label}
				{#if report.purchasing_power.live_rate}
					<span class="rate-note">
						Reference rate: 1 USD = {fmt(report.purchasing_power.live_rate, 2)}
						{report.purchasing_power.currency}
					</span>
				{/if}
			</span>

			<div class="pp-table-wrapper">
				<table class="pp-table">
					<thead>
						<tr>
							<th>Workload</th>
							<th>At Floor (${report.rate_ranges.floor.usd}/hr)</th>
							<th>At Median (${report.rate_ranges.median.usd}/hr)</th>
							<th>At Target (${report.rate_ranges.target.usd}/hr)</th>
						</tr>
					</thead>
					<tbody>
						{#each Object.values(report.purchasing_power.scenarios) as row}
							<tr>
								<td class="workload-label">{row.label}</td>
								<td>
									${fmt(row.floor_usd)}
									{#if row.floor_local !== null}
										<br /><span class="local"
											>{fmt(row.floor_local)} {report.purchasing_power.currency}</span
										>
									{/if}
								</td>
								<td class="accent-col">
									${fmt(row.median_usd)}
									{#if row.median_local !== null}
										<br /><span class="local accent-local"
											>{fmt(row.median_local)} {report.purchasing_power.currency}</span
										>
									{/if}
								</td>
								<td>
									${fmt(row.target_usd)}
									{#if row.target_local !== null}
										<br /><span class="local"
											>{fmt(row.target_local)} {report.purchasing_power.currency}</span
										>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<p class="col-note">
				Reference: a {report.purchasing_power.col_reference.label} costs approximately ${fmt(
					report.purchasing_power.col_reference.amount_usd
				)}/month
				{#if report.purchasing_power.col_reference.amount_local !== null}
					({fmt(report.purchasing_power.col_reference.amount_local)}
					{report.purchasing_power.currency})
				{/if}.
			</p>
		</div>

		<!-- 5. Market Timing -->
		<div class="report-card timing-card">
			<span class="card-label">Market Timing</span>
			<span
				class="timing-badge"
				style="border-color: {timingColour(report.market_timing.signal)}; color: {timingColour(
					report.market_timing.signal
				)};"
			>
				{report.market_timing.signal}
			</span>
			<p class="ai-text">{report.market_timing.explanation}</p>
		</div>

		<!-- 6. Working Windows (static, always shown) -->
		<div class="report-card">
			<span class="card-label">Best Hours to Be Online</span>
			<p class="windows-note">
				These windows apply regardless of your skill — they reflect when your highest-paying clients
				are actively hiring.
			</p>
			<div class="windows-grid">
				{#each report.working_windows as w}
					<div class="window-item">
						<span class="window-market">{w.market}</span>
						<span class="window-local">{w.egypt_local}</span>
						<span class="window-sub">{w.note}</span>
					</div>
				{/each}
			</div>
		</div>

		<!-- 7. What It Takes -->
		<div class="report-card">
			<span class="card-label">What It Takes to Get There</span>
			<p class="ai-text">{report.what_it_takes}</p>
		</div>

		<!-- 8. Client Perspective -->
		<div class="report-card">
			<span class="card-label">How Clients Read Your Rate</span>
			<p class="ai-text">{report.client_perspective}</p>
		</div>

		<!-- 9. Positioning Brief -->
		<div class="report-card brief-card">
			<span class="card-label">Positioning Brief</span>
			<p class="brief-text">{report.positioning_brief}</p>
		</div>

		<!-- 10. Action Layer -->
		<div class="report-card action-card">
			<span class="card-label">What To Do Next</span>
			<p class="ai-text action-text">{report.action_layer}</p>
		</div>
	</div>
{/if}

<style>
	/* ── Page Header ── */
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

	/* ── Form Card ── */
	.form-card {
		border: 3px solid var(--theme-line);
		background: var(--theme-paper);
		border-radius: 1rem;
		padding: 2rem;
		box-shadow: 6px 6px 0 var(--theme-shadow);
		margin-bottom: 2rem;
	}
	.form-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.25rem;
		margin-bottom: 1.5rem;
	}
	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
	}
	.field {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	label {
		font-weight: bold;
		font-size: 0.95rem;
	}
	.optional {
		font-weight: normal;
		color: var(--theme-muted);
		font-size: 0.85rem;
		margin-left: 0.25rem;
	}
	select,
	input[type='number'] {
		border: 2px solid var(--theme-line);
		background: var(--theme-bg);
		color: var(--theme-text);
		border-radius: 0.5rem;
		padding: 0.6rem 0.8rem;
		font-size: 1rem;
		font-family: inherit;
		width: 100%;
	}
	select:focus,
	input[type='number']:focus {
		outline: none;
		border-color: var(--theme-accent);
	}
	.form-action {
		display: flex;
		justify-content: flex-end;
	}
	.error {
		color: var(--theme-danger, #e53e3e);
		font-weight: bold;
		margin-top: 1rem;
	}
	.loading {
		color: var(--theme-muted);
	}

	/* ── Skeleton ── */
	.skeleton-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.25rem;
		margin-bottom: 2rem;
	}
	@media (max-width: 640px) {
		.skeleton-grid {
			grid-template-columns: 1fr;
		}
	}
	.skeleton-card {
		border: 3px solid var(--theme-line);
		border-radius: 1rem;
		height: 120px;
		background: var(--theme-paper);
		opacity: 0.5;
		animation: pulse-skeleton 1.4s ease-in-out infinite;
	}
	@keyframes pulse-skeleton {
		0%,
		100% {
			opacity: 0.5;
		}
		50% {
			opacity: 0.2;
		}
	}

	/* ── Report ── */
	.report {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	/* Base card — matches commit-card from reference */
	.report-card {
		border: 3px solid var(--theme-line);
		background: var(--theme-paper);
		border-radius: 1rem;
		padding: 1.75rem;
		box-shadow: 6px 6px 0 var(--theme-shadow);
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.card-label {
		font-family: monospace;
		color: var(--theme-accent);
		font-weight: bold;
		font-size: 0.85rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	/* ── Position Card ── */
	.position-badge {
		display: inline-block;
		border: 3px solid;
		border-radius: 2rem;
		padding: 0.35rem 1.25rem;
		font-size: 1.4rem;
		font-weight: 900;
		width: fit-content;
	}
	.position-detail {
		margin: 0;
		font-size: 1.05rem;
		line-height: 1.6;
	}

	/* ── Rate Ranges ── */
	.rate-row {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: 1rem;
	}
	@media (max-width: 480px) {
		.rate-row {
			grid-template-columns: 1fr;
		}
	}
	.rate-tier {
		border: 2px dashed var(--theme-line);
		border-radius: 0.75rem;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		text-align: center;
	}
	.rate-tier.accent {
		border-style: solid;
		border-color: var(--theme-accent);
		box-shadow: 4px 4px 0 var(--theme-shadow);
	}
	.tier-name {
		font-size: 0.8rem;
		font-weight: bold;
		text-transform: uppercase;
		color: var(--theme-muted);
		letter-spacing: 0.05em;
	}
	.tier-usd {
		font-size: 1.6rem;
		font-weight: 900;
	}
	.rate-tier.accent .tier-usd {
		color: var(--theme-accent);
	}
	.tier-local {
		font-size: 0.9rem;
		color: var(--theme-muted);
	}

	/* ── Two-col layout ── */
	.two-col {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.25rem;
	}
	@media (max-width: 640px) {
		.two-col {
			grid-template-columns: 1fr;
		}
	}

	/* ── Signal Badges ── */
	.signal-badge {
		display: inline-block;
		border: 2px solid var(--theme-line);
		border-radius: 2rem;
		padding: 0.2rem 0.9rem;
		font-size: 0.85rem;
		font-weight: bold;
		width: fit-content;
	}
	.demand-high {
		border-color: var(--theme-success, #38a169);
		color: var(--theme-success, #38a169);
	}
	.demand-medium {
		border-color: var(--theme-accent);
		color: var(--theme-accent);
	}
	.demand-low {
		border-color: var(--theme-muted);
		color: var(--theme-muted);
	}
	.demand-saturated {
		border-color: var(--theme-danger, #e53e3e);
		color: var(--theme-danger, #e53e3e);
	}
	.saturation-high {
		border-color: var(--theme-danger, #e53e3e);
		color: var(--theme-danger, #e53e3e);
	}
	.saturation-medium {
		border-color: var(--theme-accent);
		color: var(--theme-accent);
	}
	.saturation-low {
		border-color: var(--theme-success, #38a169);
		color: var(--theme-success, #38a169);
	}

	/* ── AI text ── */
	.ai-text {
		margin: 0;
		font-size: 1rem;
		line-height: 1.7;
		white-space: pre-line;
	}

	/* ── Purchasing Power Table ── */
	.rate-note {
		font-weight: normal;
		font-size: 0.8rem;
		color: var(--theme-muted);
		font-family: monospace;
	}
	.pp-table-wrapper {
		overflow-x: auto;
	}
	.pp-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.95rem;
	}
	.pp-table th {
		text-align: left;
		padding: 0.5rem 0.75rem;
		border-bottom: 2px solid var(--theme-line);
		font-weight: bold;
		white-space: nowrap;
	}
	.pp-table td {
		padding: 0.6rem 0.75rem;
		border-bottom: 1px dashed var(--theme-line);
		vertical-align: top;
	}
	.workload-label {
		font-weight: bold;
		color: var(--theme-muted);
		font-size: 0.85rem;
	}
	.accent-col {
		background: color-mix(in srgb, var(--theme-accent) 8%, transparent);
	}
	.local {
		font-size: 0.8rem;
		color: var(--theme-muted);
	}
	.accent-local {
		color: var(--theme-accent);
		font-weight: bold;
	}
	.col-note {
		margin: 0;
		font-size: 0.85rem;
		color: var(--theme-muted);
		border-top: 1px dashed var(--theme-line);
		padding-top: 0.75rem;
	}

	/* ── Timing Card ── */
	.timing-badge {
		display: inline-block;
		border: 3px solid;
		border-radius: 2rem;
		padding: 0.3rem 1rem;
		font-size: 1.1rem;
		font-weight: 900;
		width: fit-content;
	}

	/* ── Working Windows ── */
	.windows-note {
		margin: 0;
		font-size: 0.9rem;
		color: var(--theme-muted);
	}
	.windows-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
	}
	@media (max-width: 640px) {
		.windows-grid {
			grid-template-columns: 1fr;
		}
	}
	.window-item {
		border: 2px dashed var(--theme-line);
		border-radius: 0.75rem;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	.window-market {
		font-weight: bold;
		font-size: 0.9rem;
	}
	.window-local {
		font-family: monospace;
		color: var(--theme-accent);
		font-weight: bold;
		font-size: 1.1rem;
	}
	.window-sub {
		font-size: 0.8rem;
		color: var(--theme-muted);
		line-height: 1.4;
	}

	/* ── Brief Card ── */
	.brief-card {
		border-color: var(--theme-accent);
		box-shadow: 8px 8px 0 var(--theme-shadow);
	}
	.brief-text {
		margin: 0;
		font-size: 1.1rem;
		line-height: 1.8;
		font-style: italic;
	}

	/* ── Action Card ── */
	.action-card {
		background: color-mix(in srgb, var(--theme-accent) 6%, var(--theme-paper));
	}
	.action-text {
		white-space: pre-line;
		font-size: 1rem;
		line-height: 1.9;
	}
</style>
