import functools
from pathlib import Path
from hebrew import Hebrew, GematriaTypes
import grapheme

import json

from gematrick.books import TORAH, NEVIIM, KETUVIM, TANACH


class BookData:
    def __init__(self, books="tanach"):
        self.data = None
        self.books = None

        self.data_path = Path(__file__).parent / "data"

        self.__load(group=books)

    def __load(self, group="tanach"):
        """Load books of Tanach from based on grouping.

        Parameters
        ----------
        group : str
            Grouping of books to load. Valid values are "Tanach", "Torah", "nevi'im", "Ketuvim" and "Book" by name.

        """
        with open(self.data_path / "books.json", "r") as f:
            data = json.load(f)
            tanach_data = data["torah"] + data["neviim"] + data["ketuvim"]
            if group == "Tanach":
                self.books = tanach_data
            elif group in ["Torah", "Nevi'im", "Ketuvim"]:
                group = group.lower().replace("'", "")
                self.books = data[group]
            elif group in tanach_data:
                self.books = [group]
            else:
                raise ValueError(f"Invalid Tanach grouping: {group}")

        self.data = []
        with open(self.data_path / "tanach.json", "r") as f:
            data = json.load(f)
            for book in self.books:
                self.data.extend(data[book])

    def chapters(self):
        for chapter in self.data:
            yield chapter

    def verses(self):
        for chapter in self.chapters():
            for verse in chapter:
                yield verse

    @property
    def verse_slices(self):
        """Return a generator of verse slices, where each slice is a list of words in the verse."""
        for verse in self.verses():
            v = [word[0] for word in verse]
            yield v

    def words(self):
        for verse in self.verses():
            for word in verse:
                yield word

    def just_words(self):
        for word in self.words():
            yield word[0]

    def as_hebrew(self):
        """Not efficient, use BookData.to_hebrew_string() instead."""
        for word in self.just_words():
            yield Hebrew(word)

    @functools.lru_cache()
    def to_hebrew_string(self):
        return Hebrew(self.__str__())

    def gematria(self):
        return self.to_hebrew_string().gematria()

    @functools.lru_cache()
    def __str__(self) -> str:
        return " ".join(self.just_words())

    def __len__(self):
        """Return total books that were loaded."""
        return len(self.books)

    def __contains__(self, item):
        """Return True if item is in the list of books."""
        return item in self.books
