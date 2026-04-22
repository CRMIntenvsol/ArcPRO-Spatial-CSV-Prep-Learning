# Archaeological Site LLM Classification Pipeline

This repository contains a robust pipeline that processes raw archaeological site data, converts it into a spatial GeoPackage database, and uses Anthropic's Claude LLM to intelligently classify the sites based on complex text descriptions.

## Prerequisites

Before running the pipeline, ensure you have the required dependencies and an Anthropic API key.

```bash
pip install pandas geopandas shapely anthropic matplotlib
export ANTHROPIC_API_KEY="your-api-key-here"
```

## How to Run

We have combined the entire 4-step pipeline into a single Master Orchestrator script for maximum efficiency.

To run the entire process end-to-end (Data Prep -> GeoPackage Creation -> LLM Classification -> Reporting), simply run:

```bash
python run_pipeline.py
```

### Safety and Resuming
Because processing thousands of records with an LLM takes time and API credits, the pipeline safely saves its progress to the database (`archaeology.gpkg`) every 500 rows.

If your computer turns off, you lose internet, or you hit an API limit halfway through, **do not worry**. Simply run the pipeline again, and add the `--skip-prep` flag. It will automatically detect where the LLM left off in the database and resume processing without losing any data!

```bash
python run_pipeline.py --skip-prep
```

### Testing a Small Batch
If you just want to test the LLM on the first 5 rows to make sure everything looks good before doing the whole dataset:

```bash
python run_pipeline.py --limit 5
```

---

## Under the Hood: The 4 Steps

If you prefer to run the scripts manually one-by-one, here is what `run_pipeline.py` is doing behind the scenes:

### 1. Pre-Process Data (`process_sites.py`)
Reads your raw data and intelligently concatenates 30+ descriptive fields into a single column (`Concat_site_variables`). It preserves the context of each field (e.g., `water: Trinity River | soil_desc: Sandy loam`) so the LLM understands exactly what the data means.

### 2. Migrate to Database (`migrate_to_gpkg.py`)
Takes the processed CSV and converts it into a robust SQLite-backed spatial database (GeoPackage). It uses the `wgs_lat` and `wgs_long` coordinates to map the points into WGS84 (EPSG:4326), bypassing UTM/State Plane zone conflicts.

### 3. Run LLM Classification (`run_llm.py`)
Connects to Anthropic's API to read the concatenated text for each site and extract structured JSON classifications.
- It infers time periods, checks for Burned Rock/Clay, and typologies.
- It automatically cross-validates its own reasoning.
- It compares its findings against the Expert classifications.

### 4. Generate Reports (`generate_report.py`)
Reads the fully classified GeoPackage and generates summary statistics, charts, and a detailed text report highlighting LLM vs Expert disagreements.
