
import subprocess
import sys
import os
import time

def run_step(script_name, args=[]):
    """Runs a python script and waits for it to finish."""
    print(f"\n[PIPELINE] Starting {script_name}...")
    start_time = time.time()

    cmd = [sys.executable, script_name] + args
    try:
        # Check if file exists first
        if not os.path.exists(script_name):
            print(f"[ERROR] Script {script_name} not found!")
            return False

        result = subprocess.run(cmd, check=True)
        duration = time.time() - start_time
        print(f"[PIPELINE] Finished {script_name} in {duration:.2f} seconds.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {script_name} failed with exit code {e.returncode}.")
        return False
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred running {script_name}: {e}")
        return False

def main():
    print("=======================================================")
    print("   Archaeological Site Classification Pipeline Runner  ")
    print("=======================================================")

    # Define filenames
    raw_data = 'p3_points_export_for_cleaning.csv'
    concatenated_data = 'p3_points_concatenated.csv'
    classified_data = 'p3_points_classified.csv'

    # Check for raw data
    if not os.path.exists(raw_data):
        print(f"[ERROR] Raw data file '{raw_data}' not found. Please place it in this directory.")
        return

    # Step 1: Preprocessing (concatenation)
    # Using process_sites.py which we've designated as the robust preprocessor
    if not run_step('process_sites.py'):
        return

    # Step 2: Classification
    # Passing input and output arguments to classify_sites.py
    if not run_step('classify_sites.py', [concatenated_data, classified_data]):
        return

    # Step 3: Reporting
    # generate_report.py typically takes the classified file as input
    if not run_step('generate_report.py', [classified_data]):
        return

    print("\n=======================================================")
    print("   Pipeline Complete Successfully!                     ")
    print("=======================================================")
    print(f"Outputs generated:")
    print(f"1. {concatenated_data} (Preprocessed Data)")
    print(f"2. {classified_data} (Classified Data)")
    print(f"3. Burned_Rock_Report/ (Report Folder)")

if __name__ == "__main__":
    main()
