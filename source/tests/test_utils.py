import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from unittest import TestCase, main
from collections import Counter
from utils import *
from ipdb import set_trace as s


class SetRecordsUpdatesTestCase(TestCase):
    def setUp(self):
        self.update_record = SetRecordsUpdates()
        self.update_record.update(["Ignatius"])
        self.update_record.update(["Ignatius"])
        self.update_record.update(["Antioch"])

    def test_update_number(self):
        self.assertEqual(self.update_record.updates, 3)

    def test_update_counter(self):
        self.assertEqual(
            self.update_record.update_counter, Counter({"Ignatius": 2, "Antioch": 1})
        )


class UtilsTestCase(TestCase):
    def setUp(self):
        self.similar_element_list = [
            "12345 Jules   143 Payot",
            "12345 Jean    143 Guitton",
            "12345 Antonin 143 Sertillanges",
        ]

    def test_in_common(self):
        result = in_common(*self.similar_element_list)
        self.assertEqual(result, {"12345 ": (0, 6), " 143 ": (13, 18)})
    def test_remove_common(self):
        result = remove_common(*self.similar_element_list)
        self.assertEqual(result, ['Jules  Payot', 'Jean   Guitton', 'AntoninSertillanges'])

if __name__ == "__main__":
    main()
