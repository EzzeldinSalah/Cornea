<script lang="ts">
    import { onMount } from 'svelte';
    import NeoButton from '$lib/components/ui/NeoButton.svelte';
    import NeoCard from '$lib/components/ui/NeoCard.svelte';

    let diff = $state(null);
    let loading = $state(true);
    let error = $state(null);

    onMount(async () => {
        try {
            const res = await fetch('/api/diff');
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            diff = data;
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    });

    function formatDelta(val) {
        const prefix = val > 0 ? '+' : '';
        return prefix + val.toFixed(2);
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
        <NeoButton onclick={() => fetch('/api/sync/mock', {method:'POST'}).then(()=>location.reload())} class="mt-4">Run Mock Sync</NeoButton>
    </div>
{:else if diff}
    <NeoCard class="diff-card !p-0">
        <div class="diff-header">@@ -1,3 +1,3 @@</div>
        <div class="diff-body">
            <div class="diff-line {diff.income_delta_usd >= 0 ? 'add' : 'remove'}">
                <span class="sign">{diff.income_delta_usd >= 0 ? '+' : '-'}</span>
                <span class="text">USD Income Change: {formatDelta(diff.income_delta_usd)}</span>
            </div>
            <div class="diff-line {diff.income_delta_egp >= 0 ? 'add' : 'remove'}">
                <span class="sign">{diff.income_delta_egp >= 0 ? '+' : '-'}</span>
                <span class="text">EGP Real Change: {formatDelta(diff.income_delta_egp)}</span>
            </div>
            <div class="diff-line neutral">
                <span class="sign">~</span>
                <span class="text">EGP Rate Shift: {formatDelta(diff.egp_rate_change)}</span>
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
