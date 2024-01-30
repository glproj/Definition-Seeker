import requests, bs4, re, pathlib, urllib, json, gtts, tempfile, unidecode
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
    options = ""

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
        if self.go_to_root and self._is_inflection_without_own_definition(self.page):
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
            raise_word_not_available(request)

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
        """Returns a string with information about the word

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

    def _is_inflection_without_own_definition(cls, page: bs4.BeautifulSoup) -> bool:
        """Returns True when the word from wiktionary_page comes
        from another word and the wiktonary_page doesn't
        provide a definition for it."""
        return

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
        return (bs4.BeautifulSoup("", "html.parser"), "")
    @classmethod
    def _get_word(cls, page):
        return ""
    def format_info(
        self, definitions, examples, show_phonetic_info=False, show_root=True
    ):
        """Returns padronized word information

        Args:
            definitions (iterable): iterable with definitions
            examples (iterable): iterable with examples
            show_phonetic_info (bool, optional): self-describing. Defaults to False.
        """
        info = "\n".join(definitions)
        if len(examples) > 0:
            info += f"\n\nEXAMPLES:\n"
        info += "\n".join(examples)
        info = info.replace(self.root, "_")
        if show_phonetic_info:
            audio_section = (
                f"Phonetics: {self.root_ipa} {self.root_pronunciation_url}"
                if self.root_pronunciation_url
                else ""
            )
        else:
            audio_section = ""
        info = f"{self.root if show_root else ''}\n{audio_section}\n{info}"
        return info

    @classmethod
    def isolate_lang(cls, wiktionary_page, lang_id):
        """Isolate specific language in a wiktionary page.

        Args:
            wiktionary_page: page to narrow;
            lang_id: id of the span element that marks different languages."""
        try:
            # usually, the element with id {lang_id} will be a
            # span inside an h2 tag. We want that h2 tag.
            language_indicator = wiktionary_page.find(id=lang_id).parent
        except AttributeError:
            raise WordNotAvailable("Word not found. Maybe you missed the language?")
        below_language_indicator = remove_navigable_strings(
            language_indicator.next_siblings
        )
        isolated_page = bs4.BeautifulSoup(str(language_indicator), "html.parser")
        for sibling in below_language_indicator:
            isolated_page.append(sibling)
            if sibling.name == "h2":
                break
        return isolated_page


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
        is_inflection = self._is_inflection_without_own_definition(base_word_page)
        if is_inflection:
            return self._root_page(base_word_page)
        base_word_page = self._only_relevant_part(base_word_page)
        return (base_word_page, word)

    @classmethod
    def _get_pronunciation(cls, page):
        ipa = ""
        try:
            ipa = page.find(class_="ipa").text
        except:
            pass
        link_to_pronunciation = ""
        try:
            link_to_pronunciation = (
                "https:" + page.find(class_="aplay").next_sibling["href"]
            )
        except:
            pass
        ipa = ipa.strip().strip("[").strip("]")
        return (ipa, link_to_pronunciation)

    @classmethod
    def _get_word(cls, wiktionary_page: bs4.BeautifulSoup):
        page_title = wiktionary_page.find(class_="mw-page-title-main").text
        return page_title

    @classmethod
    def _only_relevant_part(cls, wiktionary_page: bs4.BeautifulSoup):
        """Returns a BeautifulSoup object without any non-german definitions"""
        word = cls._get_word(wiktionary_page)
        deutsch_id = f"{word}_(Deutsch)"
        only_de_page = cls.isolate_lang(wiktionary_page, deutsch_id)
        return only_de_page

    @classmethod
    def _is_inflection_without_own_definition(cls, wiktionary_page: bs4.BeautifulSoup):
        """Returns True when the word from wiktionary_page comes
        from another word and the wiktonary_page doesn't
        provide a definition for it."""
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
ENWIKTIONARY_URL = "https://en.wiktionary.org/wiki/"
TEMPORARY_DIR = tempfile.TemporaryDirectory()
TEMPORARY_DIR_PATH = pathlib.Path(TEMPORARY_DIR.name)


class ENWiktionaryWord(Word):
    base_url = ENWIKTIONARY_URL

    @classmethod
    def _get_info(cls, page) -> str:
        # TODO
        return "a"

    @classmethod
    def _get_pronunciation(cls, page) -> tuple:
        ipa_tag = page.find(class_="IPA")
        ipa = "N/A"
        if ipa_tag:
            ipa = ipa_tag.text
        source_audio_tag = page.find("source")
        link_to_audio = ""
        if source_audio_tag:
            link_to_audio = "https:" + source_audio_tag["src"]
        return (ipa, link_to_audio)

    @classmethod
    def _only_relevant_part(cls, wiktionary_page: bs4.BeautifulSoup):
        """Returns a BeautifulSoup object without any non-english definitions"""
        en_id = "English"
        only_en_page = cls.isolate_lang(wiktionary_page, en_id)
        return only_en_page


class ENDictionaryWord(Word):
    base_url = DICTIONARY_URL

    def _get_pronunciation(self, page: bs4.BeautifulSoup):
        pronunciation_tag = page.find(class_=re.compile("LgvbRZvyfgILDYMd8Lq6"))
        ipa = ""
        try:
            ipa = pronunciation_tag.text.strip("[").strip("]")
        except AttributeError:
            pass
        path_to_pronunciation = str(TEMPORARY_DIR_PATH / f"{self.word}.wav")
        pronunciation = gtts.gTTS(self.word, tld="us")
        with open(path_to_pronunciation, "w+b") as file:
            pronunciation.write_to_fp(file)
        wik = ENWiktionaryWord(self.word)
        return (wik.ipa, wik.pronunciation_url or f"file://{path_to_pronunciation}")

    def _get_info(self, page: bs4.BeautifulSoup):
        definition_blocks = page.find_all(attrs={"data-type": "word-definitions"})
        if not definition_blocks:
            return ""
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

DICIO_URL = "https://www.dicio.com.br/"


class BRDicioWord(Word):
    base_url = DICIO_URL
    api = False
    go_to_root = False
    def compatible(self, word):
        return unidecode.unidecode(word)
        
    def _get_info(self, page: bs4.BeautifulSoup):
        meaning = page.find("p", class_="significado").children
        result = ""
        for span in meaning:
            if getattr(span, "class", False) == "cl":
                result += "\n" * 2 + span.text + "\n" * 2
                break
            result += span.text + "\n"
        return result


# Latin

LAWIKTIONARY_URL = "https://en.wiktionary.org/wiki/"


class LAWiktionaryWord(Word):
    base_url = LAWIKTIONARY_URL
    api = False
    go_to_root = False

    @classmethod
    def _get_word(cls, page: bs4.BeautifulSoup):
        return page.find("strong", {"class": "Latn headword"}).text

    def _get_info(self, page: bs4.BeautifulSoup):
        head_words = page.find_all("strong", {"class": "Latn headword"})
        info = ""
        for head_word in head_words:
            definitions = []
            examples = []
            grammar = head_word.find_previous("h4").text.upper().replace("[EDIT]", "")
            if not (grammar in info):
                definitions.append(grammar)
            # prevents repeating information
            title_definition = head_word.find_parent("p").text.strip()
            definitions.append(title_definition)
            definition_list = head_word.find_next("ol")
            if definition_list.find("dl"):
                examples.append(title_definition)
            for id, li in enumerate(remove_navigable_strings(definition_list.children)):
                examples_tags = li.find_all("span", {"class": "h-usage-example"})
                try:
                    corresponding_definition_tags = reversed(
                        remove_navigable_strings(
                            # the definition is right above the list of examples
                            li.find("dl").previous_siblings
                        )
                    )
                except AttributeError:
                    # no examples implies that the li contains only the definition
                    corresponding_definition_tags = li
                corresponding_definition = " ".join(
                    list(
                        map(
                            lambda el: el.text,
                            # reverse it to get the order right
                            corresponding_definition_tags,
                        )
                    )
                )
                definitions.append(f"[{id+1}] {corresponding_definition}")
                if examples_tags:
                    for example in examples_tags:
                        examples.append(f"[{id+1}] {example.text}")
            info += self.format_info(definitions, examples, True, False) + "\n"
        info = info.replace(self._get_word(page), "_")
        return info

    @classmethod
    def _only_relevant_part(cls, page: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        latin_id = "Latin"
        only_la_page = cls.isolate_lang(page, latin_id)
        return only_la_page

    @classmethod
    def _get_pronunciation(cls, page: bs4.BeautifulSoup) -> tuple:
        ecclesiastical_pron_li = page.select_one(
            'li:-soup-contains("modern Italianate Ecclesiastical")'
        )
        ecclesiastical_ipa = ecclesiastical_pron_li.find("span", {"class": "IPA"}).text
        return (ecclesiastical_ipa, "")


# French

FRWIKTIONARY_URL = "https://fr.wiktionary.org/wiki/"


class FRWitionaryWord(Word):
    base_url = FRWIKTIONARY_URL
    api = False
    go_to_root = True

    @classmethod
    def _get_word(cls, page: bs4.BeautifulSoup):
        page_title = page.find(class_="mw-page-title-main")
        return page_title.text

    @classmethod
    def _only_relevant_part(cls, wiktionary_page: bs4.BeautifulSoup):
        """Returns a BeautifulSoup object without any non-french definitions"""
        french_id = "Français"
        only_fr_page = cls.isolate_lang(wiktionary_page, french_id)
        only_definitions_page = bs4.BeautifulSoup("", "html.parser")

        definition_titles = [
            element
            for element in only_fr_page.find_all("h3")
            if element.find(class_="titredef") or element.find(class_="titrepron")
        ]
        for definition_title in definition_titles:
            siblings = list(definition_title.next_siblings)
            only_definitions_page.append(definition_title)
            for sibling in siblings:
                if sibling.name == "h3":
                    break
                only_definitions_page.append(sibling)
        return only_definitions_page

    @classmethod
    def _get_info(cls, page: bs4.BeautifulSoup):
        definitions_and_examples = page.select("ol:not(.references)")
        info = ""
        # each li in the ols above contains a definition along
        # with a set of usage examples.
        for ol in definitions_and_examples:
            gr_info_list = [
                gr_info for gr_info in ol.previous_siblings if gr_info.name == "h3"
            ]

            grammatical_info = "NO GRAMMATICAL INFORMATION"
            if len(gr_info_list) == 0:
                continue
            grammatical_info = gr_info_list[0].text
            more_grammatical_info = ol.previous_sibling.text
            # remove already known IPA transcription:
            # The french word chat can be pronounced as \ʃa\ or \tʃat\.
            # The more common pronunciation is the first of the two, and it is
            # already going to be included in the output anyway, so we don't need
            # to include it together with every function of the word that uses this
            # pronunciation. We are only going to include the IPA transcription in
            # more_grammatical_info if its IPA transcription contains something different.
            more_grammatical_info = more_grammatical_info.replace(
                cls._get_pronunciation(page)[0], ""
            )
            word = more_grammatical_info.split(" ")[0]
            more_grammatical_info = more_grammatical_info.replace(word, "")
            info += "\n\n" + (
                grammatical_info.upper().replace("[MODIFIER LE WIKICODE]", "").strip()
                + "\n"
                + more_grammatical_info.strip()
                + "\n"
            )
            definitions = ""
            examples = ""
            for index, def_tag in enumerate(remove_navigable_strings(ol)):
                definition_number = f"[{index+1}]"
                example_list = def_tag.find("ul")
                examples_li = []
                if example_list:
                    examples_li = [
                        definition_number + example_tag.text
                        for example_tag in remove_navigable_strings(
                            example_list.children
                        )
                    ]
                only_definition_tags = [tag for tag in def_tag if tag.name != "ul"]
                examples_text = "\n".join(examples_li)
                definition = definition_number
                definition += "".join(
                    [
                        definition_part.text
                        for definition_part in only_definition_tags
                        # the example list is the last thing that appears in def_set,
                        # so we just need to get the text of all its previous siblings
                        # to get the corresponding definition. But before getting the definition
                        # we have to reverse the siblings list, since the elements we get from the previous_siblings
                        # property are in a reversed order.
                    ]
                )
                definitions += definition.strip() + "\n"
                if examples_text:
                    examples += examples_text.strip() + "\n"
            info += "\n" + definitions + "\n\n" + examples
        return info

    def get_inflections(self):
        return self.root

    # TODO: redirect to root only when user wants it.
    @classmethod
    def _get_pronunciation(cls, page: bs4.BeautifulSoup) -> tuple:
        first_definition_set = page.select("ol:not(.references)")[0]
        ipa = first_definition_set.previous_sibling.find(class_="API").text
        audio_tags = page.find_all("span", {"class": "audio-pronunciation"})
        fr_audio_tags = filter(lambda el: "France" in el.text, audio_tags)
        fr_audio_links = map(lambda fr_el: fr_el.find("source")["src"], fr_audio_tags)
        # TODO: get the user to chose from the list of audios (maybe adding the region)
        link = list(fr_audio_links)[0]
        return (ipa, "http:" + link)

    def _root_page(self) -> bs4.BeautifulSoup:
        definitions_and_examples = self.page.select("ol:not(.references)")
        redirect_link = definitions_and_examples[0].find("a")
        # redirect_link.get("href") will be something like /wiki/femme
        redirect_word = redirect_link.get("href").split("/")[-1]
        page_request = SESSION.get(FRWIKTIONARY_URL + redirect_word, timeout=0.8)
        page_request.raise_for_status()
        base_word_page = bs4.BeautifulSoup(page_request.text, "html.parser")
        is_inflection = self._is_inflection_without_own_definition(base_word_page)
        if is_inflection:
            return self._root_page(base_word_page)
        base_word_page = self._only_relevant_part(base_word_page)
        return (base_word_page, redirect_word)

    @classmethod
    def _is_inflection_without_own_definition(cls, page: bs4.BeautifulSoup) -> bool:
        definitions_and_examples = page.select("ol:not(.references)")
        if len(definitions_and_examples) > 1:
            return False

        for ol in definitions_and_examples:
            gr_info_list = [
                gr_info for gr_info in ol.previous_siblings if gr_info.name == "h3"
            ]
            return gr_info_list[0].text.startswith("Forme d")


# Russian (English)
ENRUWIKTIONARYURL = "https://en.wiktionary.org/w/index.php?title="


class ENRUWiktionaryWord(Word):
    base_url = ENRUWIKTIONARYURL

    @classmethod
    def _only_relevant_part(cls, page: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        russian_id = "Russian"
        only_ru_page = cls.isolate_lang(page, russian_id)
        return only_ru_page

    @classmethod
    def _get_info(cls, page: bs4.BeautifulSoup) -> str:
        return "adfdsafad fsdafd"

    @classmethod
    def _get_pronunciation(cls, page: bs4.BeautifulSoup) -> tuple:
        ipa = ""
        try:
            ipa = page.find(class_="IPA").text
        except:
            pass
        link_to_pronunciation = ""
        try:
            link_to_pronunciation = (
                "https:" + page.find(class_="aplay").next_sibling["href"]
            )
        except:
            pass
        ipa = ipa.strip().strip("[").strip("]")
        return (ipa, link_to_pronunciation)
