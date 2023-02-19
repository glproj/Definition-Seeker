import tkinter
from tkinter import font as tkfont
import tkinter.scrolledtext
import tkinter.filedialog
from tkinter import ttk
from ipdb import set_trace as s
from utils import VALID_LANGUAGES, SUPPORTED_EXTENSIONS, CONFIG_PARSER


class ConfigSetter(ttk.Frame):
    """Frame for setting up ebooks in the configuration file"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        explanation_text = f"""Set the path of your favorite ebooks.
        Later you'll be able to use them to fetch examples.
        Supported extensions: {" ".join(SUPPORTED_EXTENSIONS)}"""
        explanation = tkinter.Label(self, text=explanation_text)

        button_frame = ttk.Frame(self)
        language_buttons = [
            ttk.Button(button_frame, text=language, command=self.ask_for_files)
            for language in VALID_LANGUAGES.values()
        ]

        self.file_paths_text = tkinter.scrolledtext.Text(self, width=50, height=15)

        explanation.grid(column=0, row=0)
        for column, button in enumerate(language_buttons):
            button.grid(column=column, row=0, padx=10)
        button_frame.grid(column=0, row=1)
        self.file_paths_text.grid(column=0, row=2)

    def ask_for_files(self, *args):
        pass

    def set_config(self):
        pass


class ConfigViewer(ttk.Frame):
    def __init__(self):
        pass


class SimpleApp(tkinter.Tk):
    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(
            family="Helvetica", size=18, weight="bold", slant="italic"
        )

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tkinter.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        bottom_buttons_frame = ttk.Frame(container)
        end_button = ttk.Button(bottom_buttons_frame, text="Finish")
        set_config_button = ttk.Button(bottom_buttons_frame, text="Set Config")
        view_config_button = ttk.Button(bottom_buttons_frame, text="View Config")
        end_button.pack(side="right")
        set_config_button.pack(side="right")
        view_config_button.pack(side="right")

        self.frames = {}
        for F in (ConfigSetter,):
            page_name = F.__name__
            frame = F(container)
            self.frames[page_name] = frame
            frame.grid(column=0, row=0)

        bottom_buttons_frame.grid(column=0, row=1, sticky="E")
        self.show_frame("ConfigSetter")

    def show_frame(self, page_name):
        """Show a frame for the given page name"""
        frame = self.frames[page_name]
        frame.tkraise()


root = SimpleApp()
root.mainloop()
