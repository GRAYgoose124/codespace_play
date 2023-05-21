from hebrew import Hebrew
from grapheme import graphemes
from grapheme.finder import GraphemeIterator
from . import BookData

import mpmath as m

m.mp.dps = 1000
pi_digits = str(m.pi)[2:]


def get_pi_gematria_index(word: Hebrew) -> int:
    """Note this is 0th indexed into pi_digits, not 1st indexed."""
    return pi_digits.index(str(word.gematria()))


def main():
    torah_data = BookData(books="Torah")
    # neviim_data = BookData(books="Nevi'im")
    # ketuvim_data = BookData(books="Ketuvim")
    # tanach_data = BookData()
    # l = tanach_data.to_hebrew_string().text_only().length

    # start, end = (2, 6)
    # [print(e) for e in torah_data[start:end]]

    assert get_pi_gematria_index(Hebrew("בבל")) == (86 - 1)

    torah = torah_data.to_hebrew_string().text_only()
    # print(torah.slice(12852, 12852 + 10))

    print(torah_data.get_all_word_indices("בבל"))

    print("Genesis 11:4", torah_data.verse_by_ref(11, 4))


if __name__ == "__main__":
    main()
