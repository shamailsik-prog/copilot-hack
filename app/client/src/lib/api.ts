/**
 * Where the Flask prediction API lives.
 *
 * Override it by setting API_BASE_URL in the environment before `npm run dev`,
 * for example when the API runs on a different port or host.
 */
import { env } from '$env/dynamic/private';

export const API_BASE_URL = env.API_BASE_URL ?? 'http://127.0.0.1:5000';
