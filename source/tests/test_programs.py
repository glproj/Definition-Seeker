import io, sys, pathlib
from logging import log
from unittest import TestCase, main

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from programs import *
from ipdb import set_trace as s


class ProgramTestCase(TestCase):
    def setUp(self):
        self.test_in = io.StringIO()
        self.test_out = io.StringIO()
        self.cmd = TestProgram(stdout=self.test_out, stdin=self.test_in)
        self.cmd.preloop()

    def test_basic(self):
        self.inp("Haus")
        self.assertIn("Haus", self.output)
        self.assertIn("[1]", self.output)

    def test_examples(self):
        self.inp("examples oder")
        self.assertIn("oder", self.output)
        ebook_names = self.cmd.ebook_lang_name_txt["de"]
        ebook_names = [
            (name, txt)
            for book_name_txt in ebook_names
            for name, txt in book_name_txt.items()
        ]
        for ebook_name, _ in ebook_names:
            self.assertIn(ebook_name.upper(), self.output)

    def test_other_sources(self):
        with self.subTest("en"):
            self.inp("lang en")
            self.inp("ball")
            self.test_out.truncate(0)
            self.test_out.seek(0)
            self.inp("dict")
            self.assertIn("noun", self.output)
        with self.subTest("de"):
            self.inp("lang de")
            self.inp("Ball")
            self.test_out.truncate(0)
            self.test_out.seek(0)
            self.inp("dwds")
            self.assertNotIn("noun", self.output)
            self.assertIn("kugelförmiges", self.output)
    def test_other_sources_wrong_language(self):
        self.inp("lang de")
        self.inp("Huhn")
        self.inp("dict")
        self.assertIn("Change your language", self.output)


    def inp(self, text: str):
        """write in self.test_in and run a cmdloop in self.cmd

        Args:
            text (str): input
        """
        line = self.cmd.precmd(text)
        stop = self.cmd.onecmd(line)
        stop = self.cmd.postcmd(stop, line)

    @property
    def output(self):
        return self.test_out.getvalue()


if __name__ == "__main__":
    main()
