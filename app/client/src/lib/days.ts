import type { Day } from './types';

/**
 * The dataset numbers days from 1 (Monday) through 7 (Sunday), so the labels
 * are built from a known Monday rather than from the local week start.
 */
const A_MONDAY = new Date(Date.UTC(2024, 0, 1));

const formatter = new Intl.DateTimeFormat('en-US', {
	weekday: 'long',
	timeZone: 'UTC'
});

export const DAYS: Day[] = Array.from({ length: 7 }, (_, index) => {
	const date = new Date(A_MONDAY);
	date.setUTCDate(A_MONDAY.getUTCDate() + index);
	return { value: index + 1, name: formatter.format(date) };
});
