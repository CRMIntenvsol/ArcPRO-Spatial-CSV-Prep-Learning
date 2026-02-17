import unittest
import sys
import os
import csv

# Add parent directory to path so we can import csv_utils_helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv_utils_helpers

class TestCSVUtilsHelpers(unittest.TestCase):
    def test_clean_value_basic(self):
        self.assertEqual(csv_utils_helpers.clean_value("hello"), "hello")
        self.assertEqual(csv_utils_helpers.clean_value("  hello  "), "hello")

    def test_clean_value_none(self):
        self.assertEqual(csv_utils_helpers.clean_value(None), "")
        self.assertEqual(csv_utils_helpers.clean_value(""), "")

    def test_clean_value_newlines(self):
        # The function replaces \r with ' ' and \n with ' ' independently.
        # So "hello\r\nworld" -> "hello  world"
        self.assertEqual(csv_utils_helpers.clean_value("hello\nworld"), "hello world")
        self.assertEqual(csv_utils_helpers.clean_value("hello\rworld"), "hello world")
        self.assertEqual(csv_utils_helpers.clean_value("hello\r\nworld"), "hello  world")

    def test_clean_value_quotes(self):
        self.assertEqual(csv_utils_helpers.clean_value('hello "world"'), "hello 'world'")
        self.assertEqual(csv_utils_helpers.clean_value('"quoted"'), "'quoted'")

    def test_clean_value_lower(self):
        self.assertEqual(csv_utils_helpers.clean_value("Hello World", lower=True), "hello world")
        self.assertEqual(csv_utils_helpers.clean_value("  Hello World  ", lower=True), "hello world")
        self.assertEqual(csv_utils_helpers.clean_value(None, lower=True), "")

    def test_increase_csv_field_size_limit(self):
        # Just check it runs without error and sets a large limit
        try:
            csv_utils_helpers.increase_csv_field_size_limit()
        except Exception as e:
            self.fail(f"increase_csv_field_size_limit raised exception: {e}")

        limit = csv.field_size_limit()
        # Default is usually small (131072). We expect it to be very large.
        # sys.maxsize is usually much larger than default.
        self.assertTrue(limit > 131072, f"Limit {limit} is not greater than default")

if __name__ == '__main__':
    unittest.main()
