<script lang="ts">
    import Sidebar from '$lib/components/Sidebar.svelte';
    let { children } = $props();
</script>

<div class="app-layout">
    <Sidebar />
    <main class="main-content">
        {@render children()}
    </main>
</div>

<style>
    :global(body) {
        background: var(--theme-bg);
    }
    .app-layout {
        display: flex;
        min-height: 100vh;
        background: var(--theme-bg);
        color: var(--theme-text);
    }
    .main-content {
        flex: 1;
        padding: 3rem;
        box-sizing: border-box;
        max-height: 100vh;
        overflow-y: auto;
    }
</style>
