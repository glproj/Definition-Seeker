import os, readline, atexit, signal, sys, argparse
from word_info_extractor import *
from image_extractor import *
from ebook_search import *
import logging

logging.basicConfig(
    filename="main.log",
    encoding="utf-8",
    level=logging.DEBUG,
    filemode="w",
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
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
    print("\033[0m", end="")
    sys.exit()


signal.signal(signal.SIGINT, save_when_ctrl_c)
atexit.register(save, h_len, histfile)
atexit.register(remove_q)
atexit.register(print, "\033[0m")
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
setup_empty_config()
print(
    "Current language: " + CONFIG_PARSER["DEFAULT"]["language"],
)
print("-" * 72)
setup_ebooks()
language = CONFIG_PARSER["DEFAULT"]["language"]
import programs

program = programs.Program()
program.word_class = programs.WORD_PRIMARY_CLASSES[language]
program.cmdloop()
# Soli Deo Gloria
