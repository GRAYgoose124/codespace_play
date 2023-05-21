import functools
from pathlib import Path
from hebrew import Hebrew, GematriaTypes
import grapheme

import json

from gematrick.books import TORAH, NEVIIM, KETUVIM, TANACH


class FrameSlice:
    def __init__(self, iter_method):
        self.iter_method = iter_method
        self.iter_instance = None

        self.__iter__()

    def __iter__(self):
        self.iter_instance = self.iter_method()
        return self

    def __next__(self):
        if self.iter_instance is None:
            raise StopIteration

        next_value = next(self.iter_instance)

        return next_value

    def __getitem__(self, item):
        data = []

        if isinstance(item, slice):
            start = item.start or 0
            while start > 0:
                print("Skipping...")
                self.__next__()
                start -= 1

            stop = item.stop - item.start if item.stop else None
            if stop is not None:  # if end of slice is specified
                while stop > 0:
                    verse = self.__next__()
                    words = [e[0] for e in verse]
                    data.append(words)
                    stop -= 1
            else:  # if end of slice is not specified, continue till the end
                try:
                    while True:
                        verse = self.__next__()
                        words = [e[0] for e in verse]
                        data.append(words)
                except StopIteration:
                    pass

            return data

        else:
            while item > 0:
                self.__next__()
                item -= 1
            return self.__next__()


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

    def chapter(self, chapter_number):
        return self.data[chapter_number - 1]

    def verse_by_ref(self, chapter_number, verse_number, pretty=True):
        if pretty:
            return " ".join(
                [e[0] for e in self.chapter(chapter_number)[verse_number - 1]]
            )
        else:
            return self.chapter(chapter_number)[verse_number - 1]

    @property
    def letters(self):
        if self.__letters is None:
            self.__letters = []
            for chapter in self.data:
                for verse in chapter:
                    for word in verse:
                        for letter in word[0]:
                            self.__letters.append(letter)
        return self.__letters

    def letter(self, index):
        return self.letters[index]

    def chapters(self):
        for chapter in self.data:
            yield chapter

    def verses(self):
        for chapter in self.chapters():
            for verse in chapter:
                yield verse

    def __getitem__(self, item):
        return FrameSlice(self.verses)[item]

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

    def get_all_word_indices(self, word: Hebrew) -> list[int]:
        indices = []
        for i, w in enumerate(self.just_words()):
            if word in w:
                indices.append(i)

        return indices

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
