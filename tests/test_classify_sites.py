import unittest
import re
import sys
import os
import csv
from io import StringIO

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classify_sites import clean_value, is_negated, SiteClassifier, main as classify_main

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

class TestIsNegated(unittest.TestCase):
    def test_negation_within_window(self):
        text_before = "no evidence of"
        self.assertTrue(is_negated(text_before, window=3))

    def test_negation_outside_window(self):
        text_before = "no evidence of any"
        self.assertFalse(is_negated(text_before, window=3))

class TestDetermineTimePeriod(unittest.TestCase):
    def setUp(self):
        # Mock artifact DB
        self.mock_artifact_db = {}
        self.classifier = SiteClassifier(artifact_db=self.mock_artifact_db)

        # Override regex lists for testing
        self.classifier.time_period_re_list = [
            ("Archaic", re.compile(r'\barchaic\b')),
            ("Paleo", re.compile(r'\bpaleo\b')),
            ("Historic", re.compile(r'\bhistoric\b'))
        ]
        self.classifier.artifact_re_list = [
            ("Archaic", re.compile(r'\barrowhead\b')),
            ("Paleo", re.compile(r'\bclovis\b'))
        ]

    def test_determine_time_period_keyword_match(self):
        text = "found an archaic site"
        result = self.classifier.determine_time_period(text, is_prehistoric=False)
        self.assertEqual(result, "Archaic")

    def test_determine_time_period_artifact_match(self):
        text = "found a clovis point"
        result = self.classifier.determine_time_period(text, is_prehistoric=False)
        self.assertEqual(result, "Paleo")

    def test_determine_time_period_multiple_matches(self):
        text = "found archaic and paleo evidence"
        result = self.classifier.determine_time_period(text, is_prehistoric=False)
        self.assertEqual(result, "Archaic; Paleo")

    def test_determine_time_period_inferred_prehistoric(self):
        text = "just some lithics"
        result = self.classifier.determine_time_period(text, is_prehistoric=True)
        self.assertEqual(result, "Inferred: Prehistoric")

    def test_determine_time_period_inferred_historic(self):
        # Using "historic" keyword which is now in our mock list so it returns "Historic"
        # To test inference, we need is_prehistoric=False
        text = "modern trash"
        # Temporarily remove "Historic" from regex list to force inference check
        self.classifier.time_period_re_list = [x for x in self.classifier.time_period_re_list if x[0] != "Historic"]

        result = self.classifier.determine_time_period(text, is_prehistoric=False)
        self.assertEqual(result, "Inferred: Historic")

    def test_determine_time_period_unknown(self):
        text = "nothing special here"
        result = self.classifier.determine_time_period(text, is_prehistoric="No Data")
        self.assertEqual(result, "Unknown")

class TestClassifySitesRefactor(unittest.TestCase):
    def setUp(self):
        self.input_file = os.path.abspath('test_input_temp.csv')
        self.output_file = os.path.abspath('test_output_temp.csv')
        self.synonyms_file = 'potential_synonyms.txt' # Default name used by main

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
        if os.path.exists('relationship_analysis.txt'):
             os.remove('relationship_analysis.txt')
        if os.path.exists('relationship_summary.txt'):
             os.remove('relationship_summary.txt')

    def test_classification_logic(self):
        # Create test data
        data = [
            {'Concat_site_variables': 'site has fire-cracked rock and a hearth feature'},
            {'Concat_site_variables': 'no artifacts were found here'},
            {'Concat_site_variables': 'burned clay concentration observed in the unit'},
            {'Concat_site_variables': 'historic glass and metal fragments recovered'},
            {'Concat_site_variables': 'recovered a perdiz point and bone tempered pottery'}, # Perdiz -> Late Prehistoric II (Toyah)
            {'Concat_site_variables': 'found some daub fragments'}
        ]

        with open(self.input_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Concat_site_variables'])
            writer.writeheader()
            writer.writerows(data)

        # Run main function
        saved_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            classify_main(self.input_file, self.output_file)
        finally:
            sys.stdout = saved_stdout

        # Verify output
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 6)

        # Row 0: "fire-cracked rock" (Class 1), "hearth" (Class 2)
        self.assertEqual(rows[0]['Class_1_Found'], 'True')
        self.assertEqual(rows[0]['Class_2_Found'], 'True')

        # Row 1: "no artifacts"
        self.assertEqual(rows[1]['Class_1_Found'], 'False')
        self.assertEqual(rows[1]['Class_2_Found'], 'False')

        # Row 2: "burned clay" -> Class 2 (because 'burned clay' is in Class 2 keywords)
        # Wait, 'burned clay' is in BURNED_CLAY_CLASS_1_KEYWORDS (general)
        # Is it in CLASS_2_KEYWORDS (hearth related)?
        # In updated classify_sites.py: CLASS_2_KEYWORDS includes "burned clay".
        self.assertEqual(rows[2]['Class_2_Found'], 'True')
        self.assertEqual(rows[2]['Burned_Clay_Found'], 'True')

        # Row 3: "historic" -> Learned_Time_Period should contain "Historic"
        self.assertIn('Historic', rows[3]['Learned_Time_Period'])
        self.assertEqual(rows[3]['Is_Prehistoric'], 'False')

        # Row 4: "perdiz point" -> Late Prehistoric II (Toyah Phase)
        # Note: "perdiz" is in ARTIFACT_DB (if extracted_artifacts.json is loaded correctly).
        # Assuming ARTIFACT_DB_FILE exists and contains "Perdiz".
        # If running in environment where extracted_artifacts.json is present (it is), this should work.
        # "bone tempered" -> Prehistoric
        self.assertTrue(rows[4]['Learned_Time_Period'] != "Unknown", "Should detect Perdiz")
        self.assertEqual(rows[4]['Is_Prehistoric'], 'True')

        # Row 5: "daub" -> Burned Clay Class 1 (General)
        # Daub is in BURNED_CLAY_CLASS_1_KEYWORDS.
        self.assertEqual(rows[5]['Burned_Clay_Found'], 'True')
        self.assertEqual(rows[5]['Burned_Clay_Only'], 'True')

if __name__ == '__main__':
    unittest.main()
