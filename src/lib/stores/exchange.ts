import { get, writable, type Readable } from 'svelte/store';

const exchangeRateStore = writable<number>(1);
const primaryCurrencyStore = writable<string>('USD');

export const exchangeRate: Readable<number> = {
	subscribe: exchangeRateStore.subscribe
};

export const primaryCurrency: Readable<string> = {
	subscribe: primaryCurrencyStore.subscribe
};

export const currency = primaryCurrency;

export async function loadExchangeRate(
	currencyCode: string,
	token?: string | null
): Promise<number> {
	const normalizedCurrency = (currencyCode || 'USD').toUpperCase();
	primaryCurrencyStore.set(normalizedCurrency);

	if (normalizedCurrency === 'USD') {
		exchangeRateStore.set(1);
		return 1;
	}

	const res = await fetch(`/api/exchange-rate?currency=${encodeURIComponent(normalizedCurrency)}`, {
		headers: token ? { Authorization: `Bearer ${token}` } : undefined
	});
	if (!res.ok) throw new Error('Failed to load exchange rate.');

	const data = await res.json();
	const rate = Number(data.rate);
	if (!Number.isFinite(rate) || rate <= 0) throw new Error('Invalid exchange rate.');

	primaryCurrencyStore.set(data.currency || normalizedCurrency);
	exchangeRateStore.set(rate);
	return rate;
}

export function toLocal(usd: number): number {
	return (Number(usd) || 0) * get(exchangeRateStore);
}
