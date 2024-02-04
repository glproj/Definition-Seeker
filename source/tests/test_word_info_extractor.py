import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from unittest import TestCase, main
from word_info_extractor import *


class BaseTestCases:
    class BaseTestCase(TestCase):
        words = []
        # {communio: ["/komˈmuː.ni.oː/", "http://url/to/audio"]}, for example
        # communio should be in words
        ipa_dict = {}

        @classmethod
        def setUpClass(cls):
            word_to_instance_dict = {}
            for word in cls.words:
                instance = cls.class_(word)
                word_to_instance_dict.update({word: instance})
            cls.frst = word_to_instance_dict[cls.words[0]]
            cls.word_to_instance_dict = word_to_instance_dict
            cls.t_class = DEWiktionaryWord

        def test_get_info(self):
            for word in self.words:
                with self.subTest(word):
                    result = self.word_to_instance_dict[word].root_info
                    self.assertIsNot("", result)

        def test_get_pronunciation(self):
            for word, phonetics in self.ipa_dict.items():
                inst = self.word_to_instance_dict[word]
                self.assertIn(phonetics[0], inst.root_ipa)
                self.assertIn(phonetics[1], inst.pronunciation_url)

        def test_error(self):
            with self.assertRaises(WordNotAvailable):
                self.class_("fjdkslafjdsklfjldsçfjksdalfjfjkdslaçfjdskla")


class WiktionaryTestCase(BaseTestCases.BaseTestCase):
    # wmb = without multiple Bedeutung sections
    # bf = already in the base form
    # mrw = multiple redirects until base form is reached
    # ! = not
    words = (
        "ging",  # verb wmb/!bf
        "lästern",  # verb wmb/bf
        "Stuhl",  # noun wmb/bf
        "durchschneiden",  # verb !wmb/bf
        "gesucht",  # not a base form but has its own definition in wikipedia
        "verfahren",  # Verb and Adjektiv at the same time
        "Junge",  # weird table compared to other nouns. It's also a surname
        "ja",  # present in multiple languages
    )
    ipa_dict = {
        "Stuhl": [
            "ʃtuːl",
            "De-Stuhl.ogg",
        ]
    }
    class_ = DEWiktionaryWord

    def test_is_inflection_without_own_definition(self):
        with self.subTest("ging"):
            self.assertTrue(
                self.t_class._is_inflection_without_own_definition(
                    self.word_to_instance_dict["ging"].page
                )
            )
        with self.subTest("gesucht"):
            self.assertFalse(
                self.t_class._is_inflection_without_own_definition(
                    self.word_to_instance_dict["gesucht"].page
                )
            )
        with self.subTest("Stuhl"):
            self.assertFalse(
                self.t_class._is_inflection_without_own_definition(
                    self.word_to_instance_dict["Stuhl"].page
                )
            )

    def test_root_page(self):
        root_page = self.word_to_instance_dict["ging"].root_page
        self.assertTrue(root_page.find(title="Sinn und Bezeichnetes (Semantik)"))

    def test_root(self):
        root = self.word_to_instance_dict["ging"].root
        self.assertEqual(root, "gehen")

    def test_unavailable_word(self):
        with self.assertRaises(WordNotAvailable):
            DEWiktionaryWord("bruh123")

    def test_get_info_wiktionary(self):
        pass

    def test_only_de(self):
        ja_page = self.word_to_instance_dict["ja"].root_page
        self.assertTrue(ja_page.find(href="/wiki/Wiktionary:Deutsch"))
        self.assertFalse(ja_page.find(href="/wiki/Wiktionary:Schwedisch"))
        self.assertFalse(ja_page.find(href="/wiki/Wiktionary:F%C3%A4r%C3%B6isch"))


class DWDSTestCase(BaseTestCases.BaseTestCase):
    words = (
        "ging",  # verb wmb/!bf
        "lästern",  # verb wmb/bf
        "Stuhl",  # noun wmb/bf
        "durchschneiden",  # verb !wmb/bf
        "gesucht",  # not a base form but has its own definition in wikipedia
        "verfahren",  # Verb and Adjektiv at the same time
        "Junge",  # weird table compared to other nouns. It's also a surname
        "ja",  # present in multiple languages
    )
    class_ = DWDSWord

    ipa_dict = {
        "Junge": [
            "ˈjʊŋə",
            "der_Junge.mp3",
        ]
    }

    def test_get_info_dwds(self):
        page = self.word_to_instance_dict["Stuhl"].root_info
        self.assertIn("bildlich", page)
        self.assertIn("der_Stuhl.mp3", page)
        self.assertIn("Stuhl", page)


class DudenTestCase(BaseTestCases.BaseTestCase):
    words = (
        "lästern",  # verb wmb/bf
        "Stuhl",  # noun wmb/bf
        "gesucht",  # not a base form but has its own definition in wikipedia
        "Junge",  # weird table compared to other nouns. It's also a surname
        "ja",  # present in multiple languages
    )
    ipa_dict = {
        "Stuhl": [
            "St",
            "https://cdn.duden.de/_media_/audio/",
        ]
    }
    class_ = DudenWord


class BRDicioWordTestCase(BaseTestCases.BaseTestCase):
    words = ("bola", "mamão", "paralelepípedo", "meio-dia")
    class_ = BRDicioWord


class ENDictionaryTestCase(BaseTestCases.BaseTestCase):
    words = ("scant", "one-way")
    class_ = ENDictionaryWord


class WiktionaryTestCases:
    class WiktionaryTestCase(BaseTestCases.BaseTestCase):
        def test_no_key(self):
            inst = self.frst
            self.assertNotIn("(key)", inst.root_ipa)


class ENWiktionaryTestCase(WiktionaryTestCases.WiktionaryTestCase):
    words = ["house"]
    ipa_dict = {"house": ["haʊs", "En-us-house-noun.ogg"]}
    class_ = ENWiktionaryWord

    def test_examples(self):
        self.assertIn("[2] This is my house and my family's ancestral home", self.frst.root_info)


class ENRUWiktionaryTestCase(WiktionaryTestCases.WiktionaryTestCase):
    words = ("твое", "твой", "Санкт-Петербург")
    ipa_dict = {
        "Санкт-Петербург": [
            "ˌsankt pʲɪtʲɪrˈburk",
            "Ru-%D0%A1%D0%B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%80%D0%B1%D1%83%D1%80%D0%B3.ogg",
        ]
    }
    class_ = ENRUWiktionaryWord

    def test_no_IPA(self):
        inst = self.frst
        self.assertNotIn("IPA:", inst.root_ipa)


class FRWitionaryTestCase(BaseTestCases.BaseTestCase):
    words = ("milieu", "cigale", "été", "de_nouveau")
    ipa_dict = {"de_nouveau": ["də nu.vo", "Fr-de_nouveau.ogg"]}
    class_ = FRWiktionaryWord


class LAWiktionaryTestCase(WiktionaryTestCases.WiktionaryTestCase):
    words = ("cum", "communio", "homo")
    ipa_dict = {"communio": ["/komˈmuː.ni.oː/", ""]}
    class_ = LAWiktionaryWord

    def test_h3_as_grammar(self):
        # the "homo" page has the word Noun written in a h3.
        # other pages have it written in an h4.
        self.assertIn("NOUN", self.word_to_instance_dict["homo"].root_info)


if __name__ == "__main__":
    main()
