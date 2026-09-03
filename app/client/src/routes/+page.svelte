<script lang="ts">
	import { enhance } from '$app/forms';
	import { DAYS, type Airport, type Prediction } from '$lib';
	import type { ActionData, PageData } from './$types';

	let { data, form }: { data: PageData; form: ActionData } = $props();

	const airports = $derived(data.airports as Airport[]);

	const prediction = $derived(
		form && 'prediction' in form ? (form.prediction as Prediction) : null
	);
	const error = $derived(form && 'error' in form ? (form.error as string) : data.apiError);

	const dayName = $derived(
		prediction ? DAYS.find((day) => day.value === prediction.day_of_week)?.name : null
	);

	/** Low, average or high compared with a typical flight in the dataset. */
	function riskLevel(probability: number, baseline: number): 'low' | 'typical' | 'high' {
		if (probability < baseline * 0.9) return 'low';
		if (probability > baseline * 1.1) return 'high';
		return 'typical';
	}

	const RISK_WORDS = {
		low: 'better than average',
		typical: 'about average',
		high: 'worse than average'
	} as const;

	// Day and airport only move the odds within a narrow band, so the meter tops
	// out well below 100% - a full-width scale would make every answer look the
	// same. Anything beyond the cap is clamped.
	const METER_MAX = 0.5;

	const meterWidth = (probability: number) =>
		`${Math.min(probability / METER_MAX, 1) * 100}%`;
</script>

<svelte:head>
	<title>Will my flight be late?</title>
</svelte:head>

<main>
	<header>
		<h1>Will my flight be late?</h1>
		<p class="lede">
			Pick where you are landing and which day you are flying to see the chance of arriving more
			than 15 minutes behind schedule, based on US domestic flights from 2013.
		</p>
	</header>

	{#if error}
		<p class="error" role="alert">{error}</p>
	{/if}

	{#if airports.length > 0}
		<form method="POST" action="?/getDelay" use:enhance>
			<!-- The selections are restored from the last answer so a full page
			     submit, without JavaScript, still comes back on the same flight. -->
			<label>
				<span>Arrival airport</span>
				<select name="airport_id" required>
					<option value="" disabled selected={!prediction}>Choose an airport</option>
					{#each airports as airport (airport.id)}
						<option value={airport.id} selected={prediction?.airport_id === airport.id}>
							{airport.name}
						</option>
					{/each}
				</select>
			</label>

			<label>
				<span>Day of the week</span>
				<select name="day_of_week" required>
					{#each DAYS as day (day.value)}
						<option
							value={day.value}
							selected={prediction ? prediction.day_of_week === day.value : day.value === 1}
						>
							{day.name}
						</option>
					{/each}
				</select>
			</label>

			<button type="submit">Check my flight</button>
		</form>
	{/if}

	{#if prediction}
		{@const level = riskLevel(prediction.probability, prediction.baseline)}
		<section class="result" aria-live="polite">
			<p class="headline">
				<strong>{prediction.percent}%</strong> chance of a delay
			</p>
			<p class="detail">
				Flights arriving at {prediction.airport_name} on a {dayName}
			</p>

			<div
				class="meter"
				role="img"
				aria-label="{prediction.percent} percent chance of a delay over 15 minutes"
			>
				<div class="fill {level}" style="width: {meterWidth(prediction.probability)}"></div>
				<div class="baseline" style="left: {meterWidth(prediction.baseline)}"></div>
			</div>
			<div class="scale">
				<span>0%</span>
				<span class="average" style="left: {meterWidth(prediction.baseline)}">average</span>
				<span>{METER_MAX * 100}%</span>
			</div>

			<p class="comparison">
				That is <strong>{RISK_WORDS[level]}</strong> &mdash; across the whole dataset
				{(prediction.baseline * 100).toFixed(1)}% of flights arrived late.
			</p>
		</section>
	{/if}

	<footer>
		<p>
			The estimate comes from a logistic regression trained on day of week and arrival airport
			alone. Those two facts only nudge the odds, so every answer lands fairly close to the
			overall average.
		</p>
	</footer>
</main>

<style>
	:global(body) {
		margin: 0;
		background: #f6f7f9;
		color: #1a1d21;
		font-family:
			system-ui,
			-apple-system,
			'Segoe UI',
			sans-serif;
		line-height: 1.5;
	}

	main {
		max-width: 34rem;
		margin: 0 auto;
		padding: 3rem 1.25rem 4rem;
	}

	h1 {
		margin: 0 0 0.5rem;
		font-size: 1.75rem;
	}

	.lede {
		margin: 0;
		color: #55606b;
	}

	form {
		display: grid;
		gap: 1rem;
		margin: 2rem 0;
		padding: 1.5rem;
		background: #fff;
		border: 1px solid #e2e5e9;
		border-radius: 0.75rem;
	}

	label {
		display: grid;
		gap: 0.375rem;
		font-weight: 600;
		font-size: 0.9rem;
	}

	select {
		padding: 0.6rem 0.7rem;
		font: inherit;
		font-weight: 400;
		background: #fff;
		border: 1px solid #c8ced5;
		border-radius: 0.4rem;
	}

	button {
		justify-self: start;
		padding: 0.6rem 1.25rem;
		font: inherit;
		font-weight: 600;
		color: #fff;
		background: #1f5eff;
		border: none;
		border-radius: 0.4rem;
		cursor: pointer;
	}

	button:hover {
		background: #1749cc;
	}

	.error {
		padding: 0.75rem 1rem;
		color: #8a1c1c;
		background: #fdeaea;
		border: 1px solid #f3c2c2;
		border-radius: 0.5rem;
	}

	.result {
		padding: 1.5rem;
		background: #fff;
		border: 1px solid #e2e5e9;
		border-radius: 0.75rem;
	}

	.headline {
		margin: 0;
		font-size: 1.1rem;
	}

	.headline strong {
		font-size: 2.25rem;
		line-height: 1.1;
	}

	.detail {
		margin: 0.25rem 0 1.25rem;
		color: #55606b;
	}

	.meter {
		position: relative;
		height: 0.75rem;
		background: #eceff2;
		border-radius: 999px;
		overflow: hidden;
	}

	.fill {
		height: 100%;
		border-radius: 999px;
	}

	.fill.low {
		background: #1f8a4c;
	}

	.fill.typical {
		background: #b8860b;
	}

	.fill.high {
		background: #c0392b;
	}

	/* Marks where an average flight sits, for comparison. */
	.baseline {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 2px;
		background: #1a1d21;
		opacity: 0.55;
	}

	.scale {
		position: relative;
		display: flex;
		justify-content: space-between;
		margin-top: 0.375rem;
		color: #6b7580;
		font-size: 0.75rem;
	}

	.scale .average {
		position: absolute;
		transform: translateX(-50%);
		white-space: nowrap;
	}

	.comparison {
		margin: 0.75rem 0 0;
		color: #55606b;
		font-size: 0.9rem;
	}

	footer {
		margin-top: 2.5rem;
		color: #6b7580;
		font-size: 0.85rem;
	}

	footer p {
		margin: 0;
	}
</style>
