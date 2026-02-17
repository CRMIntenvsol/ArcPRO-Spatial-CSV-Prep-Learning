
import unittest
import sys
import os

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

if __name__ == '__main__':
    unittest.main()
