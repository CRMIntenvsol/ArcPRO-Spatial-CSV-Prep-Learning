import unittest
import sys
import os

def run_tests():
    """
    Discovers and runs all tests in the 'tests' directory.
    """
    # Ensure the current directory is in sys.path so tests can import the modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    print(f"Running tests from {current_dir}/tests...")

    loader = unittest.TestLoader()
    start_dir = os.path.join(current_dir, 'tests')

    # Discover all tests in the 'tests' directory
    suite = loader.discover(start_dir)

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with non-zero status if tests failed
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
