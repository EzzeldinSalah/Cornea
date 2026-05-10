<script lang="ts">
	import { type Snippet } from 'svelte';

	interface Props {
		class?: string;
		children?: Snippet;
		variant?: 'default' | 'worst' | 'best';
	}
	let { class: className = '', children, variant = 'default' }: Props = $props();
</script>

<div
	class="neo-card {variant} {className}"
	style="display:flex; flex-direction:column; height: 100%; box-sizing: border-box;"
>
	{#if children}{@render children()}{/if}
</div>

<style>
	.neo-card {
		border: 3px solid var(--theme-line);
		background: var(--theme-paper);
		padding: 1.5rem;
		box-shadow: 7px 7px 0 var(--theme-shadow);
		position: relative;
		border-radius: 16px;
	}

	.neo-card.worst {
		background: #ffcccc;
		border-color: #cc0000;
		box-shadow: 7px 7px 0 #cc0000;
	}

	.neo-card.best {
		background: #d4edda;
		border-color: #155724;
		box-shadow: 7px 7px 0 #155724;
	}
</style>
