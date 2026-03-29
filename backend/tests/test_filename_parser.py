from app.filename_parser import ParsedFilename, parse_filename


class TestRoundExtraction:
    def test_2004_r1(self):
        f = "MIDI-Unprocessed_XP_08_R1_2004_01-02_ORIG_MID--AUDIO_08_R1_2004_01_Track01_wav.midi"
        result = parse_filename(f, 2004)
        assert result.round == 1
        assert result.session == 8
        assert result.piece_index == 1

    def test_2004_r2(self):
        f = "MIDI-Unprocessed_SMF_02_R2_2004_01-05_ORIG_MID--AUDIO_02_R2_2004_05_Track05_wav.midi"
        result = parse_filename(f, 2004)
        assert result.round == 2
        assert result.session == 2
        assert result.piece_index == 5

    def test_2006(self):
        f = "MIDI-Unprocessed_01_R1_2006_01-09_ORIG_MID--AUDIO_01_R1_2006_01_Track01_wav.midi"
        result = parse_filename(f, 2006)
        assert result.round == 1
        assert result.session == 1
        assert result.piece_index == 1

    def test_2008_r3(self):
        f = "MIDI-Unprocessed_02_R3_2008_01-03_ORIG_MID--AUDIO_02_R3_2008_wav--1.midi"
        result = parse_filename(f, 2008)
        assert result.round == 3
        assert result.session == 2
        assert result.piece_index == 1

    def test_2009(self):
        f = "MIDI-Unprocessed_07_R2_2009_01_ORIG_MID--AUDIO_07_R2_2009_07_R2_2009_01_WAV.midi"
        result = parse_filename(f, 2009)
        assert result.round == 2
        assert result.session == 7

    def test_2011(self):
        f = "MIDI-Unprocessed_01_R1_2011_MID--AUDIO_R1-D1_02_Track02_wav.midi"
        result = parse_filename(f, 2011)
        assert result.round == 1
        assert result.piece_index == 2

    def test_2013(self):
        f = "ORIG-MIDI_01_7_6_13_Group__MID--AUDIO_01_R1_2013_wav--1.midi"
        result = parse_filename(f, 2013)
        assert result.round == 1
        assert result.session == 1
        assert result.piece_index == 1

    def test_2014(self):
        f = "MIDI-UNPROCESSED_01-03_R1_2014_MID--AUDIO_01_R1_2014_wav--1.midi"
        result = parse_filename(f, 2014)
        assert result.round == 1
        assert result.session == 1
        assert result.piece_index == 1

    def test_2015(self):
        f = "MIDI-Unprocessed_R1_D1-1-8_mid--AUDIO-from_mp3_01_R1_2015_wav--1.midi"
        result = parse_filename(f, 2015)
        assert result.round == 1
        assert result.session == 1
        assert result.piece_index == 1

    def test_2018_recital(self):
        f = "MIDI-Unprocessed_Recital1-3_MID--AUDIO_01_R1_2018_wav--1.midi"
        result = parse_filename(f, 2018)
        assert result.round == 1
        assert result.session == 1
        assert result.piece_index == 1

    def test_2018_chamber_r3(self):
        f = "MIDI-Unprocessed_Chamber3_MID--AUDIO_10_R3_2018_wav--1.midi"
        result = parse_filename(f, 2018)
        assert result.round == 3
        assert result.session == 10
        assert result.piece_index == 1


class TestYear2017:
    def test_july_6_is_r1(self):
        f = "MIDI-Unprocessed_041_PIANO041_MID--AUDIO-split_07-06-17_Piano-e_1-01_wav--1.midi"
        result = parse_filename(f, 2017)
        assert result.round == 1
        assert result.session == 1
        assert result.piece_index == 1

    def test_july_7_is_r1(self):
        f = "MIDI-Unprocessed_066_PIANO066_MID--AUDIO-split_07-07-17_Piano-e_3-02_wav--3.midi"
        result = parse_filename(f, 2017)
        assert result.round == 1
        assert result.session == 2
        assert result.piece_index == 3

    def test_july_8_is_r2(self):
        f = "MIDI-Unprocessed_071_PIANO071_MID--AUDIO-split_07-08-17_Piano-e_1-04_wav--4.midi"
        result = parse_filename(f, 2017)
        assert result.round == 2
        assert result.session == 4
        assert result.piece_index == 4

    def test_july_9_is_r3(self):
        f = "MIDI-Unprocessed_079_PIANO079_MID--AUDIO-split_07-09-17_Piano-e_1-04_wav--4.midi"
        result = parse_filename(f, 2017)
        assert result.round == 3
        assert result.session == 4
        assert result.piece_index == 4

    def test_2017_underscore_variant(self):
        f = "MIDI-Unprocessed_083_PIANO083_MID--AUDIO-split_07-09-17_Piano-e_2_-06_wav--1.midi"
        result = parse_filename(f, 2017)
        assert result.round == 3
        assert result.piece_index == 1
