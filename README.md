# Archaeological Site Data Processing Pipeline

This repository contains a set of Python scripts for processing, classifying, and analyzing archaeological site data (specifically burned rock features) from CSV exports.

## Overview

The pipeline consists of three main stages:
1.  **Data Cleaning & Preparation:** Concatenating relevant text fields and standardizing data format.
2.  **Classification:** Applying keyword-based logic and exclusion rules to categorize sites (e.g., Hearth vs. Oven vs. Scatter).
3.  **Reporting:** Generating statistical summaries and visualizations.

## Scripts

### 1. `process_sites.py`
**Purpose:** Prepares the raw data for classification.
-   **Input:** `p3_points_export_for_cleaning.csv` (default path in code)
-   **Output:** `p3_points_concatenated.csv`
-   **Function:**
    -   Reads the raw export.
    -   Concatenates multiple descriptive columns (e.g., `explain`, `materials`, `desc_loc`) into a single `Concat_site_variables` field.
    -   Cleans text by removing newlines and normalizing quotes.

### 2. `classify_sites.py`
**Purpose:** Classifies sites based on the concatenated text descriptions.
-   **Input:** `p3_points_concatenated.csv`
-   **Output:** `p3_points_classified.csv`
-   **Function:**
    -   **Class 1:** Burned Rock Scatters
    -   **Class 2:** Hearths (requires rock context)
    -   **Class 3:** Earth Ovens / Middens
    -   **Burned Clay:** Detects presence of burned clay.
    -   **Time Period:** Infers time periods based on artifact keywords (using `extracted_artifacts.json`) and specific terms.
    -   Includes logic for typo correction, negation handling (e.g., "no hearths"), and context exclusion (e.g., "microwave oven").

### 3. `generate_report.py`
**Purpose:** Analyzes the classified data and produces a report.
-   **Input:** `p3_points_classified.csv`
-   **Output:** `Burned_Rock_Report/` directory containing text reports and charts.
-   **Function:**
    -   Calculates statistics for each class and time period.
    -   Generates a `Burned_Rock_Analysis_Report.txt` summary.
    -   Creates visualizations (Bar charts, Pie charts) if `matplotlib` is installed.

### 4. `run_tests.py`
**Purpose:** Runs the unit test suite to ensure code reliability.
-   **Function:** Discovers and runs all tests in the `tests/` directory.

## Execution Order

To run the full pipeline:

1.  **Run Tests (Optional but Recommended):**
    ```bash
    python run_tests.py
    ```
    Ensure all tests pass before processing data.

2.  **Process Data:**
    ```bash
    python process_sites.py
    ```

3.  **Classify Sites:**
    ```bash
    python classify_sites.py
    ```

4.  **Generate Report:**
    ```bash
    python generate_report.py
    ```

## Testing

The repository includes a `tests/` directory containing unit tests for key utility functions, particularly `clean_value`, which is critical for consistent data processing across all scripts.

To run the tests manually:
```bash
python run_tests.py
```
Or using the standard library module:
```bash
python -m unittest discover tests
```
