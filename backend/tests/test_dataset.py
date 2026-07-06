from pathlib import Path

from app.data.dataset import DatasetStore

# Use mock data for CI, real data when available
CSV_PATH = Path(__file__).resolve().parent / "data" / "minimal.csv"


class TestDatasetLoad:
    def setup_method(self):
        self.store = DatasetStore()
        self.store.load(CSV_PATH)

    def test_total_tracks(self):
        assert len(self.store.tracks) == 4

    def test_composer_count(self):
        assert len(self.store.composers) == 3

    def test_years(self):
        expected = {2004, 2014, 2018}
        assert set(self.store.by_year.keys()) == expected

    def test_tracks_have_ids(self):
        ids = [t.id for t in self.store.tracks]
        assert ids == list(range(4))

    def test_all_tracks_have_round(self):
        missing = [t for t in self.store.tracks if t.round is None]
        assert len(missing) == 0, f"{len(missing)} tracks missing round info"


class TestSearch:
    def setup_method(self):
        self.store = DatasetStore()
        self.store.load(CSV_PATH)

    def test_search_by_query(self):
        results = self.store.search(q="chopin")
        assert len(results) > 0
        assert all("Chopin" in t.composer for t in results)

    def test_search_by_title(self):
        results = self.store.search(q="nocturne")
        assert len(results) > 0
        assert all("nocturne" in t.title.lower() for t in results)

    def test_filter_by_year(self):
        results = self.store.search(year=2018)
        assert len(results) == 2
        assert all(t.year == 2018 for t in results)

    def test_filter_by_composer_slug(self):
        results = self.store.search(composer="frederic-chopin")
        assert len(results) > 0
        assert all(t.composer == "Frédéric Chopin" for t in results)

    def test_sort_by_duration_desc(self):
        results = self.store.search(sort="duration", order="desc")
        durations = [t.duration for t in results]
        assert durations == sorted(durations, reverse=True)


class TestCompetition:
    def setup_method(self):
        self.store = DatasetStore()
        self.store.load(CSV_PATH)

    def test_competition_2018(self):
        comp = self.store.get_competition(2018)
        assert comp is not None
        assert comp.year == 2018
        assert comp.track_count == 2
        round_nums = [r.round for r in comp.rounds]
        assert 1 in round_nums

    def test_competition_invalid_year(self):
        comp = self.store.get_competition(1999)
        assert comp is None

    def test_all_competitions(self):
        comps = self.store.get_competitions()
        assert len(comps) == 3
        years = [c.year for c in comps]
        assert years == sorted(years)


class TestComposer:
    def setup_method(self):
        self.store = DatasetStore()
        self.store.load(CSV_PATH)

    def test_get_composer_by_slug(self):
        composer = self.store.get_composer("frederic-chopin")
        assert composer is not None
        assert composer.name == "Frédéric Chopin"

    def test_composer_tracks(self):
        tracks = self.store.get_composer_tracks("frederic-chopin")
        assert len(tracks) > 0
        assert all(t.composer == "Frédéric Chopin" for t in tracks)

    def test_composers_sorted_by_count(self):
        counts = [c.track_count for c in self.store.composers]
        assert counts == sorted(counts, reverse=True)
