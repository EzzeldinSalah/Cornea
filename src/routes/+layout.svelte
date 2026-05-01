<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { loadExchangeRate } from '$lib/stores/exchange';

	let { children } = $props();

	onMount(async () => {
		try {
			const token = localStorage.getItem('cornea_token');
			if (!token) return;

			const settingsRes = await fetch('/api/settings', {
				headers: { Authorization: `Bearer ${token}` }
			});
			const settings = await settingsRes.json();
			const currency = settings.primary_currency || 'USD';
			await loadExchangeRate(currency, token);
		} catch (e) {
			console.error('Failed to initialize exchange store', e);
		}
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
