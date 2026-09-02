export interface Airport {
	id: number;
	name: string;
}

export interface Prediction {
	day_of_week: number;
	airport_id: number;
	airport_name: string;
	/** Chance of an arrival delay over 15 minutes, between 0 and 1. */
	probability: number;
	/** The same figure as a percentage, rounded to one decimal place. */
	percent: number;
	/** Share of all flights in the training data that arrived late. */
	baseline: number;
}

export interface Day {
	value: number;
	name: string;
}
