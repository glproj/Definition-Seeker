from google_images_search import GoogleImagesSearch
from decouple import config
from utils import *
import os, subprocess, re, pathlib, tempfile
from ipdb import set_trace as s

GOOGLE_SEARCH_API_KEY = config("GOOGLE_API_KEY")
CX = config("CX")
gis = GoogleImagesSearch(GOOGLE_SEARCH_API_KEY, CX)
image_temp_directory = tempfile.TemporaryDirectory()
IMAGE_DIR = pathlib.Path(image_temp_directory.name)


def get_images_from_word(word: str, image_dir=IMAGE_DIR):
    _search_params = {
        "q": word,
        "num": 3,
        "fileType": "jpg",
        "rights": "cc_publicdomain|cc_attribute|cc_sharealike|cc_noncommercial|cc_nonderived",
        "imgSize":"medium"
    }
    gis.search(
        _search_params,
        path_to_dir=image_dir,
    )

def copy_image_then_delete(image_path: str):
    extension = re.search("\.(\w+)", image_path).groups()[0]
    new_image_path = image_path
    if extension.isupper():
        new_image_path = lowercase_extension(image_path)
        os.rename(image_path, new_image_path)
    command = f"xclip -selection clipboard -t image/{extension} -i {new_image_path}".split(" ")
    subprocess.run(command)
    os.remove(new_image_path)