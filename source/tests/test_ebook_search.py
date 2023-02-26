import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from unittest import TestCase, main
from ebook_search import *


class EbookSearchTestCase(TestCase):
    def setUp(self):
        self.text = """Und wenn er zu Mittage schläft,
Sich nicht das Blatt am Zweige regt;
Gesunder Pflanzen Balsamduft
Erfüllt die schweigsam stille Luft;
Die Nymphe darf nicht munter sein,
Und wo sie stand, da schläft sie ein."""
    def test_get_examples(self):
        with self.subTest("not separable"):
            result = get_examples("Luft", self.text)
            self.assertEqual(len(result), 1)
        with self.subTest("separable"):
            result = get_examples("schläft ein", self.text)
            self.assertEqual(len(result), 1)
        with self.subTest("case sensitivity"):
            result = get_examples("und", self.text)
            self.assertEqual(len(result), 1)

if __name__ == "__main__":
    main()
