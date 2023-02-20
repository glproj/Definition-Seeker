import atexit, os, tkinter, time, pyperclip
from pynput import keyboard
from image_extractor import *
from utils import *

KEY_SIMULATOR = keyboard.Controller()


def on_press(key):
    root = tkinter.Tk()
    try:
        k = key.char
    except:
        k = key.name
    if k == "pause":
        try:
            image_path = absolute_file_paths(IMAGE_DIR)[0]
            copy_image_then_delete(image_path)
            KEY_SIMULATOR.press(keyboard.Key.ctrl)
            KEY_SIMULATOR.press("v")
            KEY_SIMULATOR.release(keyboard.Key.ctrl)
            KEY_SIMULATOR.release("v")
        except IndexError:
            pass
    root.destroy()


listener = keyboard.Listener(on_press=on_press)
listener.start()
