import io, sys, pathlib
from unittest import TestCase, main

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from programs import *
import word_info_extractor
from ipdb import set_trace as s


class ProgramTestCase(TestCase):
    def setUp(self):
        self.test_in = io.StringIO()
        self.test_out = io.StringIO()
        self.cmd = TestProgram(stdout=self.test_out, stdin=self.test_in)
        self.cmd.word_class = word_info_extractor.DEWiktionaryWord

    def test_basic(self):
        self.inp("Haus")
        self.assertIn("Haus", self.output)
        self.assertIn("[1]", self.output)

    def test_examples(self):
        self.inp("examples oder")
        self.assertIn("Ball", self.output)
        ebook_names = self.cmd.ebook_lang_name_txt["de"]
        ebook_names = [
            (name, txt)
            for book_name_txt in ebook_names
            for name, txt in book_name_txt.items()
        ]
        for ebook_name, _ in ebook_names:
            self.assertIn(ebook_name.upper(), self.output)
    

    def inp(self, text: str):
        """write in self.test_in and run a cmdloop in self.cmd

        Args:
            text (str): input
        """
        self.test_in.write(text)
        self.cmd.cmdloop()

    @property
    def output(self):
        return self.test_out.getvalue()


if __name__ == "__main__":
    main()
