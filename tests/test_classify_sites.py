import csv
import os
import sys
import unittest

# Add parent directory to path to import classify_sites
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import classify_sites

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
