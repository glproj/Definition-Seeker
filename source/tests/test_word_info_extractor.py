import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from unittest import TestCase, main
from word_info_extractor import *

# wmb = without multiple Bedeutung sections
# bf = already in the base form
# mrw = multiple redirects until base form is reached
# ! = not
WORDS = (
    "ging",  # verb wmb/!bf
    "lästern",  # verb wmb/bf
    "Stuhl",  # noun wmb/bf
    "durchschneiden",  # verb !wmb/bf
    "gesucht",  # not a base form but has its own definition in wikipedia
    "verfahren",  # Verb and Adjektiv at the same time
    "Junge",  # weird table compared to other nouns. It's also a surname
    "ja",  # present in multiple languages
)


class BaseTestCases:
    class BaseTestCase(TestCase):
        @classmethod
        def setUpClass(cls):
            word_to_instance_dict = {}
            for word in WORDS:
                try:
                    instance = cls.class_(word)
                except WordNotAvailable:
                    print(
                        f"{cls.class_.__name__} returned error with argument '{word}'"
                    )
                word_to_instance_dict.update({word: instance})
            cls.word_to_instance_dict = word_to_instance_dict
            cls.t_class = DEWiktionaryWord

        def test_get_info(self):
            words = ["Stuhl"]
            for word in words:
                with self.subTest(word):
                    result = self.word_to_instance_dict[word].root_info
                    self.assertIn("[1]", result)


class WiktionaryTestCase(BaseTestCases.BaseTestCase, TestCase):
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

    def test_get_pronunciation(self):
        pronunciation_url = self.word_to_instance_dict["Stuhl"].pronunciation_url
        ipa = self.word_to_instance_dict["Stuhl"].root_ipa
        self.assertEqual(
            f"{ipa} {pronunciation_url}",
            "ʃtuːl https://upload.wikimedia.org/wikipedia/commons/3/38/De-Stuhl.ogg",
        )

    def test_get_info_wiktionary(self):
        pass

    def test_only_de(self):
        ja_page = self.word_to_instance_dict["ja"].root_page
        self.assertTrue(ja_page.find(href="/wiki/Wiktionary:Deutsch"))
        self.assertFalse(ja_page.find(href="/wiki/Wiktionary:Schwedisch"))
        self.assertFalse(ja_page.find(href="/wiki/Wiktionary:F%C3%A4r%C3%B6isch"))


class DWDSTestCase(BaseTestCases.BaseTestCase, TestCase):
    class_ = DWDSWord

    def test_get_info_dwds(self):
        page = self.word_to_instance_dict["Stuhl"].root_info
        self.assertIn("bildlich", page)
        self.assertIn("https://media.dwds.de/dwds2/audio/004/der_Stuhl.mp3", page)
        self.assertIn("Stuhl", page)


class DudenTestCase(BaseTestCases.BaseTestCase, TestCase):
    class_ = DudenWord


if __name__ == "__main__":
    main()
