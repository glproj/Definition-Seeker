import glob, os, re, bs4, pathlib, termcolor, ipdb, requests
from ebooklib import epub
import configparser
from collections import Counter
from ipdb import set_trace as s

CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/.configfile.ini"
CONFIG_PARSER = configparser.ConfigParser()
CONFIG_PARSER.read(CONFIG_PATH)
VALID_LANGUAGES = {"en": "English", "de": "Deutsch", "br": "Português Brasileiro"}
VALID_LANGUAGE_CODES = VALID_LANGUAGES.keys()
SUPPORTED_EXTENSIONS = ["epub", "pdf"]
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


class SetRecordsUpdates(set):
    """set but it keeps track of updates.
    >>> record = SetRecordsUpdates()
    >>> record.update(['Gloria'])
    >>> record.update(['Gloria'])
    >>> record.update(['excelsis'])
    >>> record.updates
    3
    >>> record.update_counter
    collections.Counter({'Gloria': 2, 'excelsis': 1})"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_counter = Counter()
        self.updates = 0

    def update(self, *args, **kwargs):
        self.update_counter.update(args[0])
        super().update(*args, **kwargs)
        self.updates += 1

    def get_updates(self, element):
        return self.update_counter.get(element, None)


def in_common(*args) -> dict:
    """Returns dictionary in the form
    {common_text: (start_index, end_index)}

    >>> in_common(
    ...     'qui tollis peccata mundi, miserere nobis;',
    ...     'qui tollis peccata mundi, suscipe deprecationem nostram.'
    ... )
    {'qui tollis peccata mundi, ': (0, 26), 's': (28, 29)}

    Returns:
        dict: {common_text: (start_index, end_index)}
    """
    common_sections = dict()
    common_text = ""
    for index, (characters) in enumerate(zip(*args)):
        if len(set(characters)) == 1:
            common_text += characters[0]
            # if start_index doesn't exist, then we are
            # necessarily in a new common section, since
            # we going to delete start_index at the end
            # of this common section.
            try:
                start_index
            except NameError:
                start_index = index
        else:
            try:
                end_index = index
                common_sections[common_text] = (start_index, end_index)
                common_text = ""
                del start_index
            except NameError:
                continue
    return common_sections


def remove_common(*args) -> list:
    """Return a list without any common character sequences
    between its elements.
    >>> remove_common(
    ...     "Herr, eingeborener Sohn, Jesus Christus.",
    ...     "Herr und Gott, Lamm Gottes,"
    ... )
    [", eingeborener Sohn, Jesus Christus.", " und Gott, Lamm Gottes,"]

    Returns:
        list: list without common character sequences between its elements
    """
    commons = in_common(*args)
    result = []
    for text in args:
        text_without_common_part = text
        decrease_in_len = 0
        for start, end in commons.values():
            actual_start = start - decrease_in_len
            actual_end = end - decrease_in_len
            text_without_common_part = (
                text_without_common_part[:actual_start]
                + text_without_common_part[actual_end:]
            )
            decrease_in_len = end - start
        result.append(text_without_common_part)
    return result


def absolute_file_paths(directory: str) -> list:
    """Returns the absolute path of every file inside directory

    Args:
        directory (str): directory path

    Returns:
        list: list with the absolute path of every file inside directory
    """
    return glob.glob(os.path.join(directory, "**"))


def lowercase_extension(image_path: str)->str:
    """Returns image_path but with a lowercase extension
    For example, the path "/dir/GregoryI.JPG" will be turned
    into "/dir/GregoryI.jpg"

    Args:
        image_path (str): image path

    Returns:
        str: new image path
    """
    extension = re.search("\.(\w+)", image_path).groups()[0]
    new_image_path = os.path.splitext(image_path)[0] + f".{extension.lower()}"
    return new_image_path


def remove_navigable_strings(bs4_list: list):
    """Remove every instance of bs4.NavigableString out of list
    of bs4 tags.

    Args:
        bs4_list (list): list with tags

    Returns:
        list: list without any bs4.NavigableString instances
    """
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
