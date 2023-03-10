import keyboard_shortcuts, requests, bs4, pyperclip, os, ast, readline, atexit, signal, sys, getopt, argparse, configparser, termcolor
from word_info_extractor import *
from image_extractor import *
from ebook_search import *
import programs
from pathlib import Path
from config_setter import ConfigApp, setup_initial_config_file

histfile = os.path.join(os.path.expanduser("~"), ".wiktionary_history")
try:
    readline.read_history_file(histfile)
    h_len = readline.get_current_history_length()
except FileNotFoundError:
    open(histfile, "wb").close()
    h_len = 0


# --- exit handlers --
def remove_q():
    h_len = readline.get_current_history_length()
    readline.remove_history_item(h_len - 1)


def save(prev_h_len, histfile):
    new_h_len = readline.get_current_history_length()
    readline.set_history_length(1000)
    readline.append_history_file(new_h_len - prev_h_len, histfile)


def save_when_ctrl_c(signum, frame):
    save(h_len, histfile)
    print('\033[0m', end='')
    sys.exit()


signal.signal(signal.SIGINT, save_when_ctrl_c)
atexit.register(save, h_len, histfile)
atexit.register(remove_q)
atexit.register(print, '\033[0m')
# --- exit handlers --
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-w", "--word", help="The word you are trying to search")
arg_parser.add_argument(
    "-s",
    "--source",
    choices=("wiktionary", "dwds", "duden", "examples"),
    default="wiktionary",
    help="The source you are going to search from. Valid values: wiktionary (default), dwds, duden",
)
arg_parser.add_argument("-c", "--config", action="store_true")
args = arg_parser.parse_args()
str_valid_lc = ", ".join(VALID_LANGUAGE_CODES)
if not CONFIG_PARSER.get("DEFAULT", "language", fallback=False) or vars(args).get("config"):
    if not vars(args).get("config"):
        setup_initial_config_file()
        print(
            """Setup your configuration file. If you get anything wrong, you can
change your settings later with the --config option"""
        )
        print()
    config_app = ConfigApp()
    config_app.geometry('500x500')
    config_app.mainloop()
    CONFIG_PARSER["DEFAULT"]['google_search_api_key'] = input("Google Search Api Key (press 'enter' if you don't have one): ")
    CONFIG_PARSER["DEFAULT"]['cx'] = input("Google Search Engine ID (press 'enter' if you don't have one): ")
    with open(CONFIG_PATH, 'w') as config:
        CONFIG_PARSER.write(config)

print(
    "Current language: " + CONFIG_PARSER["DEFAULT"]["language"],
    "q=quit",
    "dwds=dwds' definition for the previous word",
    "duden=duden's definition for the previous word",
    "save=save previous word for later use",
    "images=download 3 images related to the previous word. You can paste them using pause_break",
    "examples=shows examples of previous word from the books in the configfile",
    "lang {language code}=change language.Available languages: " + str_valid_lc,
    sep="\n",
)
print("-" * 72)
setup_ebooks()
classes = {'br': BRDicioWord,'en': ENDictionaryWord, 'de': DEWiktionaryWord}
language = CONFIG_PARSER["DEFAULT"]["language"]
program = programs.Program()
program.word_class = classes[language]
program.cmdloop()
#Soli Deo Gloria