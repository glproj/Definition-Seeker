import tkinter
from tkinter import font as tkfont
import tkinter.scrolledtext
import tkinter.filedialog
from tkinter import ttk
from ipdb import set_trace as s
from utils import VALID_LANGUAGES, SUPPORTED_EXTENSIONS, CONFIG_PARSER, CONFIG_PATH


class ConfigSetter(ttk.Frame):
    """Frame for setting up ebooks in the configuration file"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_language = ""

        explanation_text = f"""Set the path of your favorite ebooks.
        Later you'll be able to use them to fetch examples.
        Supported extensions: {" ".join(SUPPORTED_EXTENSIONS)}"""
        explanation = tkinter.Label(self, text=explanation_text)

        button_frame = ttk.Frame(self)
        language_buttons = [
            ttk.Button(
                button_frame,
                text=language,
                command=lambda lang=language: self.ask_for_files(lang),
            )
            for language in VALID_LANGUAGES.values()
        ]

        self.file_paths_text = tkinter.scrolledtext.Text(self, width=50, height=15)

        explanation.grid(column=0, row=0)
        for column, button in enumerate(language_buttons):
            button.grid(column=column, row=0, padx=10)
        button_frame.grid(column=0, row=1)
        self.file_paths_text.grid(column=0, row=2)

    def ask_for_files(self, lang):
        """Asks for file paths and then append
        (or write, more on that later) the paths of the files you
        chose to the self.file_paths_text widget. This method will
        use self.last_language to decide whether it will write or
        append to the Text widget.
        """
        file_paths = tkinter.filedialog.askopenfilenames()
        if not lang == self.last_language:
            self.file_paths_text.delete("1.0", "end")
        self.last_language = lang
        escape = "\n" if self.file_paths_text.get("1.0", "end").strip() else ""
        self.file_paths_text.insert("end", chars=escape + "\n".join(file_paths))

    def set_config(self):
        paths_list = self.file_paths_text.get("1.0", "end").strip().split("\n")
        for lang_code, lang in VALID_LANGUAGES.items():
            if lang == self.last_language:
                CONFIG_PARSER[lang_code]["ebook_paths"] = str(paths_list)

    def finish(self):
        with open(CONFIG_PATH, 'w') as config:
            CONFIG_PARSER.write(config)


class ConfigViewer(ttk.Frame):
    """View CONFIG_PARSER contents"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = tkinter.font.Font(family="Noto Sans UI", size=10, weight="bold")
        pretty_config = ""
        for part, section in CONFIG_PARSER.items():
            pretty_config += f"{part}:\n"
            for key, value in section.items():
                pretty_config += f"  {key}: {value}\n"
        settings = ttk.Label(self, text=pretty_config, wraplength=500, font=font)
        settings.pack()


class ConfigApp(tkinter.Tk):
    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)

        self.container = tkinter.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (ConfigSetter, ConfigViewer):
            self.update_frames(F)

        bottom_buttons_frame = ttk.Frame(self.container)
        end_button = ttk.Button(
            bottom_buttons_frame,
            text="Finish",
            command=self.frames["ConfigSetter"].finish,
        )
        set_config_button = ttk.Button(
            bottom_buttons_frame,
            text="Set Config",
            command=self.frames["ConfigSetter"].set_config,
        )
        self.view_config_text = tkinter.StringVar(self.container, "View Config")
        view_config_button = AlternatingButton(
            bottom_buttons_frame,
            textvariable=self.view_config_text,
            command=(self.show_config, self.show_config_setter),
        )
        end_button.pack(side="right")
        set_config_button.pack(side="right")
        view_config_button.pack(side="right")

        bottom_buttons_frame.grid(column=0, row=1, sticky="E")
        self.show_frame("ConfigSetter")

    def show_frame(self, page_name):
        """Show a frame for the given page name"""
        if last_frame := vars(self).get("last_frame"):
            self.frames[self.last_frame].grid_forget()
        self.frames[page_name].grid(column=0, row=0)
        self.last_frame = page_name

    def show_config(self):
        self.update_frames(ConfigViewer)
        self.view_config_text.set("Go Back")
        self.show_frame("ConfigViewer")

    def show_config_setter(self):
        self.view_config_text.set("View Config")
        self.show_frame("ConfigSetter")

    def update_frames(self, class_):
        page_name = class_.__name__
        frame = class_(self.container)
        self.frames[page_name] = frame


class AlternatingButton(ttk.Button):
    """Button that alternates between commands.
    For example, if you pass (func1, func2) to command, the first
    time you click the button func1 will be executed. Second click, func2.
    Third click, func1, and so on."""

    def __init__(self, *args, **kwargs):
        self.commands = kwargs["command"]
        self.last_command_index = 1
        kwargs["command"] = self.alternate
        super().__init__(*args, **kwargs)
        # self.commands = kwargs.pop('command')

    def alternate(self):
        """Alternate between commands"""
        index = 1 if self.last_command_index == 0 else 0
        self.commands[index]()
        self.last_command_index = index

def setup_initial_config_file():
    CONFIG_PARSER["DEFAULT"]['Language']='en'
    for lang_code in VALID_LANGUAGES.keys():
        CONFIG_PARSER[lang_code] = {'ebook_paths': '[]'}
    CONFIG_PARSER["DEFAULT"]["GOOGLE_API_KEY"] = ''
    CONFIG_PARSER["DEFAULT"]["CX"] = ''
    with open(CONFIG_PATH, 'w') as config:
        CONFIG_PARSER.write(config)
