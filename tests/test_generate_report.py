import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_report import clean_value

class TestGenerateReport(unittest.TestCase):
    def test_clean_value_none(self):
        self.assertEqual(clean_value(None), "")

    def test_clean_value_empty(self):
        self.assertEqual(clean_value(""), "")

    def test_clean_value_lowercase(self):
        self.assertEqual(clean_value("HELLO"), "hello")
        self.assertEqual(clean_value("MixedCase"), "mixedcase")

    def test_clean_value_whitespace(self):
        self.assertEqual(clean_value("  hello  "), "hello")

    def test_clean_value_newlines(self):
        # generate_report.clean_value does NOT remove newlines
        self.assertEqual(clean_value("hello\nworld"), "hello\nworld")

    def test_clean_value_quotes(self):
        # generate_report.clean_value does NOT replace quotes
        self.assertEqual(clean_value('hello "world"'), 'hello "world"')

if __name__ == '__main__':
    unittest.main()
