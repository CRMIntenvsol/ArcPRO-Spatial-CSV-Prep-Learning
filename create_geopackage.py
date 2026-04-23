import geopandas as gpd
import pandas as pd
import argparse
import os

def create_geopackage(input_csv: str, output_gpkg: str, lat_col: str = 'Northing', lon_col: str = 'Easting'):
    print(f"Reading {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Assuming Northing/Easting have been converted or are the main spatial cols to map
    # We will try to map using valid coords.

    if lat_col not in df.columns or lon_col not in df.columns:
        print(f"Columns {lat_col} and {lon_col} not found in {input_csv}. Using generic coordinates if missing.")
        df['geometry'] = None
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
    else:
        # Filter out rows with invalid/missing coords
        df_valid = df.dropna(subset=[lat_col, lon_col])
        df_invalid = df[df[lat_col].isna() | df[lon_col].isna()]

        # Create GeoDataFrame
        # Important: determine the CRS. We'll assume the converted coordinates might be in lat/lon WGS84,
        # or we might need to rely on the convert_coordinates.py outputs.
        # For this script, let's just create points.
        gdf_valid = gpd.GeoDataFrame(
            df_valid,
            geometry=gpd.points_from_xy(df_valid[lon_col], df_valid[lat_col])
        )
        # Combine back
        gdf_invalid = gpd.GeoDataFrame(df_invalid, geometry=[None]*len(df_invalid))
        gdf = pd.concat([gdf_valid, gdf_invalid])

    print(f"Writing to {output_gpkg}...")
    # SQLite/GeoPackage can't handle all column types cleanly sometimes, convert complex types to string
    for col in gdf.columns:
        if gdf[col].dtype == 'object':
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(output_gpkg, driver="GPKG")
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="p3_points_concatenated.csv")
    parser.add_argument("--output", default="archaeology_sites.gpkg")
    args = parser.parse_args()

    create_geopackage(args.input, args.output)
