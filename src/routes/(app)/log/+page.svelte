<script lang="ts">
    import { onMount } from 'svelte';
    import NeoButton from '$lib/components/ui/NeoButton.svelte';

    let snapshots = $state([]);
    let loading = $state(true);

    onMount(async () => {
        try {
            const res = await fetch('/api/log');
            const data = await res.json();
            snapshots = data.snapshots || [];
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    });
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
{:else if snapshots.length === 0}
    <div class="empty-state">
        <p>No commits found. Try running a sync first.<br>
        <NeoButton onclick={() => fetch('/api/sync/mock', {method:'POST'}).then(()=>location.reload())} class="mt-4">Run Mock Sync</NeoButton></p>
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
                        <span class="value">${s.total_invoiced_usd.toFixed(2)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="label">Received (EGP):</span>
                        <span class="value egp">{s.total_received_egp.toFixed(2)} EGP</span>
                    </div>
                    <div class="stat-row">
                        <span class="label">Exchange Rate:</span>
                        <span class="value">{s.egp_rate_at_date.toFixed(2)}</span>
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
    .stat-row .egp {
        color: var(--theme-accent);
        font-weight: 900;
    }
</style>
