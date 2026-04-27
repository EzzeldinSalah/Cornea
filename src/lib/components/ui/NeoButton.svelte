<script lang="ts">
    import { type Snippet } from 'svelte';
    
    interface Props {
        href?: string;
        variant?: 'primary' | 'secondary';
        class?: string;
        onclick?: () => void;
        disabled?: boolean;
        children?: Snippet;
    }
    
    let { 
        href, 
        variant = 'primary', 
        class: className = '', 
        onclick, 
        disabled = false, 
        children 
    }: Props = $props();
</script>

{#if href}
    <a {href} {onclick} class="neo-btn {variant} {className}" aria-disabled={disabled}>
        {#if children}{@render children()}{/if}
    </a>
{:else}
    <button {onclick} {disabled} class="neo-btn {variant} {className}">
        {#if children}{@render children()}{/if}
    </button>
{/if}

<style>
    .neo-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 3px solid var(--theme-line);
        font-family: monospace;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 0.8rem 1.25rem;
        text-decoration: none;
        transition: all 0.15s ease-out;
        cursor: pointer;
        box-shadow: 4px 4px 0 var(--theme-shadow);
        font-size: 0.95rem;
        border-radius: 12px;
    }
    
    .neo-btn[disabled], .neo-btn[aria-disabled="true"] {
        opacity: 0.6;
        cursor: not-allowed;
        pointer-events: none;
    }

    .neo-btn:active:not([disabled]) {
        transform: translate(4px, 4px);
        box-shadow: 0px 0px 0 var(--theme-shadow);
    }

    .neo-btn:hover:not([disabled]) {
        transform: translate(-3px, -3px);
        box-shadow: 7px 7px 0 var(--theme-shadow);
    }

    .neo-btn.primary {
        background: var(--theme-accent);
        color: var(--theme-accent-ink);
    }
    
    .neo-btn.secondary {
        background: transparent;
        color: var(--theme-text);
    }
</style>
