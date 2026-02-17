import unittest
import re
import sys
import os


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
# Add the parent directory to sys.path to import classify_sites
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classify_sites import is_negated

class TestIsNegated(unittest.TestCase):

    def test_negation_within_window(self):
        """Test that negation within the window is correctly identified."""
        text_before = "no evidence of"
        self.assertTrue(is_negated(text_before, window=3))

    def test_negation_outside_window(self):
        """
        Test that negation outside the specified window is NOT detected.

        This documents the current limitation where a negation term appearing
        earlier in the text (outside the window) is ignored.
        """
        # "no" is the first word, followed by 3 words ("evidence", "of", "any").
        # With window=3, the check window is ["evidence", "of", "any"].
        # "no" is not in the window.
        text_before = "no evidence of any"
        self.assertFalse(is_negated(text_before, window=3))
import csv
import os
import sys
import unittest

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
# Helper to create a dummy CSV
def create_dummy_csv(filename, rows):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Concat_site_variables'])
        writer.writeheader()
        writer.writerows(rows)

class TestClassifySitesRefactor(unittest.TestCase):
    def setUp(self):
        # Use absolute paths for temp files to avoid issues
        self.input_file = os.path.abspath('test_input_temp.csv')
        self.output_file = os.path.abspath('test_output_temp.csv')
        self.synonyms_file = '/tmp/potential_synonyms.txt'

    def tearDown(self):
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.synonyms_file):
            try:
                os.remove(self.synonyms_file)
            except OSError:
                pass

    def test_classification_logic(self):
        # Create test data
        data = [
            {'Concat_site_variables': 'site has fire-cracked rock and a hearth feature'},
            {'Concat_site_variables': 'no artifacts were found here'},
            {'Concat_site_variables': 'burned clay concentration observed in the unit'},
            {'Concat_site_variables': 'historic glass and metal fragments recovered'},
            {'Concat_site_variables': 'recovered a perdiz point and bone tempered pottery'},
            {'Concat_site_variables': 'found some daub fragments'}
        ]
        create_dummy_csv(self.input_file, data)

        # Run main function
        from io import StringIO
        saved_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            classify_sites.main(self.input_file, self.output_file)
        finally:
            sys.stdout = saved_stdout

        # Verify output
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 6)

        # Row 0: "fire-cracked rock" (Class 1), "hearth" (Class 2)
        self.assertEqual(rows[0]['Class_1_Found'], 'True', "Row 0 should have Class 1")
        self.assertEqual(rows[0]['Class_2_Found'], 'True', "Row 0 should have Class 2")

        # Row 1: "no artifacts"
        self.assertEqual(rows[1]['Class_1_Found'], 'False')
        self.assertEqual(rows[1]['Class_2_Found'], 'False')

        # Row 2: "burned clay" -> Class 2 (because 'burned clay' is in Class 2 keywords)
        self.assertEqual(rows[2]['Class_2_Found'], 'True', "Row 2 should have Class 2 (burned clay)")
        self.assertEqual(rows[2]['Burned_Clay_Found'], 'True', "Row 2 should have Burned Clay")
        self.assertEqual(rows[2]['Burned_Clay_Only'], 'False', "Row 2 should NOT be Burned Clay Only")

        # Row 3: "historic"
        self.assertIn('Historic', rows[3]['Learned_Time_Period'], "Row 3 should be Historic")

        # Row 4: "perdiz point" -> Late Prehistoric II
        self.assertIn('Late Prehistoric', rows[4]['Learned_Time_Period'], "Row 4 should be Late Prehistoric")
        self.assertEqual(rows[4]['Is_Prehistoric'], 'True')

        # Row 5: "daub" -> Burned Clay Only
        self.assertEqual(rows[5]['Burned_Clay_Found'], 'True', "Row 5 should have Burned Clay (daub)")
        self.assertEqual(rows[5]['Class_1_Found'], 'False', "Row 5 should not have Class 1")
        self.assertEqual(rows[5]['Class_2_Found'], 'False', "Row 5 should not have Class 2")
        self.assertEqual(rows[5]['Burned_Clay_Only'], 'True', "Row 5 should be Burned Clay Only")

if __name__ == '__main__':
    unittest.main()
