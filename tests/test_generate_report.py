import unittest
import sys
import os
import csv
from unittest.mock import patch, mock_open, MagicMock

# Adjust sys.path to allow importing from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate_report

class TestGenerateReport(unittest.TestCase):

    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_ensure_dir(self, mock_exists, mock_makedirs):
        """Test ensure_dir creates directory if it doesn't exist."""
        # Case 1: Directory exists
        mock_exists.return_value = True
        generate_report.ensure_dir("test_dir")
        mock_makedirs.assert_not_called()

        # Case 2: Directory does not exist
        mock_exists.return_value = False
        generate_report.ensure_dir("test_dir")
        mock_makedirs.assert_called_with("test_dir")

    def test_analyze_data_file_not_found(self):
        """Test analyze_data handles missing file gracefully."""
        # Mock open to raise FileNotFoundError
        with patch('builtins.open', side_effect=FileNotFoundError):
            with self.assertRaises(SystemExit) as cm:
                generate_report.analyze_data("non_existent.csv")
            self.assertEqual(cm.exception.code, 1)

    def test_analyze_data_calculations(self):
        """Test statistics calculation with mocked CSV data."""
        csv_content = (
            "Class_1_Found,Class_2_Found,Class_3_Found,Burned_Clay_Found,Burned_Clay_Only,Burned_Clay_Class_1_Found,Burned_Clay_Class_2_Found,Caddo_Found,Henrietta_Found,Henrietta_Caddo_Overlap_Found,Is_Prehistoric,Learned_Time_Period,Soil_Inferred_Context\n"
            "True,False,False,False,False,False,False,True,False,False,False,,Deep Alluvium\n"
            "False,True,False,False,False,False,False,False,True,False,False,Historic,\n"
            "False,False,True,True,False,True,True,True,True,True,True,Prehistoric,Sandy Loam\n"
        )

        with patch('builtins.open', mock_open(read_data=csv_content)):
            stats = generate_report.analyze_data("dummy.csv")

        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['c1'], 1)
        self.assertEqual(stats['c2'], 1)
        self.assertEqual(stats['c3'], 1)

        self.assertEqual(stats['caddo'], 2) # Row 1, Row 3
        self.assertEqual(stats['henrietta'], 2) # Row 2, Row 3
        self.assertEqual(stats['overlap'], 1) # Row 3

        self.assertEqual(stats['burned_clay'], 1) # Row 3
        self.assertEqual(stats['bc_class_1'], 1) # Row 3
        self.assertEqual(stats['bc_class_2'], 1) # Row 3

        self.assertEqual(stats['soil_contexts']['Deep Alluvium'], 1)
        self.assertEqual(stats['soil_contexts']['Sandy Loam'], 1)

if __name__ == '__main__':
    unittest.main()
