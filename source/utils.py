import glob, os, re, bs4, pathlib, termcolor, ipdb, requests
from ebooklib import epub

TRENNBARE_PRÄFIXE = [
    "auseinander",
    "gegenüber",
    "hinterher",
    "entgegen",
    "zusammen",
    "herunter",
    "entlang",
    "zurecht",
    "entzwei",
    "herüber",
    "weiter",
    "runter",
    "nieder",
    "herauf",
    "heraus",
    "herbei",
    "herein",
    "hervor",
    "gegen",
    "rüber",
    "empor",
    "herab",
    "heran",
    "herum",
    "nach",
    "rein",
    "raus",
    "hoch",
    "fern",
    "fest",
    "fort",
    "heim",
    "auf",
    "aus",
    "bei",
    "ein",
    "mit",
    "vor",
    "hin",
    "her",
    "los",
    "weg",
    "an",
    "ab",
    "da",
    "zu",
]


class NeverSayNeverSession(requests.Session):
    def get(self, url, **kwargs):
        r"""Sends a GET requests until it doesn't timeout.
        Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        try:
            return super().get(url, **kwargs)
        except requests.exceptions.Timeout:
            print("Request timed out. Trying again...")
            return self.get(url, **kwargs)


def absolute_file_paths(directory):
    return glob.glob(os.path.join(directory, "**"))


def lowercase_extension(image_path: str):
    extension = re.search("\.(\w+)", image_path).groups()[0]
    new_image_path = os.path.splitext(image_path)[0] + f".{extension.lower()}"
    return new_image_path


def remove_navigable_strings(bs4_list: list):
    result = []
    for item in bs4_list:
        if str(item.__class__) == "<class 'bs4.element.NavigableString'>":
            continue
        result.append(item)
    return result


def epub_to_bs(epub_path: str):
    """Picks all EpubHtmls from the epub file and returns a nice BeautifulSoup object with them"""
    book = epub.read_epub(epub_path, options={"ignore_ncx": True})
    book_items = book.get_items()
    ugly_book_html = bytes()
    for item in book_items:
        item_class = str(item.__class__)
        if item_class == "<class 'ebooklib.epub.EpubHtml'>":
            ugly_book_html += item.content + bytes("\n", "utf-8")
    book_html = bs4.BeautifulSoup(ugly_book_html, "html.parser")
    return book_html
