import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classify_sites import clean_value

class TestClassifySites(unittest.TestCase):
    def test_clean_value_none(self):
        self.assertEqual(clean_value(None), "")

    def test_clean_value_empty(self):
        self.assertEqual(clean_value(""), "")

    def test_clean_value_normal_string(self):
        self.assertEqual(clean_value("hello world"), "hello world")

    def test_clean_value_whitespace(self):
        self.assertEqual(clean_value("  hello  "), "hello")

    def test_clean_value_newlines(self):
        self.assertEqual(clean_value("hello\nworld"), "hello world")
        self.assertEqual(clean_value("hello\rworld"), "hello world")
        self.assertEqual(clean_value("hello\r\nworld"), "hello  world")

    def test_clean_value_quotes(self):
        self.assertEqual(clean_value('hello "world"'), "hello 'world'")

    def test_clean_value_mixed(self):
        input_val = '  \n"hello" \r '
        expected = "'hello'"
        self.assertEqual(clean_value(input_val), expected)

if __name__ == '__main__':
    unittest.main()
