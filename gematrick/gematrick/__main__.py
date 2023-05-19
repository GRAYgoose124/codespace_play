from . import BookData


def main():
    torah_data = BookData(books="Torah")
    # neviim_data = BookData(books="Nevi'im")
    # ketuvim_data = BookData(books="Ketuvim")
    # tanach_data = BookData()
    # l = tanach_data.to_hebrew_string().text_only().length

    print(torah_data.verse_slices[0:5])
    # dump tanach data to json well formatted


if __name__ == "__main__":
    main()
