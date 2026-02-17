import unittest
import re
import sys
import os

# Add parent directory to path to import classify_sites
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import classify_sites

class TestDetermineTimePeriod(unittest.TestCase):

    def setUp(self):
        # Setup mock data for injection
        self.mock_time_period_re_list = [
            ("Archaic", re.compile(r'\barchaic\b')),
            ("Paleo", re.compile(r'\bpaleo\b')),
            ("Historic", re.compile(r'\bhistoric\b'))
        ]

        self.mock_artifact_re_list = [
            ("Archaic", re.compile(r'\barrowhead\b')),
            ("Paleo", re.compile(r'\bclovis\b'))
        ]

    def test_determine_time_period_keyword_match(self):
        text = "found an archaic site"
        result = classify_sites.determine_time_period(
            text, {}, False,
            time_period_re_list=self.mock_time_period_re_list,
            artifact_re_list=self.mock_artifact_re_list
        )
        self.assertEqual(result, "Archaic")

    def test_determine_time_period_artifact_match(self):
        text = "found a clovis point"
        result = classify_sites.determine_time_period(
            text, {}, False,
            time_period_re_list=self.mock_time_period_re_list,
            artifact_re_list=self.mock_artifact_re_list
        )
        self.assertEqual(result, "Paleo")

    def test_determine_time_period_multiple_matches(self):
        text = "found archaic and paleo evidence"
        result = classify_sites.determine_time_period(
            text, {}, False,
            time_period_re_list=self.mock_time_period_re_list,
            artifact_re_list=self.mock_artifact_re_list
        )
        # Assuming the function sorts the result
        self.assertEqual(result, "Archaic; Paleo")

    def test_determine_time_period_inferred_prehistoric(self):
        text = "just some lithics"
        result = classify_sites.determine_time_period(
            text, {}, True,
            time_period_re_list=self.mock_time_period_re_list,
            artifact_re_list=self.mock_artifact_re_list
        )
        self.assertEqual(result, "Inferred: Prehistoric")

    def test_determine_time_period_inferred_historic(self):
        # Here "historic" is in the mock time_period_re_list, so it returns "Historic"
        # If we want to test "Inferred: Historic", we need text that has "historic" keyword but
        # doesn't match the regex list. But "historic" regex matches "historic" word.

        # So we should create a separate list for this test or use a word that isn't in the list
        # but contains "historic" substring? No, the code checks `if "historic" in normalized_text`.

        # To hit "Inferred: Historic", the loops must return nothing.
        # So I need to use a list that doesn't have "Historic" regex.

        custom_tp_list = [("Archaic", re.compile(r'\barchaic\b'))]
        text = "this is a historic site"
        result = classify_sites.determine_time_period(
            text, {}, False,
            time_period_re_list=custom_tp_list,
            artifact_re_list=self.mock_artifact_re_list
        )
        self.assertEqual(result, "Inferred: Historic")

    def test_determine_time_period_unknown(self):
        text = "nothing special here"
        result = classify_sites.determine_time_period(
            text, {}, False,
            time_period_re_list=self.mock_time_period_re_list,
            artifact_re_list=self.mock_artifact_re_list
        )
        self.assertEqual(result, "Unknown")

    def test_determine_time_period_default_args(self):
        # Test that default arguments (using globals) still work (backward compatibility)
        # For this to work, we rely on the globals being empty lists (because imported module doesn't populate them)
        # So it should return "Unknown" unless text has "historic" or is_prehistoric is True.

        # But wait, in setUp I didn't touch globals.
        # If I import classify_sites, globals are empty.

        text = "nothing"
        result = classify_sites.determine_time_period(text, {}, False)
        self.assertEqual(result, "Unknown")

        # If I had populated globals in main, this test would be flaky/depend on external state.
        # Since I know they are empty, this confirms defaults are used.

if __name__ == '__main__':
    unittest.main()
