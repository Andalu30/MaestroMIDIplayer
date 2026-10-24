export function formatDuration(seconds: number): string {
	const total = Math.floor(seconds);
	const h = Math.floor(total / 3600);
	const m = Math.floor((total % 3600) / 60);
	const s = total % 60;
	if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
	return `${m}:${s.toString().padStart(2, '0')}`;
}

export function formatTotalDuration(seconds: number): string {
	const total = Math.floor(seconds);
	const h = Math.floor(total / 3600);
	const m = Math.floor((total % 3600) / 60);
	if (h > 0) return `${h}h ${m}m`;
	return `${m}m`;
}

// Word-level synonyms seen across MAESTRO title spellings of the same piece
const PIECE_SYNONYMS: Record<string, string> = {
	et: 'and', und: 'and',
	grand: 'grande', brilliant: 'brillante', brillant: 'brillante', brilliante: 'brillante',
	opus: 'op', movement: 'mov', mvt: 'mov',
	no: '', nr: ''
};

/**
 * Grouping key for "same piece, different spelling" in the dataset, e.g.
 * "Variations Serieuses Op. 54" / "Variations sérieuses, Op. 54" or
 * "Toccata in C Major, Op. 7" / "Toccata in C major, opus 7".
 * Ignores case, accents, punctuation and a few synonyms; never touches numbers.
 */
export function pieceKey(title: string): string {
	return title
		.normalize('NFKD')
		.replace(/\p{M}/gu, '')
		.toLowerCase()
		.split(/[^\p{L}\p{N}]+/u)
		.map((w) => PIECE_SYNONYMS[w] ?? w)
		.filter(Boolean)
		.join(' ');
}
