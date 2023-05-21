import unittest

from hebrew import Hebrew
from gematrick import BookData

special_words = {
    "torah": (
        Hebrew("תורה"),
        611,
    ),  # gematria 611 - 611 commandments, 2 for the 2 commandments that were said by God = 613
    "yh": (Hebrew("יה"), 15),
    "el": (Hebrew("אל"), 31),
    "israel": (Hebrew("ישראל"), 541),
    "moses": (Hebrew("משה"), 345),
    "adam": (Hebrew("אדם"), 45),
    "babel": (Hebrew("בבל"), 34),
}


def get_special_gematrias():
    return {k: v[0].gematria() for k, v in special_words.items()}


def assert_special_gematrias():
    for k, v in special_words.items():
        assert (
            v[0].gematria() == v[1]
        ), f"{k} gematria is {v[0].gematria()}, should be {v[1]}"


class TestBasic(unittest.TestCase):
    def test_torah(self):
        torah_data = BookData(books="Torah")
        self.assertEqual(len(torah_data), 5)
        self.assertIn("Genesis", torah_data)
        self.assertIn("Exodus", torah_data)
        self.assertIn("Leviticus", torah_data)
        self.assertIn("Numbers", torah_data)
        self.assertIn("Deuteronomy", torah_data)

    def test_neviim(self):
        neviim_data = BookData(books="Nevi'im")
        self.assertEqual(len(neviim_data), 21)
        self.assertIn("Joshua", neviim_data)
        self.assertIn("Judges", neviim_data)
        self.assertIn("I Samuel", neviim_data)
        self.assertIn("II Samuel", neviim_data)
        self.assertIn("I Kings", neviim_data)
        self.assertIn("II Kings", neviim_data)
        self.assertIn("Isaiah", neviim_data)
        self.assertIn("Jeremiah", neviim_data)
        self.assertIn("Ezekiel", neviim_data)
        self.assertIn("Hosea", neviim_data)
        self.assertIn("Joel", neviim_data)
        self.assertIn("Amos", neviim_data)
        self.assertIn("Obadiah", neviim_data)
        self.assertIn("Jonah", neviim_data)
        self.assertIn("Micah", neviim_data)
        self.assertIn("Nahum", neviim_data)
        self.assertIn("Habakkuk", neviim_data)
        self.assertIn("Zephaniah", neviim_data)
        self.assertIn("Haggai", neviim_data)
        self.assertIn("Zechariah", neviim_data)
        self.assertIn("Malachi", neviim_data)

    def test_ketuvim(self):
        ketuvim_data = BookData(books="Ketuvim")
        self.assertEqual(len(ketuvim_data), 13)
        self.assertIn("Psalms", ketuvim_data)
        self.assertIn("Proverbs", ketuvim_data)
        self.assertIn("Job", ketuvim_data)
        self.assertIn("Song of Solomon", ketuvim_data)
        self.assertIn("Ruth", ketuvim_data)
        self.assertIn("Lamentations", ketuvim_data)

    def test_special_words(self):
        assert_special_gematrias()

    def test_tanach(self):
        self.assertEqual(len(BookData(books="Tanach")), 39)

    def test_genesis_gematria(self):
        genesis_data = BookData(books="Genesis")
        assert "Genesis" in genesis_data
        assert len(genesis_data) == 1

        hebrew_iter = genesis_data.as_hebrew()
        word_sum = 0
        roshei_tevot_sum = 0
        for _ in range(7):
            h = next(hebrew_iter)
            word_sum += h.gematria()
            roshei_tevot_sum += Hebrew(h.slice(0, 1)).gematria()
        assert (
            word_sum == 2701
        ), f"sum of first 7 words of Genesis is {word_sum}, should be 2701"
        assert (
            roshei_tevot_sum == 22
        ), f"sum of roshei tevot of first 7 words of Genesis is {roshei_tevot_sum}, should be 22"
        print("All test gematrias are correct!")

    def test_verse_slice(self):
        torah_data = BookData(books="Torah")

        tests = [
            (2, 6),
            (None, 6),
            (2, None),
        ]

        for start, end in tests:
            if start is None:
                start = 0
            if end is None:
                end = len(torah_data)

            assert (
                len([print(e) for e in torah_data[start:end]]) == end - start
            ), f"Slice failed: [{start}:{end}] length not {end - start}"
