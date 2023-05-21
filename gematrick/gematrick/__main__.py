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


def babel_investigation(torah_data: BookData):
    assert get_pi_gematria_index(Hebrew("בבל")) == (86 - 1)
    # print(torah_data.get_all_word_indices("בבל"))

    #     the Babel Tower ELS begins at 12,853
    # the first occurrence of 12853 in pi begins at position 252,359
    # 252 + 359 = 611, the gematria value of Torah (תורה) is 611
    gen114 = torah_data.verse_by_ref(11, 4)

    #    Dan 9:13 is Bible verse # 22,002
    # Luk 13:18 is Bible verse # 25,537
    # 25,537 - 22,002 = 3,535 (the gematria of Gen 11:4)
    assert Hebrew(gen114).gematria() == 3535

    print("Genesis 11:4", gen114)
    print("Letter #12856", torah_data.letters[12856])
    # generate aleph tower for 1850 (50*37) ELS


def main():
    torah_data = BookData(books="Torah")
    # neviim_data = BookData(books="Nevi'im")
    # ketuvim_data = BookData(books="Ketuvim")
    # tanach_data = BookData()
    # l = tanach_data.to_hebrew_string().text_only().length

    # start, end = (2, 6)
    # [print(e) for e in torah_data[start:end]]

    # torah = torah_data.to_hebrew_string().text_only()

    babel_investigation(torah_data)


if __name__ == "__main__":
    main()
