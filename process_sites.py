import csv
import csv_utils
import sys
import json
import argparse
import os

# Increase CSV field size limit to handle large fields
csv_utils.increase_field_size_limit()

DEFAULT_INPUT_FILE = '/tmp/file_attachments/Analysis/p3_points_export_for_cleaning.csv'
DEFAULT_OUTPUT_FILE = '/tmp/p3_points_concatenated.csv'
INPUT_FILE = 'p3_points_export_for_cleaning.csv'
OUTPUT_FILE = 'p3_points_concatenated.csv'

DEFAULT_COLUMNS_TO_CONCAT = [
    'type_site',
    'explain',
    'additional',
    'surf_tech',
    'map_meth',
    'test_meth',
    'exca_meth',
    'records',
    'materials',
    'samples',
    'time_occ',
    'drainage',
    'soil_desc',
    'surf_tex',
    'visible',
    'env_desc',
    'time_desc',
    'site_size',
    'basis',
    'cult_desc',
    'basis_size',
    'artifact',
    'intact',
    'value',
    'invest',
    'disc_desc',
    'unmatched'
]

def load_config(config_path):
    """
    Load configuration from a JSON file.
    Returns a dictionary with configuration or None if loading fails.
    """
    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_path}: {e}")
        return None

def clean_value(val):
    if val is None:
        return ""
    # Replace newlines with spaces and double quotes with single quotes to ensure robust CSV structure
    return str(val).replace('\r', ' ').replace('\n', ' ').replace('"', "'").strip()

def should_skip(val):
    """
    Returns True if the value should be skipped (e.g. 'No Data', 'False', empty).
    """
    v = clean_value(val).lower()
    return v in ['no data', 'false', '']

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process site data.')
    parser.add_argument('--input', '-i', default='p3_points_export_for_cleaning.csv', help='Input CSV file path')
    parser.add_argument('--output', '-o', default='p3_points_concatenated.csv', help='Output CSV file path')
    return parser.parse_args()

def main():
    parser = argparse.ArgumentParser(description='Process site data and concatenate columns.')
    parser.add_argument('--config', type=str, default='config.json', help='Path to configuration file')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    
    if config:
        print(f"Loaded configuration from {args.config}")
        input_file = config.get('input_file', DEFAULT_INPUT_FILE)
        output_file = config.get('output_file', DEFAULT_OUTPUT_FILE)
        columns_to_concat = config.get('columns_to_concat', DEFAULT_COLUMNS_TO_CONCAT)
    else:
        print(f"Configuration file {args.config} not found or invalid. Using defaults.")
        input_file = DEFAULT_INPUT_FILE
        output_file = DEFAULT_OUTPUT_FILE
        columns_to_concat = DEFAULT_COLUMNS_TO_CONCAT

    print(f"Reading from {input_file}...")

    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as fin:
            reader = csv.DictReader(fin)
            fieldnames = reader.fieldnames if reader.fieldnames else []
    args = parse_arguments()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    print(f"Reading from {args.input}...")
    
    with open(args.input, 'r', encoding='utf-8', errors='replace', newline='') as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames if reader.fieldnames else []
        
        # Check if all target columns exist
        missing_cols = [c for c in COLUMNS_TO_CONCAT if c not in fieldnames]
        if missing_cols:
            print(f"Warning: The following columns were not found in the input CSV: {missing_cols}")
            # We will proceed but skip missing columns for concatenation
        
        # Add the new column to fieldnames, ensuring no duplicates if re-running
        base_fieldnames = [f for f in fieldnames if f != 'Concat_site_variables']
        new_fieldnames = base_fieldnames + ['Concat_site_variables']
        
        print(f"Writing to {args.output}...")
        with open(args.output, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
            writer.writeheader()
            
            # Check if all target columns exist
            missing_cols = [c for c in columns_to_concat if c not in fieldnames]
            if missing_cols:
                print(f"Warning: The following columns were not found in the input CSV: {missing_cols}")
                # We will proceed but skip missing columns for concatenation

            # Add the new column to fieldnames, ensuring no duplicates if re-running
            base_fieldnames = [f for f in fieldnames if f != 'Concat_site_variables']
            new_fieldnames = base_fieldnames + ['Concat_site_variables']

            print(f"Writing to {output_file}...")
            with open(output_file, 'w', encoding='utf-8', newline='') as fout:
                writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
                writer.writeheader()
                
                row_count = 0
                for row in reader:
                    # Clean all fields in the row to ensure no newlines exist in the output
                    clean_row = {k: clean_value(v) for k, v in row.items()}

                    concat_parts = []
                    for col in columns_to_concat:
                        if col in clean_row:
                            val = clean_row[col]
                            if not should_skip(val):
                                # Format: "Header: Value;"
                                # Value is already cleaned of newlines
                                concat_parts.append(f"{col}: {val};")

                    clean_row['Concat_site_variables'] = " ".join(concat_parts)
                    writer.writerow(clean_row)
                    row_count += 1

                    if row_count % 1000 == 0:
                        print(f"Processed {row_count} rows...")
                
                print(f"Finished processing {row_count} rows.")
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
