<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import NeoButton from '$lib/components/ui/NeoButton.svelte';

	let settings = $state({
		email: '',
		display_name: '',
		avatar_url: '',
		primary_language: 'English',
		primary_currency: 'USD',
		secondary_currency_display: true,
		coach_language: 'mixed',
		coach_tone: 'Balanced',
		notify_weekly_digest: true,
		notify_slow_month: true,
		notify_late_payment: true,
		notify_exchange_rate: false
	});

	let isLoading = $state(true);
	let isSaving = $state(false);
	let avatarPreview = $state('');
	let avatarFile: File | null = $state(null);
	let oldPassword = $state('');
	let newPassword = $state('');
	let showDeleteConfirm = $state(false);
	let showClearConfirm = $state(false);

	function getToken() {
		return localStorage.getItem('cornea_token');
	}

	onMount(async () => {
		const token = getToken();
		if (!token) {
			goto('/auth');
			return;
		}
		try {
			const res = await fetch('/api/settings', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				const data = await res.json();
				settings = { ...settings, ...data };
				if (settings.avatar_url) avatarPreview = settings.avatar_url;
			} else if (res.status === 401) {
				localStorage.removeItem('cornea_token');
				goto('/auth');
			}
		} catch (e) {
			console.error('Failed to load settings', e);
		} finally {
			isLoading = false;
		}
	});

	async function saveSettings() {
		isSaving = true;
		const token = getToken();
		try {
			// Upload avatar first if selected
			if (avatarFile) {
				const formData = new FormData();
				formData.append('file', avatarFile);
				const avatarRes = await fetch('/api/avatar', {
					method: 'POST',
					headers: { Authorization: `Bearer ${token}` },
					body: formData
				});
				if (avatarRes.ok) {
					const avatarData = await avatarRes.json();
					settings.avatar_url = avatarData.avatar_url;
				}
			}
			const res = await fetch('/api/settings', {
				method: 'PUT',
				headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
				body: JSON.stringify(settings)
			});
			if (res.ok) alert('Settings saved successfully!');
			else alert('Failed to save settings.');
		} catch (e) {
			alert('Error saving settings.');
		} finally {
			isSaving = false;
		}
	}

	function handleAvatarSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		if (input.files && input.files[0]) {
			avatarFile = input.files[0];
			avatarPreview = URL.createObjectURL(avatarFile);
		}
	}

	async function changePassword() {
		if (!oldPassword || !newPassword) {
			alert('Fill in both password fields.');
			return;
		}
		const token = getToken();
		try {
			const res = await fetch('/api/auth/password', {
				method: 'PUT',
				headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
				body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
			});
			const data = await res.json();
			if (res.ok) {
				alert('Password changed successfully!');
				oldPassword = '';
				newPassword = '';
			} else alert(data.detail || 'Failed to change password.');
		} catch (e) {
			alert('Error changing password.');
		}
	}

	async function deleteAccount() {
		const token = getToken();
		try {
			const res = await fetch('/api/account', {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				localStorage.removeItem('cornea_token');
				goto('/auth');
			} else alert('Failed to delete account.');
		} catch (e) {
			alert('Error deleting account.');
		}
	}

	async function clearSnapshots() {
		const token = getToken();
		try {
			const res = await fetch('/api/snapshots', {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				alert('All financial snapshots cleared.');
				showClearConfirm = false;
			} else alert('Failed to clear snapshots.');
		} catch (e) {
			alert('Error clearing snapshots.');
		}
	}

	async function exportData() {
		const token = getToken();
		try {
			const res = await fetch('/api/export', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				const data = await res.json();
				const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
				const url = URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = 'cornea-export.json';
				a.click();
				URL.revokeObjectURL(url);
			} else alert('Failed to export data.');
		} catch (e) {
			alert('Error exporting data.');
		}
	}
</script>

<svelte:head>
	<title>Settings | Cornea</title>
</svelte:head>

<div class="settings-page">
	<div class="header">
		<h1>Settings</h1>
		<p class="subtitle">Customize your Cornea experience.</p>
	</div>

	{#if isLoading}
		<p class="loading">Loading settings...</p>
	{:else}
		<div class="settings-grid">
			<!-- Profile Section -->
			<section class="settings-card">
				<h2>👤 Profile</h2>
				<div class="form-group">
					<label>Avatar</label>
					<div class="avatar-preview">
						<div class="avatar-circle">
							{#if avatarPreview}
								<img src={avatarPreview} alt="Avatar" class="avatar-img" />
							{:else}
								{settings.display_name ? settings.display_name.charAt(0).toUpperCase() : '?'}
							{/if}
						</div>
						<label class="upload-btn">
							<input type="file" accept="image/*" onchange={handleAvatarSelect} hidden />
							Upload Image
						</label>
					</div>
				</div>
				<div class="form-group">
					<label for="display-name">Display Name</label>
					<input
						type="text"
						id="display-name"
						bind:value={settings.display_name}
						placeholder="Your Name"
					/>
				</div>
				<div class="form-group">
					<label for="email">Account Email</label>
					<input
						type="email"
						id="email"
						value={settings.email}
						readonly
						disabled
						class="readonly-input"
					/>
					<small class="hint">Log in identifier.</small>
				</div>
				<div class="form-group">
					<label for="primary-lang">Primary Language</label>
					<select id="primary-lang" bind:value={settings.primary_language}>
						<option value="English">English</option>
						<option value="Arabic">Arabic</option>
						<option value="Both">Both (Arabic & English)</option>
					</select>
				</div>
			</section>

			<!-- Financial Settings -->
			<section class="settings-card">
				<h2>💰 Financial Settings</h2>
				<div class="form-group">
					<label for="primary-currency">Primary Currency</label>
					<select id="primary-currency" bind:value={settings.primary_currency}>
						<option value="USD">USD — United States Dollar</option>
						<option value="KWD">KWD — Kuwaiti Dinar</option>
						<option value="BHD">BHD — Bahraini Dinar</option>
						<option value="OMR">OMR — Omani Rial</option>
						<option value="JOD">JOD — Jordanian Dinar</option>
						<option value="TND">TND — Tunisian Dinar</option>
						<option value="QAR">QAR — Qatari Riyal</option>
						<option value="AED">AED — UAE Dirham</option>
						<option value="SAR">SAR — Saudi Riyal</option>
						<option value="LYD">LYD — Libyan Dinar</option>
						<option value="MAD">MAD — Moroccan Dirham</option>
						<option value="MRU">MRU — Mauritanian Ouguiya</option>
						<option value="EGP">EGP — Egyptian Pound</option>
						<option value="SYP">SYP — Syrian Pound</option>
						<option value="DZD">DZD — Algerian Dinar</option>
						<option value="DJF">DJF — Djiboutian Franc</option>
						<option value="YER">YER — Yemeni Rial</option>
						<option value="KMF">KMF — Comorian Franc</option>
						<option value="SOS">SOS — Somali Shilling</option>
						<option value="SDG">SDG — Sudanese Pound</option>
						<option value="IQD">IQD — Iraqi Dinar</option>
						<option value="LBP">LBP — Lebanese Pound</option>
					</select>
				</div>
				<div class="form-group checkbox-group">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={settings.secondary_currency_display} />
						<span class="custom-checkbox"></span>
						Secondary Currency Display (always show USD equivalent)
					</label>
				</div>
			</section>

			<!-- Coach Settings -->
			<section class="settings-card">
				<h2>🤖 Coach Settings</h2>
				<div class="form-group">
					<label for="coach-lang">Coach Language</label>
					<select id="coach-lang" bind:value={settings.coach_language}>
						<option value="mixed">Mixed (Default)</option>
						<option value="English">Strictly English</option>
						<option value="Arabic">Strictly Arabic</option>
					</select>
				</div>
				<div class="form-group">
					<label for="coach-tone">Coach Tone</label>
					<select id="coach-tone" bind:value={settings.coach_tone}>
						<option value="Balanced">Balanced</option>
						<option value="Blunt uncle">Blunt Uncle</option>
						<option value="Gentle">Gentle</option>
					</select>
				</div>
			</section>

			<!-- Notifications -->
			<section class="settings-card">
				<h2>🔔 Notifications <span class="badge dev">Under Dev</span></h2>
				<div class="form-group checkbox-group">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={settings.notify_weekly_digest} />
						<span class="custom-checkbox"></span>
						Weekly Financial Digest
					</label>
				</div>
				<div class="form-group checkbox-group">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={settings.notify_slow_month} />
						<span class="custom-checkbox"></span>
						"Slow month incoming" Forecast Alert
					</label>
				</div>
				<div class="form-group checkbox-group">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={settings.notify_late_payment} />
						<span class="custom-checkbox"></span>
						Late Payment Alert
					</label>
				</div>
				<div class="form-group checkbox-group">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={settings.notify_exchange_rate} />
						<span class="custom-checkbox"></span>
						Exchange Rate Alert (USD/EGP drastic moves)
					</label>
				</div>
			</section>

			<!-- Security -->
			<section class="settings-card">
				<h2>🔒 Security</h2>
				<div class="form-group">
					<label for="old-pw">Current Password</label>
					<input type="password" id="old-pw" bind:value={oldPassword} placeholder="••••••••" />
				</div>
				<div class="form-group">
					<label for="new-pw">New Password</label>
					<input type="password" id="new-pw" bind:value={newPassword} placeholder="••••••••" />
				</div>
				<NeoButton onclick={changePassword}>Change Password</NeoButton>
			</section>

			<!-- Danger Zone -->
			<section class="settings-card danger-card">
				<h2>🧪 Danger Zone</h2>

				<NeoButton variant="secondary" onclick={exportData}>Export All Data as JSON</NeoButton>

				{#if showClearConfirm}
					<div class="confirm-box">
						<p>Are you sure? This will <strong>erase all financial history</strong>.</p>
						<div class="confirm-actions">
							<NeoButton onclick={clearSnapshots}>Yes, Clear Everything</NeoButton>
							<NeoButton variant="secondary" onclick={() => (showClearConfirm = false)}
								>Cancel</NeoButton
							>
						</div>
					</div>
				{:else}
					<NeoButton variant="secondary" onclick={() => (showClearConfirm = true)}>
						Clear All Snapshots
					</NeoButton>
				{/if}

				{#if showDeleteConfirm}
					<div class="confirm-box">
						<p>
							⚠️ This is <strong>irreversible</strong>. Your account and all data will be
							permanently deleted.
						</p>
						<div class="confirm-actions">
							<NeoButton onclick={deleteAccount}>Delete Account Permanently</NeoButton>
							<NeoButton variant="secondary" onclick={() => (showDeleteConfirm = false)}
								>Cancel</NeoButton
							>
						</div>
					</div>
				{:else}
					<NeoButton variant="secondary" onclick={() => (showDeleteConfirm = true)}>
						Delete Account Permanently
					</NeoButton>
				{/if}
			</section>
		</div>

		<div class="actions">
			<NeoButton onclick={saveSettings} disabled={isSaving}>
				{isSaving ? 'Saving...' : 'Save Settings'}
			</NeoButton>
		</div>
	{/if}
</div>

<style>
	.settings-page {
		max-width: 900px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}

	.header {
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 2.5rem;
		margin: 0;
		text-transform: uppercase;
		letter-spacing: -0.02em;
	}

	.subtitle {
		color: var(--theme-muted);
		font-size: 1.1rem;
		margin-top: 0.5rem;
	}

	.loading {
		font-family: monospace;
		color: var(--theme-muted);
		font-size: 1.2rem;
	}

	.settings-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 2rem;
	}

	@media (min-width: 768px) {
		.settings-grid {
			grid-template-columns: 1fr 1fr;
		}
	}

	.settings-card {
		background: var(--theme-paper);
		border: 4px solid var(--theme-line);
		border-radius: 1rem;
		padding: 1.5rem;
		box-shadow: 6px 6px 0 var(--theme-shadow);
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.danger-card {
		border-color: #b91c1c;
		box-shadow: 6px 6px 0 #7f1d1d;
	}

	h2 {
		font-size: 1.25rem;
		margin: 0;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding-bottom: 1rem;
		border-bottom: 3px solid var(--theme-line);
	}

	.danger-card h2 {
		border-bottom-color: #b91c1c;
	}

	.badge {
		font-size: 0.7rem;
		padding: 0.2rem 0.5rem;
		border-radius: 999px;
		font-weight: 800;
		text-transform: uppercase;
		border: 2px solid var(--theme-line);
	}

	.badge.dev {
		background: var(--theme-accent);
		color: var(--theme-accent-ink);
		box-shadow: 2px 2px 0 var(--theme-shadow);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	label {
		font-weight: 700;
		font-size: 0.9rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	input[type='text'],
	input[type='password'],
	input[type='email'],
	select {
		padding: 0.75rem;
		border: 3px solid var(--theme-line);
		border-radius: 0.5rem;
		background: var(--theme-bg);
		color: var(--theme-text);
		font-family: inherit;
		font-size: 1rem;
		outline: none;
		transition:
			box-shadow 0.2s,
			transform 0.1s;
	}

	input[type='text']:focus,
	input[type='password']:focus,
	input[type='email']:focus,
	select:focus {
		box-shadow: 4px 4px 0 var(--theme-accent);
		transform: translate(-2px, -2px);
	}

	.readonly-input {
		background: var(--theme-line) !important;
		color: var(--theme-bg) !important;
		cursor: not-allowed;
		border-color: var(--theme-line) !important;
		opacity: 0.7;
	}

	.avatar-preview {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.avatar-circle {
		width: 4rem;
		height: 4rem;
		border-radius: 50%;
		background: var(--theme-accent);
		color: var(--theme-accent-ink);
		border: 3px solid var(--theme-line);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: 800;
		box-shadow: 4px 4px 0 var(--theme-shadow);
		flex-shrink: 0;
		overflow: hidden;
	}

	.avatar-img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.upload-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.6rem 1rem;
		border: 3px solid var(--theme-line);
		border-radius: 0.5rem;
		background: var(--theme-bg);
		font-weight: 700;
		font-size: 0.85rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		cursor: pointer;
		transition:
			box-shadow 0.2s,
			transform 0.15s;
		box-shadow: 3px 3px 0 var(--theme-shadow);
	}

	.upload-btn:hover {
		transform: translate(-2px, -2px);
		box-shadow: 5px 5px 0 var(--theme-shadow);
	}

	.checkbox-group {
		flex-direction: row;
		align-items: center;
	}

	.toggle-label {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		cursor: pointer;
		font-size: 0.95rem;
		text-transform: none;
		font-weight: 600;
		letter-spacing: 0;
		line-height: 1.4;
	}

	.toggle-label input[type='checkbox'] {
		display: none;
	}

	.custom-checkbox {
		width: 1.5rem;
		height: 1.5rem;
		border: 3px solid var(--theme-line);
		border-radius: 0.35rem;
		display: inline-block;
		position: relative;
		flex-shrink: 0;
		background: var(--theme-bg);
		transition:
			background 0.1s,
			box-shadow 0.1s;
		margin-top: 0.1rem;
	}

	.toggle-label input[type='checkbox']:checked + .custom-checkbox {
		background: var(--theme-accent);
		box-shadow: 2px 2px 0 var(--theme-shadow);
	}

	.toggle-label input[type='checkbox']:checked + .custom-checkbox::after {
		content: '';
		position: absolute;
		left: 0.3rem;
		top: 0.1rem;
		width: 0.4rem;
		height: 0.8rem;
		border: solid var(--theme-accent-ink);
		border-width: 0 3px 3px 0;
		transform: rotate(45deg);
	}

	.confirm-box {
		background: #fef2f2;
		border: 3px solid #b91c1c;
		border-radius: 0.75rem;
		padding: 1rem;
		color: #7f1d1d;
	}

	.confirm-box p {
		margin: 0 0 0.75rem 0;
		font-size: 0.95rem;
	}

	.confirm-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.actions {
		margin-top: 3rem;
		display: flex;
		justify-content: flex-end;
	}
</style>
