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
        pass


class ConfigViewer(ttk.Frame):
    """View CONFIG_PARSER contents"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pretty_config = ""
        for part, section in CONFIG_PARSER.items():
            pretty_config += f"{part}:\n"
            for key, value in section.items():
                pretty_config += f"  {key}: {value}\n"
        settings = ttk.Label(self, text=pretty_config, wraplength=400)
        settings.pack()


class ConfigApp(tkinter.Tk):
    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(
            family="Helvetica", size=18, weight="bold", slant="italic"
        )

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
        if last_frame := vars(self).get("last_frame"):
            self.frames[self.last_frame].grid_forget()
        self.frames[page_name].grid(column=0, row=0)
        self.last_frame = page_name

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


root = ConfigApp()
root.geometry('400x400')
root.mainloop()
