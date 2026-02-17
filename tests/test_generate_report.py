import unittest
import sys
import os
import csv
from unittest.mock import patch, mock_open, MagicMock

# Adjust sys.path to allow importing from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate_report

class TestGenerateReport(unittest.TestCase):

    def test_clean_value(self):
        """Test the clean_value helper function."""
        # Note: clean_value is now in csv_utils_helpers, but we can test it via import if needed
        # Or test how generate_report uses it.
        # For this test, let's verify generate_report imports it correctly or use csv_utils_helpers directly
        import csv_utils_helpers
        self.assertEqual(csv_utils_helpers.clean_value(None), "")
        self.assertEqual(csv_utils_helpers.clean_value(""), "")
        self.assertEqual(csv_utils_helpers.clean_value("  Test  ", lower=True), "test")
        self.assertEqual(csv_utils_helpers.clean_value("VALUE", lower=True), "value")

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
        with patch('builtins.open', side_effect=FileNotFoundError):
            with self.assertRaises(SystemExit) as cm:
                generate_report.analyze_data("non_existent.csv")
            self.assertEqual(cm.exception.code, 1)

    def test_analyze_data_calculations(self):
        """Test statistics calculation with mocked CSV data."""
        csv_content = (
            "Class_1_Found,Class_2_Found,Class_3_Found,Burned_Clay_Found,Burned_Clay_Only,Is_Prehistoric,Learned_Time_Period\n"
            "True,False,False,False,False,False,\n"
            "False,True,False,False,False,False,Historic\n"
            "False,False,True,True,False,True,Prehistoric\n"
            "False,False,False,True,True,False,Unknown\n"
        )

        with patch('builtins.open', mock_open(read_data=csv_content)):
            stats = generate_report.analyze_data("dummy.csv")

        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['c1'], 1)
        self.assertEqual(stats['c2'], 1)
        self.assertEqual(stats['c3'], 1)
        self.assertEqual(stats['c1_only'], 1)
        self.assertEqual(stats['c2_only'], 1)
        self.assertEqual(stats['c3_only'], 1)

        self.assertEqual(stats['prehistoric'], 1)
        self.assertEqual(stats['c3_prehistoric'], 1)

        self.assertEqual(stats['burned_clay'], 2)
        self.assertEqual(stats['burned_clay_only'], 1)

        self.assertEqual(stats['time_periods']['Unknown'], 2)
        self.assertEqual(stats['time_periods']['Historic'], 1)
        self.assertEqual(stats['time_periods']['Prehistoric'], 1)

    def test_generate_charts(self):
        """Test that charts are generated when PLOTTING_AVAILABLE is True."""
        stats = {
            'c1': 10, 'c2': 5, 'c3': 5,
            'c3_prehistoric': 3, 'c3_historic_only': 2,
            'time_periods': generate_report.Counter({'A': 10, 'B': 5})
        }

        # We patch 'generate_report.plt' because 'matplotlib.pyplot' might not exist
        # and generate_report imports it as plt.
        # create=True allows creating the attribute if it doesn't exist (which it won't if import failed)
        mock_plt = MagicMock()

        with patch('generate_report.plt', mock_plt, create=True), \
             patch('generate_report.PLOTTING_AVAILABLE', True):

            generate_report.generate_charts(stats, "output_dir")

            # Verify calls
            self.assertTrue(mock_plt.figure.called)
            self.assertTrue(mock_plt.bar.called)
            self.assertTrue(mock_plt.pie.called)
            self.assertTrue(mock_plt.savefig.called)
            self.assertTrue(mock_plt.close.called)

            # Verify savefig calls
            calls = [call.args[0] for call in mock_plt.savefig.call_args_list]
            self.assertTrue(any('class_distribution.png' in str(c) for c in calls))

    def test_generate_charts_unavailable(self):
        """Test that charts are skipped when PLOTTING_AVAILABLE is False."""
        stats = {}

        # We still mock plt to ensure it is NOT called
        mock_plt = MagicMock()

        with patch('generate_report.plt', mock_plt, create=True), \
             patch('generate_report.PLOTTING_AVAILABLE', False):

            generate_report.generate_charts(stats, "output_dir")

            mock_plt.savefig.assert_not_called()

    def test_write_text_report(self):
        """Test that the text report is written with correct content."""
        stats = {
            'total': 100,
            'c1': 50, 'c2': 30, 'c3': 20,
            'c1_only': 40, 'c2_only': 20, 'c3_only': 10,
            'prehistoric': 60,
            'c3_prehistoric': 15, 'c3_historic_only': 5,
            'burned_clay': 25, 'burned_clay_only': 5,
            'bc_with_c1': 10, 'bc_with_c2': 5, 'bc_with_c3': 5, 'bc_prehistoric': 15,
            'time_periods': generate_report.Counter({'Period A': 50, 'Period B': 50})
        }

        with patch('builtins.open', mock_open()) as mock_file:
            generate_report.write_text_report(stats, "output_dir")

            mock_file.assert_called_with(os.path.join("output_dir", "Burned_Rock_Analysis_Report.txt"), 'w', encoding='utf-8')
            handle = mock_file()

            # Verify content
            written = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn("BURNED ROCK ANALYSIS REPORT", written)
            self.assertIn("Total Sites Processed: 100", written)
            self.assertIn("Class 1 (Scatters): 50", written)

    def test_write_methodology_report(self):
        """Test writing the methodology report."""
        with patch('builtins.open', mock_open()) as mock_file:
            generate_report.write_methodology_report("output_dir")
            mock_file.assert_called()

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
import pytest
from generate_report import clean_value

def test_clean_value_basic():
    """Test basic stripping and lowercasing."""
    assert clean_value("  Hello World  ") == "hello world"
    assert clean_value("PYTHON") == "python"

def test_clean_value_empty_and_none():
    """Test handling of None and empty strings."""
    assert clean_value("") == ""
    assert clean_value(None) == ""

def test_clean_value_falsy_inputs():
    """Test handling of other falsy Python values."""
    # Current implementation 'if not val: return ""' means these should return ""
    assert clean_value(0) == ""
    assert clean_value(False) == ""
    assert clean_value([]) == ""
    assert clean_value({}) == ""

def test_clean_value_whitespace():
    """Test various whitespace characters."""
    assert clean_value("\n  test\t") == "test"
    assert clean_value("   ") == ""

def test_clean_value_non_string_truthy():
    """Test truthy non-string inputs which should raise AttributeError."""
    with pytest.raises(AttributeError):
        clean_value(123)
    with pytest.raises(AttributeError):
        clean_value([1, 2, 3])
