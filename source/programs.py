import termcolor, ebook_search, pyperclip, sys, cmd, typing
from word_info_extractor import *
from utils import VALID_LANGUAGE_CODES
from image_extractor import IMAGE_EXTRACTION, get_images_from_word

WORD_PRIMARY_CLASSES = {
    "br": BRDicioWord,
    "en": ENWiktionaryWord,
    "de": DEWiktionaryWord,
    "la": LAWiktionaryWord,
    "fr": FRWiktionaryWord,
    "en-ru": ENRUWiktionaryWord,
}


class Program(cmd.Cmd):
    word_class = None
    prompt = "Word: "
    all_sources = {
        "de": {"dwds": DWDSWord, "duden": DudenWord},
        "br": {},
        "en": {"dict": ENDictionaryWord},
        "fr": {"enfr": ENFRWiktionaryWord, "defr": DEFRWiktionaryWord},
        "en-ru": {},
    }
    lang = CONFIG_PARSER["DEFAULT"]["Language"]

    def precmd(self, line):
        cmd, arg, line = self.parseline(line)
        for lang, sources in self.all_sources.items():
            if cmd in sources.keys() and lang != self.lang:
                print(
                    f"Change your language to {VALID_LANGUAGES[lang]} before using this command.",
                    f"Your current language is {self.lang}.",
                    file=self.stdout,
                )
                return "DO_NOTHING"
        return line

    def onecmd(self, line):
        """Interpret the argument as though it had been typed in response
        to the prompt.

        This may be overridden, but should not normally need to be;
        see the precmd() and postcmd() methods for useful execution hooks.
        The return value is a flag indicating whether interpretation of
        commands by the interpreter should stop.

        """
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if line == "EOF":
            self.lastcmd = ""
            sys.exit()
        if line == "DO_NOTHING":
            return
        if cmd == "":
            return self.default(line)
        else:
            try:
                func = getattr(self, "do_" + cmd)
            except AttributeError:
                return self.default(line)
            try:
                return func(arg)
            except WordNotAvailable as e:
                print(e)

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline

                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            print("\033[31m", end="", file=self.stdout)
                            line = input(self.prompt)
                            print("\033[0m", end="", file=self.stdout)
                        except EOFError:
                            line = "EOF"
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.getvalue()
                        if not len(line):
                            line = "EOF"
                        else:
                            line = line.rstrip("\r\n")
                # try:
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
                # except WordNotAvailable as e:
                #     print(e)
                # except Exception as e:
                #     print("Some error occurried.")
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline

                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def default(self, line):
        if not vars(self).get("previous_word"):
            self.previous_word = ""
        input_ = line
        input_list = input_.split(" ")
        input_list_wo_modifiers = word_str, *arguments = [
            x for x in input_list if not x.startswith("--")
        ]
        modifiers = [x for x in input_list if x.startswith("--")]
        try:
            phrase = "_".join(input_list_wo_modifiers)
            term = phrase if ("--p" in modifiers) else word_str
            word = self.word_class(term)
            self.previous_word = word
        except WordNotAvailable as e:
            print(e, file=self.stdout)
            return
        if not word.root == word.word:
            print(f"Redirecting to {word.root}\n", file=self.stdout)
        print(f"IPA: {word.ipa}\n", file=self.stdout)
        if word.go_to_root:
            print(f"root IPA: {word.root_ipa}\n", file=self.stdout)
        pyperclip.copy(f"{word.root_ipa} {word.root_pronunciation_url}")
        print(word.root_info, file=self.stdout)

    def get_previous_word(self):
        return vars(self).get("previous_word", "")

    def do_q(self, arg):
        sys.exit(0)

    def do_lang(self, lang):
        """Changes the language of the running program.

        Args:
            lang (str, optional): language code. Defaults to ''.
        """
        if (lang not in VALID_LANGUAGE_CODES) or not lang.strip():
            print(
                f"The language code should be one of the following: {', '.join(VALID_LANGUAGE_CODES)}",
                file=self.stdout,
            )
            return
        CONFIG_PARSER["DEFAULT"]["Language"] = lang
        self.lang = lang
        self.word_class = WORD_PRIMARY_CLASSES[self.lang]
        with open(CONFIG_PATH, "w") as file:
            CONFIG_PARSER.write(file)

    def do_examples(self, arg):
        """prints examples on the screen"""
        word = arg or self.previous_word
        if arg:
            inflections = tuple([word])
        else:
            inflections = self.previous_word.get_inflections()
        for lang, book_name_text in self.ebook_lang_name_txt.items():
            if lang != self.lang:
                continue
            book_name_text = [
                (name, txt)
                for book_name_txt in book_name_text
                for name, txt in book_name_txt.items()
            ]
            for book_name, book_txt in book_name_text:
                examples = ebook_search.get_examples(inflections, book_txt)
                for example in examples:
                    print(
                        termcolor.colored(book_name.upper(), "blue"), file=self.stdout
                    )
                    print(example + "\n", file=self.stdout)

    def do_toggle(self, arg):
        if arg == "show_word":
            CONFIG_PARSER["DEFAULT"]["show_word"] = (
                "1" if CONFIG_PARSER["DEFAULT"].get("show_word") == "0" else "0"
            )
            with open(CONFIG_PATH, "w") as config:
                CONFIG_PARSER.write(config)
            print("New value: "+CONFIG_PARSER["DEFAULT"].get("show_word"))
        else:
            print("Options available: show_word.")
            print("show_word: show word in definitions.")

    def _get(self, attr: str, default):
        try:
            return getattr(self, attr)
        except AttributeError:
            return default

    def preloop(self):
        directory = ebook_search.EBOOK_DIR
        dir_paths = absolute_file_paths(directory)
        from collections import defaultdict

        for sources in self.all_sources.values():
            for source_name, source_class in sources.items():

                def source_func(source_class):
                    def s(word):
                        w = source_class(word or self.previous_word.root)
                        print(w.root_info, file=self.stdout)

                    return s

                setattr(self, "do_" + source_name, source_func(source_class))
        # {lang: [{name: txt}]}
        self.ebook_lang_name_txt = defaultdict(list)
        for dir_path in dir_paths:
            dir_pathlib = pathlib.Path(dir_path)
            file_paths = absolute_file_paths(dir_pathlib)
            lang = dir_pathlib.name
            for file_path in file_paths:
                with open(file_path) as ebook_txt:
                    ebook_name = os.path.splitext(os.path.basename(file_path))[0]
                    self.ebook_lang_name_txt[lang].append(
                        {ebook_name: ebook_txt.read()}
                    )


class TestProgram(Program):
    use_rawinput = 0

    def postcmd(self, stop, line):
        return True
