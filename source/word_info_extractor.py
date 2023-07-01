import requests, bs4, re, pathlib, urllib, json, gtts, tempfile
from utils import *
from collections import Counter

DWDS_URL = "https://www.dwds.de/wb/"
DUDEN_URL = "https://www.duden.de/rechtschreibung/"
WIKTIONARY_URL = "https://de.wiktionary.org/wiki/"
SESSION = NeverSayNeverSession()


def raise_word_not_available(request: requests.Request, netloc=""):
    if not netloc:
        netloc = urllib.parse.urlparse(request.url).netloc
    raise WordNotAvailable(f"Word not available at {netloc}")


def raise_word_not_available_404(request: requests.Request):
    if request.status_code == 404:
        raise_word_not_available(request)


class WordNotAvailable(Exception):
    pass


class CompatibilityMixin:
    @classmethod
    def compatible(self, word):
        """Returns word but with tweaks so that the request actually
        brings you to the word page. For example, the url
        "https://www.duden.de/rechtschreibung/Buchführung" will not
        return give you access to the Buchführung page; you'll have
        to convert Buchführung to Buchfuehrung for it to work
        properly (https://www.duden.de/rechtschreibung/Buchfuehrung).

        Returns:
            str or False: url-compatible word
        """
        return False


class Word(CompatibilityMixin):
    """Base class for website-specific word classes.
    Args:
        word (str): word that the object will represent.
        base_url (str): url of the site you gonna use.
        go_to_root (bool, optional): use _root_page() to set self.root_page. Defaults to False.
        api (bool, optional): set to True if you are using an api. Defaults to False.
    Relevant attributes:
        self.word = the same word you gave as input.
        self.page = parsed page from base_url + word.
        self.root_page = page you get redirected to when using _root_page().
        If go_to_root is set to false, then self.root_page is the same as self.page.
        self.root = word extracted from self.root_page.
        self.root_info = where all the relevant info is contained.
        self.ipa = ipa representation from word.
        self.root_ipa = ipa representation from root_word.
    """

    base_url = None
    api = False
    go_to_root = False
    options = ''

    def __init__(self, word):
        self.word = self.compatible(word) or word
        url = self.base_url + self.word + self.options
        request = SESSION.get(url, timeout=0.8)
        raise_word_not_available_404(request)
        if not self.api:
            self.page = bs4.BeautifulSoup(request.text, "html.parser")
            self.page = self._only_relevant_part(self.page)
        else:
            self.page = json.loads(request.text)

        self.ipa, self.pronunciation_url = self._get_pronunciation(self.page)
        if self.go_to_root and self.is_inflection_without_own_definition(self.page):
            self.root_page, self.root = self._root_page()
            self.root_ipa, self.root_pronunciation_url = self._get_pronunciation(
                self.root_page
            )
        else:
            self.root_page, self.root = self.page, word
            self.root_ipa, self.root_pronunciation_url = (
                self.ipa,
                self.pronunciation_url,
            )
        self.root_info = self._get_info(self.root_page)
        if not self.root_info.strip():
            raise_word_not_available(request, netloc="www.dwds.de")
    @classmethod
    def _only_relevant_part(cls, page: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        """Returns a page without information that could get in the way
        of your info extraction, like definitions in languages other
        than the language of interest.

        Args:
            page (bs4.BeautifulSoup): word page

        Returns:
            bs4.BeatifulSoup: trimmed version of page
        """
        return page

    @classmethod
    def _get_info(cls, page: bs4.BeautifulSoup) -> str:
        """Returns an iterator with every section of information about
        the word

        Args:
            page (bs4.BeautifulSoup): word page

        Returns:
            str: string with information about the word
        """
        pass

    @classmethod
    def _get_pronunciation(cls, page: bs4.BeautifulSoup) -> tuple:
        """Returns a tuple with the form (ipa, pronunciation_url)

        Args:
            tuple(str, str): for example, (ˈhʊndɐt, https://upload.wikimedia.org/wikipedia/commons/c/c0/De-hundert.ogg)
        """
        return ("", "")

    def _root_page(self) -> bs4.BeautifulSoup:
        """Returns the root page of self.word and the root word.
        For example, if you use de.wikipedia.org to get the definition
        of the word "großer", you will be directed to a page only with
        grammatical information. To actually understand the word, you
        would have to go to the "groß" page. That page has a useful
        definition. That "root word" ("groß" in this case) doesn't have
        to be the lemmatization of self.word. The word "beleidigt", for
        example, although an inflection of the word beleidigen, has an
        useful definition on de.wiktionary.org.

        Returns:
            (bs4.BeautifulSoup, str): (root page of self.word, root word)
        """
        pass

    def format_info(self, definitions, examples, show_phonetic_info=False):
        """Returns padronized word information

        Args:
            definitions (iterable): iterable with definitions
            examples (iterable): iterable with examples
            show_phonetic_info (bool, optional): self-describing. Defaults to False.
        """
        info = ""
        for definition in definitions:
            info += definition + "\n"
        info += "\n"
        for example in examples:
            info += example + "\n"
        definition_without_the_word = info.replace(self.root, "_")
        if show_phonetic_info:
            audio_section = (
                f"Phonetics: {self.root_ipa} {self.root_pronunciation_url}"
                if self.root_pronunciation_url
                else ""
            )
        else:
            audio_section = ""
        definition_without_the_word = (
            f"\n{self.root}\n{audio_section}\n{definition_without_the_word}"
        )
        return definition_without_the_word


class SecondaryWord(CompatibilityMixin):
    """Base class for other information-fetcher classes.
    Args:
        word (str): word that the object will represent.
        base_url (str): url of the site you gonna use.
    Relevant attributes:
        self.word = the same word you gave as input.
        self.page = parsed page from base_url + word.
        self.info = where all the relevant info is contained.
    """

    base_url = None

    def __init__(self, word, base_url):
        self.word = self.compatible(word) or word
        url = self.base_url + self.word
        request = SESSION.get(url, timeout=0.8)
        raise_word_not_available_404(request)
        self.page = bs4.BeautifulSoup(request.text, "html.parser")
        self.audio_url = self._get_audio_url()
        self.info = self._get_info()

    def _get_info(self):
        """Returns relevant information about self.word"""
        pass

    def _get_audio_url(self):
        """Returns audio url or False in case there is no audio
        url.

        Returns:
            str: audio url
        """
        return False


# GERMAN
class DudenWord(Word):
    base_url = DUDEN_URL

    @classmethod
    def compatible(cls, word: str):
        return (
            word.replace("ä", "ae")
            .replace("Ä", "Ae")
            .replace("ö", "oe")
            .replace("Ö", "Oe")
            .replace("ü", "ue")
            .replace("Ü", "Ue")
        )

    def _get_info(self, page: bs4.BeautifulSoup):
        word = page.find(class_="lemma__main").text
        definitions = []
        examples = []

        def setup_examples(bedeutung, index):
            example_title = bedeutung.find(
                class_="note__title", string=re.compile("Beispiel")
            )
            if example_title:
                example_tag = example_title.parent
            else:
                return
            example_iter = example_tag.find(class_="note__list").children
            example_iter = remove_navigable_strings(example_iter)
            for example in example_iter:
                examples.append(f"[{index}] {example.text.strip()}")

        if ugly_info := page.find(id="bedeutung"):
            definitions.append(f"[1] {ugly_info.p.text}")
            setup_examples(ugly_info, "1")
        else:
            ugly_info = page.find_all("li", id=re.compile("Bedeutung-"))
            for bedeutung in ugly_info:
                bedeutung_index = bedeutung["id"].split("-")[1]
                try:
                    definition = f"[{bedeutung_index}] {bedeutung.div.text.strip()}"
                except:
                    # some Duden definitions are just a figure, without any text
                    if figure := bedeutung.figure:
                        definition = f"[{bedeutung_index}] {figure.a['href']}"
                    else:
                        definition = ""
                definitions.append(definition)
                setup_examples(bedeutung, bedeutung_index)
        info = self.format_info(definitions, examples, show_phonetic_info=True)
        return info

    def _get_pronunciation(self, page: bs4.BeautifulSoup):
        guide_tag = page.find(class_="pronunciation-guide")
        useful_info_tags = guide_tag.find_all("dd")
        useful_info_tags = [tag.div.children for tag in useful_info_tags]
        phonetic_info = []
        pronunciation_url = ""
        for tag_iter in useful_info_tags:
            for tag in tag_iter:
                if "NavigableString" in str(tag.__class__):
                    continue
                try:
                    pronunciation_url = tag["href"]
                except (KeyError, TypeError):
                    phon = ""
                    if len(tag.contents) == 1:
                        phon += tag.contents[0].text
                    else:
                        for content in tag.contents:
                            if not content.name:
                                phon += content.text
                            else:
                                phon += f"\033[4m{content.text}\033[0m"
                    phonetic_info.append(phon)
        phonetic_info = " ".join(phonetic_info)
        return (phonetic_info, pronunciation_url)


class DWDSWord(Word):
    base_url = DWDS_URL

    def _get_info(self, page: bs4.BeautifulSoup):
        word = page.find("h1", class_="dwdswb-ft-lemmaansatz")
        if word:
            word = word.text
        else:
            # returning an empty string here raises an error later
            return ""
        main_definitions = page.find_all(id=re.compile("d-\d-\d"))
        definitions = []
        examples = []
        counter = Counter(["definition_number"])
        alphabet = "abcdefghijklmnopqrstuvwxyz"

        def append_definition_and_examples(definition: bs4.BeautifulSoup, preffix: str):
            result = ""
            sub = " " if len(preffix) > 1 else ""
            definition_number = counter["definition_number"]
            content = list(definition.children)[1]
            main_definition = content.find("div", class_="dwdswb-lesart-def")
            definitions.append(f"{sub}[{preffix}] {main_definition.text.strip()}")
            try:
                main_definition_examples = main_definition.next_sibling.children
            except AttributeError:
                return content
            for example in main_definition_examples:
                if example.name == "button":
                    continue
                elif "Beispiel" in example.text:
                    continue
                examples.append(f"[{preffix}] {example.text.strip()}")
            return content

        def is_sub_definition(tag: bs4.BeautifulSoup):
            return re.match(r"d-\d-\d-\d", tag["id"])

        for definition in main_definitions:
            if is_sub_definition(definition):
                continue
            definition_number = str(counter["definition_number"])
            content = append_definition_and_examples(definition, definition_number)
            sub_definitions = content.find_all(id=re.compile(r"d-\d-\d-\d"))
            for sub_definition in sub_definitions:
                sub_definition_letter = alphabet[counter["sub_definition_number"]]
                preffix = str(definition_number) + sub_definition_letter
                append_definition_and_examples(sub_definition, preffix)
                counter.update(["sub_definition_number"])
            try:
                counter.pop("sub_definition_number")
            except KeyError:
                pass
            counter.update(["definition_number"])
        info = self.format_info(definitions, examples, show_phonetic_info=True)
        return info

    @classmethod
    def _get_pronunciation(self, page: bs4.BeautifulSoup):
        try:
            audio_tag = page.find("audio")
            url = audio_tag.source["src"]
            ipa_tag = audio_tag.next_sibling.next_sibling
            try:
                ipa = ipa_tag.text.strip("[").strip("]")
            except:
                ipa = ""
            return (ipa, url)
        except (KeyError, AttributeError, TypeError):
            return (False, False)


class DEWiktionaryWord(Word):
    go_to_root = True
    base_url = WIKTIONARY_URL

    def _root_page(self, page: bs4.BeautifulSoup = False):
        if not page:
            page = self.page
        merkmale_title = page.find(title="Grammatische Merkmale")
        merkmale_siblings = remove_navigable_strings(merkmale_title.next_siblings)
        first_merkmal = merkmale_siblings[0]
        word = first_merkmal.text.split(" ")[-1]
        page_request = SESSION.get(WIKTIONARY_URL + word, timeout=0.8)
        page_request.raise_for_status()
        base_word_page = bs4.BeautifulSoup(page_request.text, "html.parser")
        is_inflection = self.is_inflection_without_own_definition(base_word_page)
        if is_inflection:
            return self._root_page(base_word_page)
        base_word_page = self._only_relevant_part(base_word_page)
        return (base_word_page, word)

    @classmethod
    def _get_pronunciation(cls, page):
        ipa = page.find(class_="ipa").text
        link_to_pronunciation = (
            "https:" + page.find(class_="aplay").next_sibling["href"]
        )
        return (ipa, link_to_pronunciation)

    @classmethod
    def _get_word(cls, wiktionary_page: bs4.BeautifulSoup):
        page_title = wiktionary_page.find(id=re.compile(r"_\(Deutsch\)"))
        return "_".join(page_title.text.split(" ")[:-1])

    @classmethod
    def _only_relevant_part(cls, wiktionary_page: bs4.BeautifulSoup):
        """Returns a BeautifulSoup object without any non-german definitions"""
        word = cls._get_word(wiktionary_page)
        deutsch_id = f"{word}_(Deutsch)"
        language_indicator = wiktionary_page.find(id=deutsch_id).parent
        below_language_indicator = remove_navigable_strings(
            language_indicator.next_siblings
        )
        only_de_page = bs4.BeautifulSoup(str(language_indicator), "html.parser")
        for sibling in below_language_indicator:
            try:
                if sibling.name == "h2":
                    non_de_id_at_the_end = sibling
                    non_de_children = list(non_de_id_at_the_end.children)
                    non_de_children.sort(  # puts an element like <span class="mw-headline" id="ja_(Esperanto)">...</span> at the top
                        key=lambda x: x.get("id", "bruh").startswith(f"{word}_(")
                    )
                    id_ = non_de_children[-1].get("id")
                    if id_.startswith(
                        f"{word}_("
                    ):  # only break if id_ is an actual non-german id
                        break
            except (KeyError, TypeError):
                pass
            only_de_page.append(sibling)
        return only_de_page

    @classmethod
    def is_inflection_without_own_definition(cls, wiktionary_page: bs4.BeautifulSoup):
        """Returns True when the word from wiktionary_page comes
        from another word and the wiktonary_page doesn't
        provide a definition"""
        return wiktionary_page.find(
            title="Grammatische Merkmale"
        ) and not wiktionary_page.find(title="Sinn und Bezeichnetes (Semantik)")

    @classmethod
    def _get_info(self, page: bs4.BeautifulSoup):
        info = ""
        all_definition_headers = iter(
            page.find_all(title="Sinn und Bezeichnetes (Semantik)")
        )
        all_example_headers = iter(page.find_all(title="Verwendungsbeispielsätze"))
        result = ""
        try:
            for definitions, examples in zip(
                all_definition_headers, all_example_headers
            ):
                definitions_ps = definitions.previous_siblings
                grammatical_information_header = next(
                    x for x in definitions_ps if x.name == "h3"
                )
                g_info_text = grammatical_information_header.text.replace(
                    "[Bearbeiten]", ""
                )
                info += g_info_text + "\n"
                for sibling in definitions.next_siblings:
                    if sibling.name == "dl":
                        info += "\n" + sibling.text
                        break
                for sibling in examples.next_siblings:
                    if sibling.name == "dl":
                        info += "\n" * 2 + sibling.text
                        break
                result += info + "\n"
                info = ""
        except StopIteration:
            pass
        return result

    def get_inflections(self):
        all_inflection_tables = self.root_page.find_all(
            class_=re.compile("inflection-table")
        )
        all_inflection_tables.reverse()  # because g_info is reversed
        result = set()
        for inflection_table in all_inflection_tables:
            g_info_current = inflection_table.previous_sibling.text
            if "Nachname" in g_info_current:
                word = self.root
                result = result.union([word])
            elif "Verb" in g_info_current:
                inflection_cells = inflection_table.find_all("td", colspan=3)
                for inflection_cell in inflection_cells:
                    inflection_text = inflection_cell.text.strip().split("!")
                    result = result.union(inflection_text)
            elif "Substantiv" in g_info_current:
                inflection_cells = inflection_table.find_all("td")
                for inflection_cell in inflection_cells:
                    inflection_text = []
                    try:
                        inflection_cell.find("br").replace_with(" ")
                    except AttributeError:
                        pass
                    inflection_split = inflection_cell.text.strip().split(" ")
                    gender_word_pairs = zip(
                        inflection_split[::2], inflection_split[1::2]
                    )
                    for gender, word in gender_word_pairs:
                        inflection_text.append(word)
                    result = result.union(inflection_text)
            elif "Adjektiv" in g_info_current:
                inflection_cells = inflection_table.find_all("td")
                for inflection_cell in inflection_cells:
                    result = result.union(
                        [inflection_cell.text.strip().replace("am", "")]
                    )
        try:
            result.remove("")
        except KeyError:
            pass
        return tuple(result)


# ENGLISH

DICTIONARY_URL = "https://www.dictionary.com/browse/"
TEMPORARY_DIR = tempfile.TemporaryDirectory()
TEMPORARY_DIR_PATH = pathlib.Path(TEMPORARY_DIR.name)


class ENDictionaryWord(Word):
    base_url = DICTIONARY_URL

    def _get_pronunciation(self, page: bs4.BeautifulSoup):
        pronunciation_tag = page.find(class_=re.compile("LgvbRZvyfgILDYMd8Lq6"))
        ipa = pronunciation_tag.text.strip("[").strip("]")
        path_to_pronunciation = str(TEMPORARY_DIR_PATH / f"{self.word}.wav")
        pronunciation = gtts.gTTS(self.word, tld="us")
        with open(path_to_pronunciation, "w+b") as file:
            pronunciation.write_to_fp(file)
        return (ipa, f"file://{path_to_pronunciation}")

    def _get_info(self, page: bs4.BeautifulSoup) -> iter:
        definition_blocks = page.find_all(attrs={"data-type": "word-definitions"})

        definitions_text = f"{self.word}\n"
        for block in definition_blocks:
            try:
                block_grammar = block.find(class_="OoNk445te7MEusWxZIjw").text
            except AttributeError:
                continue
            definitions = block.find_all(class_="ESah86zaufmd2_YPdZtq")
            definitions_text += "\n" + block_grammar + "\n"
            for definition in definitions:
                definitions_text += definition.text + "\n"

        examples = page.find_all(class_="VvALg_9aE120lhieur0R")
        examples_text = ""
        for example in examples:
            examples_text += example.p.text + "\n"
        content = f"{definitions_text}\n\nEXAMPLES\n{examples_text}"
        return content


# Portuguese

DICIO_URL = "https://dicio-api-ten.vercel.app/v2/"


class BRDicioWord(Word):
    base_url = DICIO_URL
    api = True
    go_to_root = False

    def _get_info(self, page):
        result = ""
        try:
            if "error" in page.keys():
                netloc = urllib.parse.urlparse(DICIO_URL).netloc
                raise WordNotAvailable(f"Word not available at {netloc}")
        except AttributeError:
            pass
        for info in page:
            result += info["partOfSpeech"].upper() + "\n"
            for meaning in info["meanings"]:
                result += meaning + "\n"
            result += "\n"
        return result

# Latin

LAWIKTIONARY_URL = "https://en.wiktionary.org/wiki/"
class LAWiktionaryWord(Word):
    base_url = LAWIKTIONARY_URL
    api = False
    go_to_root = False
    options = "?action=raw"
    def _get_info(self, page:bs4.BeautifulSoup):
        return page.text
    @classmethod
    def _only_relevant_part(cls, page: bs4.BeautifulSoup):
        text = page.text + "==Language==\n"
        isolate_latin_pattern = re.compile(r'==Latin==(.+?)==[^=]+==\n', re.DOTALL)
        isolated_latin: re.Match = re.search(isolate_latin_pattern, text)
        result = isolated_latin.groups()[0]
        return bs4.BeautifulSoup(result, 'html.parser')
        
