<script lang="ts">
    import Sidebar from '$lib/components/Sidebar.svelte';
    let { children } = $props();
</script>

<div class="app-layout">
    <div class="grid-bg" aria-hidden="true"></div>
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
        position: relative;
    }
    .grid-bg {
        position: absolute;
        inset: 0;
        pointer-events: none;
        background:
            repeating-linear-gradient(
                90deg,
                transparent,
                transparent 35px,
                rgba(43, 30, 22, 0.08) 35px,
                rgba(43, 30, 22, 0.08) 36px
            ),
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 35px,
                rgba(43, 30, 22, 0.08) 35px,
                rgba(43, 30, 22, 0.08) 36px
            );
        opacity: 1;
        z-index: 0;
    }
    .main-content {
        flex: 1;
        padding: 3rem;
        box-sizing: border-box;
        max-height: 100vh;
        overflow-y: auto;
        position: relative;
        z-index: 1;
    }
</style>
