import { fail } from '@sveltejs/kit';
import { API_BASE_URL } from '$lib/api';
import type { Airport, Prediction } from '$lib';
import type { Actions, PageServerLoad } from './$types';

/** Load the airport list so the dropdown has something to show. */
export const load: PageServerLoad = async ({ fetch }) => {
	try {
		const response = await fetch(`${API_BASE_URL}/airports`);
		if (!response.ok) {
			return { airports: [] as Airport[], apiError: `The API returned ${response.status}.` };
		}
		const airports: Airport[] = await response.json();
		return { airports, apiError: null };
	} catch {
		return {
			airports: [] as Airport[],
			apiError: `Could not reach the prediction API at ${API_BASE_URL}. Is it running?`
		};
	}
};

export const actions: Actions = {
	getDelay: async ({ fetch, request }) => {
		const data = await request.formData();
		const dayOfWeek = data.get('day_of_week');
		const airportId = data.get('airport_id');

		if (!dayOfWeek || !airportId) {
			return fail(400, { error: 'Pick both an arrival airport and a day.' });
		}

		const query = new URLSearchParams({
			day_of_week: String(dayOfWeek),
			airport_id: String(airportId)
		});

		try {
			const response = await fetch(`${API_BASE_URL}/predict?${query}`);
			const body = await response.json();

			if (!response.ok) {
				return fail(response.status, { error: body.error ?? 'The prediction failed.' });
			}

			return { prediction: body as Prediction };
		} catch {
			return fail(503, {
				error: `Could not reach the prediction API at ${API_BASE_URL}. Is it running?`
			});
		}
	}
};
