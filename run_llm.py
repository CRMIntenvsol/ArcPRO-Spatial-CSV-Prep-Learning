import argparse
import geopandas as gpd
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from llm_classifier import LLMClassifier
import time

def process_geopackage(gpkg_path: str, api_key: str, limit: int = None):
    print(f"Connecting to {gpkg_path}...")

    if not os.path.exists(gpkg_path):
        print(f"Error: {gpkg_path} not found.")
        sys.exit(1)

    llm = LLMClassifier(api_key=api_key)

    try:
        gdf = gpd.read_file(gpkg_path)
    except Exception as e:
        print(f"Error reading GeoPackage: {e}")
        sys.exit(1)

    unprocessed_indices = gdf.index[gdf['llm_processed'] != 'True'].tolist()

    if limit:
        unprocessed_indices = unprocessed_indices[:limit]

    total = len(unprocessed_indices)
    print(f"Found {total} unprocessed sites.")

    if total == 0:
        print("All sites processed!")
        return

    count = 0
    save_interval = 500 # Save to disk every 500 rows

    for idx in unprocessed_indices:
        row = gdf.loc[idx]
        trinomial = row.get('trinomial')
        text = row.get('Concat_site_variables', '')

        if not text or str(text) == 'nan':
            gdf.at[idx, 'llm_processed'] = 'True'
            continue

        print(f"Processing {trinomial} ({count+1}/{total})...")

        result = llm.classify(text)

        if result:
            expert_class = row.get('expert_refined_context')
            if expert_class and str(expert_class).strip() and str(expert_class).lower() != 'nan':
                final_class = f"Expert: {expert_class}"

                learned = str(result.get('learned_classification', '')).lower()
                expert_str = str(expert_class).lower()

                disagreement = ""
                if 'historic' in learned and 'prehistoric' in expert_str and 'historic' not in expert_str:
                    disagreement = "LLM inferred Historic but Expert explicitly assigned Prehistoric."
                elif 'prehistoric' in learned and 'historic' in expert_str and 'prehistoric' not in expert_str:
                    disagreement = "LLM inferred Prehistoric but Expert explicitly assigned Historic."
            else:
                final_class = result.get('learned_classification', 'Unknown')
                disagreement = ""

            gdf.at[idx, 'llm_processed'] = 'True'
            gdf.at[idx, 'original_classification'] = result.get('original_classification', '')
            gdf.at[idx, 'learned_classification'] = result.get('learned_classification', '')
            gdf.at[idx, 'learned_reasoning'] = result.get('learned_reasoning', '')
            gdf.at[idx, 'br_presence'] = result.get('br_presence', '')
            gdf.at[idx, 'br_reasoning'] = result.get('br_reasoning', '')
            gdf.at[idx, 'bc_presence'] = result.get('bc_presence', '')
            gdf.at[idx, 'bc_reasoning'] = result.get('bc_reasoning', '')
            gdf.at[idx, 'typology_presence'] = result.get('typology_presence', '')
            gdf.at[idx, 'typology_reasoning'] = result.get('typology_reasoning', '')
            gdf.at[idx, 'final_classification'] = final_class
            gdf.at[idx, 'disagreement_reasoning'] = disagreement

            print(f"  -> Success: {result.get('learned_classification')}")

            time.sleep(0.5)
        else:
            print(f"Failed to process {trinomial}. Skipping to next...")

        count += 1

        if count % save_interval == 0:
            print(f"Saving progress to {gpkg_path}...")
            gdf.to_file(gpkg_path, driver="GPKG")

    print(f"Final save to {gpkg_path}...")
    gdf.to_file(gpkg_path, driver="GPKG")
    print("Done processing!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify site data in GeoPackage using LLM.")
    parser.add_argument("--gpkg", default="archaeology.gpkg", help="Path to the GeoPackage file")
    parser.add_argument("--api-key", required=False, help="Anthropic API Key")
    parser.add_argument("--limit", type=int, default=None, help="Process only N rows (for testing)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Anthropic API key is required.")
        sys.exit(1)

    process_geopackage(args.gpkg, api_key, args.limit)
