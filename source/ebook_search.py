import os, pathlib, re, termcolor, ebooklib, bs4, ast
from pathlib import Path
from ipdb import set_trace as s

EBOOK_DIR = Path(__file__).parent / "ebooks"

def setup_ebooks(ebook_paths: list, language: str):
    try:
        for language in VALID_LANGUAGE_CODES:
            ebook_paths = CONFIG_PARSER[language]["ebook_paths"]
            ebook_paths = ast.literal_eval(ebook_paths)
            for ebook_path in ebook_paths:
                ebook_name = os.path.splitext(os.path.basename(ebook_path))[0]
                bs_ebook_path = (
                    pathlib.Path(__file__).parent / f"ebooks/{language}/{ebook_name}.txt"
                )
                if not bs_ebook_path.exists():
                    print(f"Setting up {ebook_name}...")
                    bs_ebook_path.parent.mkdir(exist_ok=True, parents=True)
                    bs_ebook_path.write_text(str(epub_to_bs(str(ebook_path)).text))
    except KeyError as e:
        pass



def epub_to_bs(epub_path: str):
    """Picks all EpubHtmls from the epub file and returns a nice BeautifulSoup object with them"""
    book = ebooklib.epub.read_epub(epub_path, ignore_ncx=True)
    book_items = book.get_items()
    ugly_book_html = bytes()
    for item in book_items:
        item_class = str(item.__class__)
        if item_class == "<class 'ebooklib.epub.EpubHtml'>":
            ugly_book_html += item.content + bytes("\n", "utf-8")
    book_html = bs4.BeautifulSoup(ugly_book_html, "html.parser")
    return book_html


def slice_with_red_color(text: str, start: int, end: int):
    to_be_colored = text[start:end]
    colored_slice = termcolor.colored(to_be_colored, "red")
    result = f"{text[:start]}{colored_slice}{text[end:]}"
    return result


def red_groups(match: re.Match) -> str:
    """Returns match.group() but with all elements of match.groups()
    painted in red.

    Args:
        match (re.Match): Match object

    Returns:
        str: match.group() but with red groups
    """
    full_match = match.group()
    full_start, _ = match.span()
    for i in range(len(match.groups())):
        span_group = match.span(i + 1)
        start, end = span_group[0] - full_start, span_group[1] - full_start
        full_match = slice_with_red_color(full_match, start, end)
    return full_match


def findall_with_red_groups(pattern, text, **kwargs):
    """The same as re.findall but with the usage of red_groups()

    Args:
        pattern (re.Pattern): pattern
        text (str): text

    Returns:
        list: same style as re.findall
    """
    match_iterator = re.finditer(pattern, text, **kwargs)
    result = []
    for match in match_iterator:
        red_match = red_groups(match)
        result.append(red_match)
    return result


def get_examples(words, book_txt):
    word_tuple = words
    if isinstance(words, str):
        word_tuple = tuple([words])
    examples = set()
    for word in word_tuple:
        word_split = word.split(" ")
        stem, preffix = (word, "") if len(word_split) == 1 else word_split
        if preffix:
            patterns = [
                rf"^[^.?!]*?\b({stem})\b[\w\s]*?\b({preffix})[,;][^.]*?[.!?]",
                rf"^[^.?!]*?\b({preffix}{stem})\b[^.]*?[.!?]",
                rf"^[^.?!]*?\b({stem})\b[\w\s]*?({preffix})[.!?]",
            ]
            compiled_patterns = [
                re.compile(pattern, flags=re.MULTILINE) for pattern in patterns
            ]
            bs4_examples = [
                findall_with_red_groups(pattern, book_txt)
                for pattern in compiled_patterns
            ]
            # planify bs4_examples. Otherwise bs4_examples would look like [[...],[...],[...]]
            bs4_examples = [
                example for findall_list in bs4_examples for example in findall_list
            ]
        else:
            pattern = rf"^[^.?!]*?\b({stem})\b[^.]*?[.?!]"
            bs4_examples = findall_with_red_groups(
                pattern, book_txt, flags=re.MULTILINE
            )
        for example in bs4_examples:
            if preffix:
                examples.add(example)
            else:
                examples.add(example)
    return examples


book_txt = """[1] Warum musst du immer im Kino einschlafen?
[2] Gestern Nacht ist unsere Oma friedlich eingeschlafen.
[3] Wenn ich noch länger knie, schlafen mir die Füße ein.
[4] Über die Jahre ist dann die Beziehung leider eingeschlafen.
[5] Du schläfst mit mir.
"""
inflections = (
    "schläfst ein",
    "schlaft ein",
    "schlief ein",
    "schlaf ein",
    "schläft ein",
    "eingeschlafen",
    "schliefe ein",
    "schlafe ein",
    "schlafen ein",
)
# for i in get_examples(inflections, book_txt):
#     print(repr(i))
