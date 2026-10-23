import io
import os
import sys
import tempfile
import unittest
import requests
import mido

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chart_extractor import (
    FESTIVAL_MIDI_KEY,
    decrypt_midi,
    midi_to_chart,
    create_song_ini,
    extract_chart_files,
)
from FFR import FortniteTracksGUI


class TestChartExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Butter Barn Hoedown test data
        cls.dat_url = "https://cdn2.unrealengine.com/y3iotu5bothnse3s-71d4f25bc425.dat"
        cls.song_info = {
            "title": "Butter Barn Hoedown",
            "artist": "Epic Games",
            "album": "Fortnite",
            "release_year": 2021,
            "genre": ["Country"],
            "duration": 157,
            "mu": cls.dat_url,
            "cover_art_url": "https://cdn2.unrealengine.com/8trfqm9nofp8xeoj-512x512-4d008e153456.jpg",
            "intensities": {"pg": 4, "pb": 2, "pd": 1, "vl": 4, "gr": 4, "ba": 1, "ds": 2},
            "qi_data": {"preview": {"starttime": 44.0816}},
        }
        resp = requests.get(cls.dat_url, timeout=20)
        resp.raise_for_status()
        cls.raw_dat = resp.content

    def test_decryption(self):
        mid_bytes = decrypt_midi(self.raw_dat, FESTIVAL_MIDI_KEY)
        self.assertTrue(mid_bytes.startswith(b"MThd"), "Decrypted file must start with MIDI header MThd")
        mid = mido.MidiFile(file=io.BytesIO(mid_bytes))
        self.assertGreater(len(mid.tracks), 0, "MIDI must contain tracks")
        track_names = [t.name for t in mid.tracks]
        self.assertIn("PLASTIC GUITAR", track_names)
        self.assertIn("PLASTIC DRUMS", track_names)
        self.assertIn("PLASTIC BASS", track_names)

    def test_chart_conversion(self):
        mid_bytes = decrypt_midi(self.raw_dat, FESTIVAL_MIDI_KEY)
        mid = mido.MidiFile(file=io.BytesIO(mid_bytes))
        chart_text = midi_to_chart(mid, self.song_info)

        self.assertIn("[Song]", chart_text)
        self.assertIn('Name = "Butter Barn Hoedown"', chart_text)
        self.assertIn("[SyncTrack]", chart_text)
        self.assertIn("[Events]", chart_text)
        self.assertIn("[ExpertSingle]", chart_text)
        self.assertIn("[ExpertDoubleBass]", chart_text)
        self.assertIn("[ExpertDrums]", chart_text)

    def test_song_ini_generation(self):
        ini_text = create_song_ini(self.song_info)
        self.assertIn("[song]", ini_text)
        self.assertIn("name = Butter Barn Hoedown", ini_text)
        self.assertIn("artist = Epic Games", ini_text)
        self.assertIn("diff_guitar = 4", ini_text)
        self.assertIn("diff_bass = 2", ini_text)
        self.assertIn("diff_drums = 1", ini_text)

    def test_extract_midi_files_end_to_end(self):
        test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp_test_output"))
        try:
            created = extract_chart_files(self.song_info, test_dir)
            # Must NOT create .chart
            self.assertFalse(os.path.exists(os.path.join(test_dir, "notes.chart")), "notes.chart should NOT be created by default")
            # Must create .mid, song.ini, and album.png
            self.assertTrue(os.path.exists(os.path.join(test_dir, "notes.mid")), "notes.mid must be created")
            self.assertTrue(os.path.exists(os.path.join(test_dir, "song.ini")), "song.ini must be created")
            self.assertTrue(os.path.exists(os.path.join(test_dir, "album.png")), "album.png must be created")

            mid_size = os.path.getsize(os.path.join(test_dir, "notes.mid"))
            self.assertGreater(mid_size, 50000, "notes.mid size should be substantial")
        finally:
            if os.path.exists(test_dir):
                import shutil
                shutil.rmtree(test_dir, ignore_errors=True)

    def test_unified_song_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            class DummyApp:
                def __init__(self, folder):
                    self.extract_folder = folder
                sanitize_folder_name = FortniteTracksGUI.sanitize_folder_name
                get_song_folder = FortniteTracksGUI.get_song_folder

            app = DummyApp(tmpdir)

            # 1. New folder creation: exactly the song title, no '- stems' or '- chart' suffix
            folder = app.get_song_folder("Butter Barn Hoedown", "Epic Games")
            expected = os.path.join(tmpdir, "Butter Barn Hoedown")
            self.assertEqual(folder, expected)
            self.assertTrue(os.path.isdir(expected))

            # 2. Legacy migration: if separate stems/chart folders already exist, merge them
            legacy_stems = os.path.join(tmpdir, "Legacy Track - stems")
            legacy_chart = os.path.join(tmpdir, "Legacy Track - chart")
            os.makedirs(legacy_stems, exist_ok=True)
            os.makedirs(legacy_chart, exist_ok=True)
            with open(os.path.join(legacy_stems, "Drums.wav"), "w") as f:
                f.write("audio")
            with open(os.path.join(legacy_chart, "notes.mid"), "w") as f:
                f.write("midi")

            unified = app.get_song_folder("Legacy Track", "Artist")
            expected_unified = os.path.join(tmpdir, "Legacy Track")
            self.assertEqual(unified, expected_unified)
            self.assertTrue(os.path.exists(os.path.join(expected_unified, "Drums.wav")))
            self.assertTrue(os.path.exists(os.path.join(expected_unified, "notes.mid")))
            self.assertFalse(os.path.exists(legacy_stems), "Legacy stems folder should be removed after merge")
            self.assertFalse(os.path.exists(legacy_chart), "Legacy chart folder should be removed after merge")


if __name__ == "__main__":
    unittest.main()
