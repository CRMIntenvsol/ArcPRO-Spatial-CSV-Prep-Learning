import csv
import json
import os
import csv_utils_helpers

# Increase CSV field size limit to handle large fields
csv_utils_helpers.increase_csv_field_size_limit()

DEFAULT_CONFIG_FILE = 'config.json'
INPUT_FILE = 'p3_points_export_for_cleaning.csv'
OUTPUT_FILE = 'p3_points_concatenated.csv'

# Default columns if config is missing
DEFAULT_COLUMNS_TO_CONCAT = [
    'type_site', 'explain', 'additional', 'surf_tech', 'map_meth',
    'test_meth', 'exca_meth', 'records', 'materials', 'samples',
    'time_occ', 'drainage', 'soil_desc', 'surf_tex', 'visible',
    'env_desc', 'time_desc', 'site_size', 'basis', 'cult_desc',
    'basis_size', 'artifact', 'intact', 'value', 'invest',
    'disc_desc', 'unmatched'
]

def load_config(config_path):
    """
    Loads configuration from a JSON file.
    Returns a dictionary with configuration or empty dict if file not found/invalid.
    """
    if not os.path.exists(config_path):
        print(f"Config file {config_path} not found. Using defaults.")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}. Using defaults.")
        return {}
    except Exception as e:
        print(f"Error reading config file: {e}. Using defaults.")
        return {}

def should_skip(val):
    """
    Returns True if the value should be skipped (e.g. 'No Data', 'False', empty).
    """
    v = csv_utils_helpers.clean_value(val, lower=True)
    return v in ['no data', 'false', '']

def main(input_file=None, output_file=None, config_file=DEFAULT_CONFIG_FILE):
    # Load Config
    config = load_config(config_file)

    # Determine Input/Output files (CLI args override config, which overrides defaults)
    input_path = input_file or config.get('input_file') or INPUT_FILE
    output_path = output_file or config.get('output_file') or OUTPUT_FILE
    columns_to_concat = config.get('columns_to_concat', DEFAULT_COLUMNS_TO_CONCAT)
    
    print(f"Reading from {input_path}...")

    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace', newline='') as fin:
            reader = csv.DictReader(fin)
            fieldnames = reader.fieldnames if reader.fieldnames else []

            # Check if all target columns exist
            missing_cols = [c for c in columns_to_concat if c not in fieldnames]
            if missing_cols:
                print(f"Warning: The following columns were not found in the input CSV: {missing_cols}")
            
            # Add the new column to fieldnames
            base_fieldnames = [f for f in fieldnames if f != 'Concat_site_variables']
            new_fieldnames = base_fieldnames + ['Concat_site_variables']

            print(f"Writing to {output_path}...")
            with open(output_path, 'w', encoding='utf-8', newline='') as fout:
                writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
                writer.writeheader()
                
                row_count = 0
                for row in reader:
                    # Clean all fields
                    clean_row = {k: csv_utils_helpers.clean_value(v) for k, v in row.items()}

                    concat_parts = []
                    for col in columns_to_concat:
                        if col in clean_row:
                            val = clean_row[col]
                            if not should_skip(val):
                                concat_parts.append(f"{col}: {val};")

                    clean_row['Concat_site_variables'] = " ".join(concat_parts)
                    writer.writerow(clean_row)
                    row_count += 1

                    if row_count % 1000 == 0:
                        print(f"Processed {row_count} rows...")
                
                print(f"Finished processing {row_count} rows.")
                
    except FileNotFoundError:
        print(f"Error: Input file '{input_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Concatenate site variables from a CSV file.")
    parser.add_argument("--input", "-i", help="Path to the input CSV file.")
    parser.add_argument("--output", "-o", help="Path to the output CSV file.")
    parser.add_argument("--config", "-c", default=DEFAULT_CONFIG_FILE, help="Path to the JSON config file.")
    args = parser.parse_args()

    main(input_file=args.input, output_file=args.output, config_file=args.config)
