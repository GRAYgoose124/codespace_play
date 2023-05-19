import functools
from hebrew import Hebrew, GematriaTypes
import grapheme

import json

special_words = {
    "torah": (
        Hebrew("תורה"),
        611,
    ),  # gematria 611 - 611 commandments, 2 for the 2 commandments that were said by God = 613
    "yh": (Hebrew("יה"), 15),
    "el": (Hebrew("אל"), 31),
    "israel": (Hebrew("ישראל"), 541),
    "moses": (Hebrew("משה"), 345),
    # "the man": (Hebrew("האדם"), 45),
}


def get_special_gematrias():
    return {k: v[0].gematria() for k, v in special_words.items()}


def assert_special_gematrias():
    for k, v in special_words.items():
        assert (
            v[0].gematria() == v[1]
        ), f"{k} gematria is {v[0].gematria()}, should be {v[1]}"


TORAH = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
NEVIIM = [
    "Joshua",
    "Judges",
    "I Samuel",
    "II Samuel",
    "I Kings",
    "II Kings",
    "Isaiah",
    "Jeremiah",
    "Ezekiel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
]
KETUVIM = [
    "Psalms",
    "Proverbs",
    "Job",
    "Song of Solomon",
    "Ruth",
    "Lamentations",
    "Ecclesiastes",
    "Esther",
    "Daniel",
    "Ezra",
    "Nehemiah",
    "I Chronicles",
    "II Chronicles",
]

TANACH = TORAH + NEVIIM + KETUVIM


class BookData:
    def __init__(self, books=TANACH):
        self.data = []
        self.books = books

        self.__load_books()

    def __load_books(self):
        with open("hebrew.json", "r") as f:
            data = json.load(f)
            for book in self.books:
                print(f"Loading {book}...")
                self.data.extend(data[book])

    def chapters(self):
        for chapter in self.data:
            yield chapter

    def verses(self):
        for chapter in self.chapters():
            for verse in chapter:
                yield verse

    def words(self):
        for verse in self.verses():
            for word in verse:
                yield word

    def just_words(self):
        for word in self.words():
            yield word[0]

    def as_hebrew(self):
        for word in self.just_words():
            yield Hebrew(word)

    @functools.lru_cache(maxsize=128)
    def to_hebrew_string(self):
        return Hebrew(self.__str__())

    def gematria(self):
        return self.to_hebrew_string().gematria()

    def __str__(self) -> str:
        return " ".join(self.just_words())

    def __len__(self):
        """Return total books that were loaded."""
        return len(self.data)

    def __contains__(self, item):
        """Return True if item is in the list of books."""
        return item in self.books


def main():
    # print("Special words gematrias:", get_special_gematrias())
    assert_special_gematrias()

    torah_data = BookData(books=TORAH)
    # neviim_data = BookData(books=NEVIIM)
    # ketuvim_data = BookData(books=KETUVIM)

    # tanach_data = BookData()

    # l = tanach_data.to_hebrew_string().text_only().length

    if "Genesis" in torah_data:
        hs = torah_data.as_hebrew()
        word_sum = 0
        roshei_tevot_sum = 0
        for _ in range(7):
            h = next(hs)
            word_sum += h.gematria()
            roshei_tevot_sum += Hebrew(h.slice(0, 1)).gematria()
        assert (
            word_sum == 2701
        ), f"sum of first 7 words of Genesis is {word_sum}, should be 2701"
        assert (
            roshei_tevot_sum == 22
        ), f"sum of roshei tevot of first 7 words of Genesis is {roshei_tevot_sum}, should be 22"
        print("All test gematrias are correct!")

    print("\n", torah_data.gematria())


if __name__ == "__main__":
    main()
