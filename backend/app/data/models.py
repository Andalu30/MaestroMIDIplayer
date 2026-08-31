from pydantic import BaseModel, computed_field


def _make_slug(name: str) -> str:
    """Simple ASCII slug from a composer name."""
    # Avoid pulling in python-slugify; just do basic normalization
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    slug = ascii_str.lower().strip()
    slug = slug.replace(" ", "-").replace("/", "-")
    # collapse multiple hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


class Track(BaseModel):
    id: int
    composer: str
    title: str
    split: str
    year: int
    midi_filename: str
    audio_filename: str
    duration: float  # seconds
    round: int | None = None
    session: int | None = None
    piece_index: int | None = None

    @computed_field
    @property
    def duration_formatted(self) -> str:
        total = int(self.duration)
        minutes, seconds = divmod(total, 60)
        return f"{minutes}:{seconds:02d}"

    @computed_field
    @property
    def composer_slug(self) -> str:
        return _make_slug(self.composer)


class PaginatedTracks(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[Track]


class PaginatedTracks(BaseModel):
    total: int
    skip: int
    limit: int
    items: list["Track"]


class Composer(BaseModel):
    name: str
    slug: str
    track_count: int
    total_duration: float

    @computed_field
    @property
    def total_duration_formatted(self) -> str:
        total = int(self.total_duration)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s"


class CompetitionSession(BaseModel):
    session: int | None
    tracks: list[Track]


class CompetitionRound(BaseModel):
    round: int | None
    sessions: list[CompetitionSession]
    track_count: int


class CompetitionYear(BaseModel):
    year: int
    track_count: int
    rounds: list[CompetitionRound]
