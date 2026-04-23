import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import subprocess
import argparse
from pathlib import Path

def run_step(script_name, description, *args):
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"Executing: python {script_name} {' '.join(args)}")
    print(f"{'='*60}\n")

    cmd = [sys.executable, script_name] + list(args)
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n[!] Error: {script_name} failed with exit code {result.returncode}")
        print("Pipeline halted.")
        sys.exit(result.returncode)

    print(f"\n[+] {script_name} completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Master Pipeline for Archaeological Site Processing & LLM Classification")
    parser.add_argument("--api-key", required=False, help="Anthropic API Key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--limit", type=int, default=None, help="Process only N rows (for testing)")
    parser.add_argument("--skip-prep", action="store_true", help="Skip CSV concatenation and GeoPackage creation (resume LLM only)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Anthropic API key is required. Pass via --api-key or set ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)

    # Make API key available to subprocesses
    os.environ["ANTHROPIC_API_KEY"] = api_key

    print("\nStarting Master Archaeological Data Pipeline...")

    gpkg_path = "archaeology.gpkg"

    if not args.skip_prep:
        # Step 1: Process CSV
        run_step("process_sites.py", "Data Prep & Concatenation")

        # Step 2: Create GeoPackage
        run_step("migrate_to_gpkg.py", "GeoPackage Spatial Migration")
    else:
        print(f"\n[*] Skipping data prep. Using existing database...")

    if not os.path.exists(gpkg_path):
        print(f"\n[!] Error: {gpkg_path} was not created successfully.")
        sys.exit(1)

    # Step 3: Run LLM
    llm_args = []
    if args.limit:
        llm_args.extend(["--limit", str(args.limit)])
    run_step("run_llm.py", "LLM Classification Analysis", *llm_args)

    # Step 4: Generate Report
    run_step("generate_report.py", "Final Reporting & Visualization")

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE!")
    print(f"Data saved to {gpkg_path}")
    print("Reports generated in Burned_Rock_Report/")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
