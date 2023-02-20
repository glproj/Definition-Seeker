import requests, shutil, os, pyperclip, tkinter, subprocess, time, tempfile, sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from unittest import TestCase, main
from image_extractor import *
from utils import *

class ImageExtractorTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_dir_path = str(pathlib.Path(self.test_dir.name))
        self.tk = tkinter.Tk()
        get_images_from_word('bruh', image_dir=self.test_dir_path)
        self.test_image_paths = absolute_file_paths(self.test_dir_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_copy_image_then_delete(self):
        with self.subTest("lowercase common extensions"):
            for image_path in self.test_image_paths[0:2]:
                extension = os.path.split(image_path)[0]
                copy_image_then_delete(image_path)
                self.assertFalse(os.path.exists(image_path))

        with self.subTest("uppercase extension"):
            copy_image_then_delete(self.test_image_paths[2])
            self.assertFalse(os.path.exists(image_path))
            self.assertFalse(os.path.exists(lowercase_extension(image_path)))

    def save_clipboard(self, image_path):
        extension = re.search("\.(\w+)", image_path).groups()[0]
        test_path = image_path.split("/")
        test_path[-2] = "images_test"
        test_path = test_path.join()
        command = (
            f"xclip -selection clipboard -t image/{extension} -o > file.png".split(" ")
        )
        subprocess.run(command)


if __name__ == "__main__":
    main()
