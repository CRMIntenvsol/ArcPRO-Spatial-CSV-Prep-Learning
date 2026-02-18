# Archeological Site Classification Pipeline

This repository contains a set of Python scripts to process, classify, and analyze archeological site data from CSV files. It uses text analysis to infer site types (e.g., Burned Rock Middens, Hearths) and time periods (e.g., Late Prehistoric, Archaic) based on artifact assemblages and geological context.

## Prerequisites

1.  **Python 3.x**: Ensure Python is installed and added to your system PATH.
2.  **Dependencies**: The core pipeline uses standard Python libraries (`csv`, `sys`, `re`, `json`, `os`, `difflib`, `collections`, `subprocess`, `argparse`).
    *   *Optional:* `matplotlib` is used by `generate_report.py` for creating charts. Install it via:
        ```bash
        pip install matplotlib
        ```
    *   *Optional:* `pdfplumber`, `pytesseract`, `Pillow`, `tqdm` are required only if you want to use the `batch_pdf_to_md.py` tool to convert new PDF documents.

## Setup

1.  Place your raw data file named `p3_points_export_for_cleaning.csv` in the same directory as the scripts.
2.  Ensure `extracted_artifacts.json` is present (this is the database of artifact types).

## Quick Start (Run Everything)

To run the entire workflow (Preprocessing -> Classification -> Reporting) in one go, execute:

```bash
python run_pipeline.py
```

This script will:
1.  **Preprocess:** Read `p3_points_export_for_cleaning.csv` and create `p3_points_concatenated.csv` by combining relevant text columns.
2.  **Classify:** Read `p3_points_concatenated.csv`, apply classification rules, and save results to `p3_points_classified.csv`.
3.  **Report:** specific statistics from the classified data and generate a text report in the `Burned_Rock_Report` folder.

## Detailed Steps (Manual Execution)

If you prefer to run steps individually:

### 1. Preprocessing
Combines text fields from the raw export into a single searchable column.

```bash
python process_sites.py [input_file] [output_file]
```
*   Defaults: `process_sites.py p3_points_export_for_cleaning.csv p3_points_concatenated.csv`

### 2. Classification
Analyzes the text to identify site types and time periods.

```bash
python classify_sites.py [input_file] [output_file]
```
*   Defaults: `classify_sites.py p3_points_concatenated.csv p3_points_classified.csv`

### 3. Reporting
Generates summary statistics and charts.

```bash
python generate_report.py [input_file]
```
*   Defaults: `generate_report.py p3_points_classified.csv`

## Helper Tools

### Compare with Expert Data
If you have a dataset classified by an expert, you can verify the machine's accuracy.

```bash
python compare_results.py expert_classified.csv p3_points_classified.csv comparison_report.txt
```

### PDF to Markdown
To add more knowledge to the system, you can convert PDF reports to text.

```bash
python batch_pdf_to_md.py
```
*   Follow the on-screen prompts to select input/output directories.

### Mining Relationships
To analyze text for new soil-site relationships.

```bash
python scan_markdown.py
python analyze_relationships.py
```

## Logic Overview

*   **Time Periods:** Determined by looking up diagnostic artifacts (e.g., "Perdiz", "Gary") in `extracted_artifacts.json`.
*   **Site Context:** Inferred from geological keywords (e.g., "Deep Alluvium" -> Paleoindian potential) using rules defined in `classify_sites.py`.
*   **Site Type:** Determined by keywords for "Burned Rock" (Class 1), "Hearths" (Class 2), and "Middens/Ovens" (Class 3).
