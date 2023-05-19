from . import BookData


def main():
    torah_data = BookData(books="Torah")
    # neviim_data = BookData(books="Nevi'im")
    # ketuvim_data = BookData(books="Ketuvim")
    # tanach_data = BookData()
    # l = tanach_data.to_hebrew_string().text_only().length

    start, end = (2, 6)
    [print(e) for e in torah_data[start:end]]


if __name__ == "__main__":
    main()
