"""Extract competition round, session, and piece index from MAESTRO MIDI filenames."""

import re
from dataclasses import dataclass


@dataclass
class ParsedFilename:
    round: int | None  # 1, 2, or 3
    session: int | None
    piece_index: int | None


def _audio_portion(filename: str) -> str:
    """Extract the part of the filename after '--AUDIO'."""
    idx = filename.find("--AUDIO")
    if idx == -1:
        return filename
    return filename[idx:]


def _parse_2017(filename: str) -> ParsedFilename:
    """2017 has no explicit round — infer from date in filename.

    Dates: 07-06-17, 07-07-17 → R1; 07-08-17 → R2; 07-09-17 → R3
    Pattern: MIDI-Unprocessed_{NNN}_PIANO{NNN}_MID--AUDIO-split_{MM}-{DD}-17_Piano-e_{piano}-{session}_wav--{split}.midi
    """
    round_num = None
    date_match = re.search(r"(\d{2})-(\d{2})-17", filename)
    if date_match:
        day = int(date_match.group(2))
        if day in (6, 7):
            round_num = 1
        elif day == 8:
            round_num = 2
        elif day == 9:
            round_num = 3

    session = None
    # Session from Piano-e_{piano}-{session} portion
    session_match = re.search(r"Piano-e_\d+[_-]+(\d+)", filename)
    if session_match:
        session = int(session_match.group(1))

    piece_index = None
    split_match = re.search(r"wav--(\d+)", filename)
    if split_match:
        piece_index = int(split_match.group(1))

    return ParsedFilename(round=round_num, session=session, piece_index=piece_index)


def parse_filename(filename: str, year: int) -> ParsedFilename:
    """Parse round, session, and piece index from a MAESTRO MIDI filename."""
    if year == 2017:
        return _parse_2017(filename)

    audio = _audio_portion(filename)

    # Round: _R{n}_ or _R{n}-D{n}_ in the AUDIO portion
    round_num = None
    round_match = re.search(r"_R(\d+)[-_]", audio)
    if round_match:
        round_num = int(round_match.group(1))

    # Session: two-digit number immediately before _R{n}_ in AUDIO portion
    # Falls back to the MIDI portion (e.g., 2011 where AUDIO has _R{n}-D{n}_ format)
    session = None
    session_match = re.search(r"_(\d{1,2})_R\d+[-_]", audio)
    if session_match:
        session = int(session_match.group(1))
    else:
        # Try the MIDI portion (before --AUDIO)
        midi_portion = filename[: filename.find("--AUDIO")] if "--AUDIO" in filename else filename
        session_match = re.search(r"_(\d{1,2})_R\d+_", midi_portion)
        if session_match:
            session = int(session_match.group(1))

    # Piece index: --{n} suffix or Track{nn}
    piece_index = None
    split_match = re.search(r"wav--(\d+)", filename)
    if split_match:
        piece_index = int(split_match.group(1))
    else:
        track_match = re.search(r"Track(\d+)", filename)
        if track_match:
            piece_index = int(track_match.group(1))

    return ParsedFilename(round=round_num, session=session, piece_index=piece_index)
