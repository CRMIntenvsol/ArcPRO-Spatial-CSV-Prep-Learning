import geopandas as gpd
import pandas as pd
import argparse
import os

def create_geopackage(input_csv: str, output_gpkg: str):
    print(f"Reading {input_csv}...")
    try:
        df = pd.read_csv(input_csv, dtype=str) # Read all as string to prevent type issues
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Check for wgs_lat and wgs_long
    if 'wgs_lat' in df.columns and 'wgs_long' in df.columns:
        print("Using wgs_lat and wgs_long for geometry (WGS84 EPSG:4326).")
        # Ensure they are numeric
        df['wgs_lat_num'] = pd.to_numeric(df['wgs_lat'], errors='coerce')
        df['wgs_long_num'] = pd.to_numeric(df['wgs_long'], errors='coerce')

        df_valid = df.dropna(subset=['wgs_lat_num', 'wgs_long_num'])
        df_invalid = df[df['wgs_lat_num'].isna() | df['wgs_long_num'].isna()]

        gdf_valid = gpd.GeoDataFrame(
            df_valid,
            geometry=gpd.points_from_xy(df_valid['wgs_long_num'], df_valid['wgs_lat_num']),
            crs="EPSG:4326"
        )
        gdf_invalid = gpd.GeoDataFrame(df_invalid, geometry=[None]*len(df_invalid), crs="EPSG:4326")
        gdf = pd.concat([gdf_valid, gdf_invalid])

        # Drop the temporary numeric columns
        gdf = gdf.drop(columns=['wgs_lat_num', 'wgs_long_num'])

    else:
        print("Warning: wgs_lat and wgs_long not found. Creating geometry-less GeoPackage.")
        gdf = gpd.GeoDataFrame(df, geometry=[None]*len(df))

    # Add columns for LLM processing state
    gdf['llm_processed'] = 'False'
    gdf['original_classification'] = ''
    gdf['learned_classification'] = ''
    gdf['learned_reasoning'] = ''

    gdf['br_presence'] = ''
    gdf['br_reasoning'] = ''
    gdf['bc_presence'] = ''
    gdf['bc_reasoning'] = ''
    gdf['typology_presence'] = ''
    gdf['typology_reasoning'] = ''

    gdf['final_classification'] = ''
    gdf['disagreement_reasoning'] = ''

    print(f"Writing to {output_gpkg}...")
    # GeoPackage creation
    try:
        gdf.to_file(output_gpkg, driver="GPKG")
        print("GeoPackage successfully created!")
    except Exception as e:
        print(f"Error writing GeoPackage: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="p3_points_concatenated.csv")
    parser.add_argument("--output", default="archaeology.gpkg")
    args = parser.parse_args()

    create_geopackage(args.input, args.output)
