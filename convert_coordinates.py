import csv
import sys
from pyproj import Transformer

# Define coordinate systems
CRS_WGS84 = "EPSG:4326"
CRS_UTM14N = "EPSG:32614"          # UTM Zone 14N (WGS84)
CRS_SP_NC_FT = "EPSG:2276"         # NAD83 / Texas North Central (ftUS)
CRS_SP_NC_M = "EPSG:32138"         # NAD83 / Texas North Central (m)

INPUT_FILE = "p3_points_export_for_cleaning.csv"
OUTPUT_FILE = "p3_points_with_lat_long.csv"

def setup_transformers():
    try:
        # always_xy=True ensures (lon, lat) output order for WGS84, and (easting, northing) input
        trans_utm = Transformer.from_crs(CRS_UTM14N, CRS_WGS84, always_xy=True)
        trans_sp_ft = Transformer.from_crs(CRS_SP_NC_FT, CRS_WGS84, always_xy=True)
        trans_sp_m = Transformer.from_crs(CRS_SP_NC_M, CRS_WGS84, always_xy=True)
        return trans_utm, trans_sp_ft, trans_sp_m
    except Exception as e:
        print(f"Error initializing coordinate transformers: {e}")
        sys.exit(1)

def convert_coordinates(northing, easting, transformers):
    trans_utm, trans_sp_ft, trans_sp_m = transformers
    lon, lat = None, None

    # Heuristic detection logic based on typical value ranges for Texas

    # 1. UTM Zone 14N (Meters)
    # Northing typically ~3,000,000 - 4,000,000
    # Easting typically ~200,000 - 800,000
    if 2_500_000 <= northing <= 4_500_000 and 100_000 <= easting <= 900_000:
        lon, lat = trans_utm.transform(easting, northing)

    # 2. State Plane North Central (US Feet)
    # Northing typically ~6,000,000 - 8,000,000
    # Easting typically ~1,500,000 - 3,000,000
    elif 5_000_000 <= northing <= 9_000_000 and 1_000_000 <= easting <= 4_000_000:
        lon, lat = trans_sp_ft.transform(easting, northing)

    # 3. State Plane North Central (Meters)
    # Northing typically ~1,800,000 - 2,500,000
    # Easting typically ~400,000 - 900,000
    elif 1_500_000 <= northing <= 2_500_000 and 300_000 <= easting <= 1_000_000:
        lon, lat = trans_sp_m.transform(easting, northing)

    return lat, lon

def main():
    print("Initializing transformers...")
    transformers = setup_transformers()

    print(f"Reading from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace', newline='') as fin:
            reader = csv.DictReader(fin)
            fieldnames = reader.fieldnames if reader.fieldnames else []

            # Prepare output fieldnames
            new_fieldnames = fieldnames + ['Latitude', 'Longitude']

            print(f"Writing to {OUTPUT_FILE}...")
            with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as fout:
                writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
                writer.writeheader()

                count = 0
                converted_count = 0

                for row in reader:
                    n_str = row.get('Northing', '').strip()
                    e_str = row.get('Easting', '').strip()

                    lat_str, lon_str = "", ""

                    if n_str and e_str and n_str.lower() != 'no data' and e_str.lower() != 'no data':
                        try:
                            northing = float(n_str)
                            easting = float(e_str)

                            lat, lon = convert_coordinates(northing, easting, transformers)

                            if lat is not None and lon is not None:
                                # Validate logical bounds for Texas/USA to filter out bad conversions
                                if 24 <= lat <= 38 and -108 <= lon <= -93:
                                    lat_str = f"{lat:.6f}"
                                    lon_str = f"{lon:.6f}"
                                    converted_count += 1
                        except ValueError:
                            pass # Skip conversion for non-numeric values

                    row['Latitude'] = lat_str
                    row['Longitude'] = lon_str
                    writer.writerow(row)
                    count += 1

                    if count % 1000 == 0:
                        print(f"Processed {count} rows...")

                print(f"Finished. Processed {count} rows. Converted {converted_count} coordinates.")

    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_FILE}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
