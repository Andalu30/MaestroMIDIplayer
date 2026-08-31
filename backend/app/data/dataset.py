"""Load the MAESTRO CSV into memory and provide search/filter/sort."""

import csv
import logging
from collections import defaultdict
from pathlib import Path

from .filename_parser import parse_filename
from .models import (
    CompetitionRound,
    CompetitionSession,
    CompetitionYear,
    Composer,
    PaginatedTracks,
    Track,
    _make_slug,
)

logger = logging.getLogger("maestro")


class DatasetStore:
    def __init__(self) -> None:
        self.tracks: list[Track] = []
        self.by_composer: dict[str, list[Track]] = defaultdict(list)
        self.by_year: dict[int, list[Track]] = defaultdict(list)
        self.composers: list[Composer] = []
        self._composer_map: dict[str, Composer] = {}

    def load(self, csv_path: Path) -> None:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                year = int(row["year"])
                parsed = parse_filename(row["midi_filename"], year)
                track = Track(
                    id=i,
                    composer=row["canonical_composer"],
                    title=row["canonical_title"],
                    split=row["split"],
                    year=year,
                    midi_filename=row["midi_filename"],
                    audio_filename=row["audio_filename"],
                    duration=float(row["duration"]),
                    round=parsed.round,
                    session=parsed.session,
                    piece_index=parsed.piece_index,
                )
                self.tracks.append(track)
                self.by_composer[track.composer].append(track)
                self.by_year[year].append(track)

        # Build composer list
        composer_data: dict[str, dict] = {}
        for composer_name, tracks in self.by_composer.items():
            slug = _make_slug(composer_name)
            composer_data[slug] = {
                "name": composer_name,
                "slug": slug,
                "track_count": len(tracks),
                "total_duration": sum(t.duration for t in tracks),
            }

        self.composers = sorted(
            [Composer(**data) for data in composer_data.values()],
            key=lambda c: c.track_count,
            reverse=True,
        )
        self._composer_map = {c.slug: c for c in self.composers}

        # Warn if any two composer names mapped to the same slug (data loss risk)
        slug_to_names: dict[str, list[str]] = defaultdict(list)
        for composer_name in self.by_composer:
            slug_to_names[_make_slug(composer_name)].append(composer_name)
        for slug, names in slug_to_names.items():
            if len(names) > 1:
                logger.warning(
                    "Slug collision: %d composers share slug '%s': %s",
                    len(names),
                    slug,
                    ", ".join(f'"{n}"' for n in names),
                )

    def get_composer(self, slug: str) -> Composer | None:
        return self._composer_map.get(slug)

    def get_composer_tracks(self, slug: str) -> list[Track]:
        for composer_name, tracks in self.by_composer.items():
            if _make_slug(composer_name) == slug:
                return tracks
        return []

    def search(
        self,
        q: str | None = None,
        composer: str | None = None,
        year: int | None = None,
        sort: str = "composer",
        order: str = "asc",
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedTracks:
        results = self.tracks

        if composer:
            results = [t for t in results if _make_slug(t.composer) == composer]

        if year:
            results = [t for t in results if t.year == year]

        if q:
            terms = q.lower().split()
            results = [
                t
                for t in results
                if all(
                    term in t.composer.lower() or term in t.title.lower()
                    for term in terms
                )
            ]

        sort_keys = {
            "composer": lambda t: (t.composer.lower(), t.title.lower()),
            "title": lambda t: t.title.lower(),
            "duration": lambda t: t.duration,
            "year": lambda t: (t.year, t.composer.lower()),
        }
        key_fn = sort_keys.get(sort, sort_keys["composer"])
        results = sorted(results, key=key_fn, reverse=(order == "desc"))

        total = len(results)
        return PaginatedTracks(total=total, skip=skip, limit=limit, items=results[skip : skip + limit])

    def get_competition(self, year: int) -> CompetitionYear | None:
        tracks = self.by_year.get(year)
        if not tracks:
            return None

        # Group by round, then by session
        rounds_dict: dict[int | None, dict[int | None, list[Track]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for track in tracks:
            rounds_dict[track.round][track.session].append(track)

        rounds = []
        for round_num in sorted(rounds_dict.keys(), key=lambda x: (x is None, x)):
            sessions = []
            for session_num in sorted(
                rounds_dict[round_num].keys(), key=lambda x: (x is None, x)
            ):
                session_tracks = sorted(
                    rounds_dict[round_num][session_num],
                    key=lambda t: (t.piece_index or 0),
                )
                sessions.append(
                    CompetitionSession(session=session_num, tracks=session_tracks)
                )
            rounds.append(
                CompetitionRound(
                    round=round_num,
                    sessions=sessions,
                    track_count=sum(len(s.tracks) for s in sessions),
                )
            )

        return CompetitionYear(
            year=year,
            track_count=len(tracks),
            rounds=rounds,
        )

    def get_competitions(self) -> list[CompetitionYear]:
        return [
            self.get_competition(year)
            for year in sorted(self.by_year.keys())
            if self.get_competition(year) is not None
        ]


# Singleton instance
store = DatasetStore()
