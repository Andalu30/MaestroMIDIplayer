import type { Track, Composer, CompetitionSummary, CompetitionYear } from './stores';

const BASE = '/api';

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${BASE}${path}`);
	if (!res.ok) throw new Error(`API error: ${res.status}`);
	return res.json();
}

export interface PaginatedTracks {
	total: number;
	skip: number;
	limit: number;
	items: Track[];
}

export async function getComposers(): Promise<Composer[]> {
	return fetchJson('/composers');
}

export async function getComposerTracks(slug: string): Promise<Track[]> {
	return fetchJson(`/composers/${slug}/tracks`);
}

export async function getComposer(slug: string): Promise<Composer> {
	return fetchJson(`/composers/${slug}`);
}

export async function getTracks(params?: {
	q?: string;
	composer?: string;
	year?: number;
	sort?: string;
	order?: string;
	skip?: number;
	limit?: number;
}): Promise<PaginatedTracks> {
	const searchParams = new URLSearchParams();
	if (params?.q) searchParams.set('q', params.q);
	if (params?.composer) searchParams.set('composer', params.composer);
	if (params?.year) searchParams.set('year', String(params.year));
	if (params?.sort) searchParams.set('sort', params.sort);
	if (params?.order) searchParams.set('order', params.order);
	if (params?.skip != null) searchParams.set('skip', String(params.skip));
	if (params?.limit != null) searchParams.set('limit', String(params.limit));
	const qs = searchParams.toString();
	return fetchJson(`/tracks${qs ? '?' + qs : ''}`);
}

export async function getTrack(id: number): Promise<Track> {
	return fetchJson(`/tracks/${id}`);
}

export async function getCompetitions(): Promise<CompetitionSummary[]> {
	return fetchJson('/competitions');
}

export async function getCompetition(year: number): Promise<CompetitionYear> {
	return fetchJson(`/competitions/${year}`);
}

export function composerImageUrl(slug: string): string {
	return `${BASE}/composers/${slug}/image`;
}

export function midiFileUrl(trackId: number): string {
	return `${BASE}/midi/tracks/${trackId}/file`;
}
