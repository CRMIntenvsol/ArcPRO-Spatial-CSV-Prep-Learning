import unittest
import os
import sys
import shutil

# Add parent directory to path to import classify_sites
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from classify_sites import SiteClassifier, process_single_row, normalize_text

class TestSiteClassifierNewFeatures(unittest.TestCase):
    def setUp(self):
        self.classifier = SiteClassifier()

    def test_burned_clay_classification(self):
        # Class 1: General
        text1 = "found some burned clay fragments"
        bc1, bc2 = self.classifier.find_burned_clay_classes(normalize_text(text1))
        self.assertTrue(bc1)
        self.assertFalse(bc2)

        # Class 2: Specific Feature
        text2 = "a clay lined hearth was observed"
        bc1, bc2 = self.classifier.find_burned_clay_classes(normalize_text(text2))
        self.assertFalse(bc1)
        self.assertTrue(bc2)

        # Both
        text3 = "burned clay and clay balls present"
        bc1, bc2 = self.classifier.find_burned_clay_classes(normalize_text(text3))
        self.assertTrue(bc1)
        self.assertTrue(bc2)

    def test_cultural_typology(self):
        # Caddo
        text_caddo = "grog tempered pottery"
        caddo, henrietta, overlap = self.classifier.find_cultural_typology(normalize_text(text_caddo))
        self.assertTrue(caddo)
        self.assertFalse(henrietta)
        self.assertFalse(overlap)

        # Henrietta
        text_henrietta = "shell tempered sherds"
        caddo, henrietta, overlap = self.classifier.find_cultural_typology(normalize_text(text_henrietta))
        self.assertFalse(caddo)
        self.assertTrue(henrietta)
        self.assertFalse(overlap)

        # Overlap
        text_overlap = "grog tempered and shell tempered pottery"
        caddo, henrietta, overlap = self.classifier.find_cultural_typology(normalize_text(text_overlap))
        self.assertTrue(caddo)
        self.assertTrue(henrietta)
        self.assertTrue(overlap)

    def test_is_prehistoric_logic(self):
        # Case 1: Prehistoric Evidence -> True
        row1 = {'Concat_site_variables': 'lithic scatter'}
        clean_row1, _ = process_single_row(row1, self.classifier)
        self.assertTrue(clean_row1['Is_Prehistoric'])

        # Case 2: Historic Evidence Only -> False
        row2 = {'Concat_site_variables': 'historic glass bottle'}
        clean_row2, _ = process_single_row(row2, self.classifier)
        self.assertFalse(clean_row2['Is_Prehistoric'])

        # Case 3: No Data -> "No Data"
        row3 = {'Concat_site_variables': 'just some dirt'}
        clean_row3, _ = process_single_row(row3, self.classifier)
        self.assertEqual(clean_row3['Is_Prehistoric'], "No Data")

    def test_expert_priority(self):
        row = {'Concat_site_variables': 'some text', 'refined_context': 'Expert Period'}
        clean_row, _ = process_single_row(row, self.classifier)
        self.assertEqual(clean_row['Learned_Time_Period'], "Prioritized expert classification: Expert Period")

if __name__ == '__main__':
    unittest.main()
