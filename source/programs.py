import termcolor, ebook_search
from word_info_extractor import *
import pyperclip
VALID_LANGUAGE_CODES = ["en", "de"]
class Program:
    def __init__(self, word_class, args={}, language=""):
        self.ebooks_txt(language)
        self.run(word_class, args=args)

    def run(self, word_class, args={}):
        if vars(self).get("return_to_loop"):
            return
        elif not vars(self).get("previous_word"):
            self.previous_word = ""
        input_ = (
            args.get("word", False)
            or str(input(termcolor.colored("Word: ", "red"))).strip()
        )
        input_list = input_.split(" ")
        input_list_wo_modifiers = word_str, *arguments = [
            x for x in input_list if not x.startswith("--")
        ]
        modifiers = [x for x in input_list if x.startswith("--")]
        try:
            if self._run_option(word_str, *arguments):
                return self.run(word_class, args=args)
            phrase = "_".join(input_list_wo_modifiers)
            term = phrase if ("--p" in modifiers) else word_str
            word = word_class(term)
            self.previous_word = word
        except WordNotAvailable as e:
            print(e)
            return self.run(word_class, args=args)
        if not word.root == word.word:
            print(f"Redirecting to {word.root}\n")
        print(f"IPA: {word.ipa}\n")
        if word.go_to_root:
            print(f"root IPA: {word.root_ipa}\n")
        pyperclip.copy(f"{word.root_ipa} {word.root_pronunciation_url}")
        print(word.root_info)
        if source := args.get("source"):
            if self._run_option(source):
                return
        if args.get("word"):
            return
        return self.run(word_class, args=args)

    def _run_option(self, command, *args):
        try:
            option = getattr(self, command)
        except AttributeError:
            return False
        option(*args)
        return True

    def get_previous_word(self):
        return vars(self).get("previous_word", "")

    def q(self):
        sys.exit(0)

    def lang(self, lang=""):
        """Changes the language of the running program.

        Args:
            lang (str, optional): language code. Defaults to ''.
        """
        if (lang not in VALID_LANGUAGE_CODES) or not lang.strip():
            print(f"The language code should be one of the following: {str_valid_lc}")
            return
        CONFIG_PARSER["DEFAULT"]["Language"] = lang
        with open(CONFIG_PATH, "w") as file:
            CONFIG_PARSER.write(file)
        self.return_to_loop = True

    def images(self, *args):
        if IMAGE_EXTRACTION:
            key_word = " ".join(args) or self.previous_word
            get_images_from_word(key_word)
        else:
            print("Your configuration file doesn't have GOOGLE_API")
    def examples(self, *args):
        word = " ".join(args) or self.previous_word
        if args:
            inflections = tuple([word])
        else:
            inflections = word.get_inflections(self.previous_word.root_page)
        for book_txt in self.ebook_list:
            examples = ebook_search.get_examples(inflections, book_txt)
            for example in examples:
                print(example + "\n")

    def _get(self, attr: str, default):
        try:
            return getattr(self, attr)
        except AttributeError:
            return default

    def ebooks_txt(self, language: str):
        directory = ebook_search.EBOOK_DIR / language
        paths = absolute_file_paths(directory)
        self.ebook_list = []
        for path in paths:
            with open(path) as ebook_txt:
                self.ebook_list.append(ebook_txt.read())


class DEProgram(Program):
    def __init__(self, args={}):
        super().__init__(DEWiktionaryWord, args=args, language="de")

    def dwds(self, word=""):
        dwds_word = DWDSWord(word or self.previous_word.root)
        print(dwds_word.root_info)

    def duden(self, word=""):
        duden_word = DudenWord(word or self.previous_word.root)
        print(duden_word.root_info)


class ENProgram(Program):
    def __init__(self, args={}):
        super().__init__(ENDictionaryWord, args, "en")
