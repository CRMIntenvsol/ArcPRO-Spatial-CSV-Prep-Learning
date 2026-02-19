import csv
import sys
import os
import argparse

# Increase CSV field size limit to handle large fields
max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int/10)

INPUT_FILE = 'p3_points_export_for_cleaning.csv'
OUTPUT_FILE = 'p3_points_concatenated.csv'
DEFAULT_EXPERT_FILE = 'expert_classified.csv'

COLUMNS_TO_CONCAT = [
    'type_site', 'sitename', 'explain', 'additional', 'observe', 'surface', 'surf_tech',
    'map_meth', 'test_meth', 'exca_meth', 'records', 'materials', 'materials_collected',
    'samples', 'time_occ', 'desc_loc', 'drainage', 'soil_desc', 'surf_tex', 'visible',
    'env_desc', 'time_desc', 'site_size', 'basis', 'cult_desc', 'basis_size',
    'artifact', 'intact', 'value', 'invest', 'disc_desc', 'unmatched'
]

def clean_value(val):
    if val is None:
        return ""
    # Replace newlines with spaces and double quotes with single quotes
    return str(val).replace('\r', ' ').replace('\n', ' ').replace('"', "'").strip()

def normalize_trinomial(val):
    """Normalize trinomial for robust matching: uppercase and stripped of whitespace."""
    if val is None:
        return ""
    return str(val).upper().strip()

def should_skip(val):
    v = clean_value(val).lower()
    return v in ['no data', 'false', '']

def load_expert_data(expert_file):
    expert_data = {}
    if not expert_file:
        return expert_data
    
    print(f"Loading expert classifications from {expert_file}...")
    try:
        with open(expert_file, 'r', encoding='utf-8', errors='replace', newline='') as f:
            reader = csv.DictReader(f)
            count = 0
            examples = []
            for row in reader:
                raw_tri = row.get('trinomial', '')
                trinomial = normalize_trinomial(raw_tri)
                if trinomial:
                    expert_data[trinomial] = {
                        'refined_context': clean_value(row.get('refined_context')),
                        'citation': clean_value(row.get('citation'))
                    }
                    count += 1
                    if count <= 5:
                        examples.append(f"'{raw_tri}' -> '{trinomial}'")

            print(f"Loaded {count} expert records.")
            if examples:
                print(f"Sample Expert Trinomials: {', '.join(examples)}")

    except FileNotFoundError:
        print(f"Warning: Expert file '{expert_file}' not found. Skipping expert data integration.")
    except Exception as e:
        print(f"Error loading expert file: {e}")

    return expert_data

def main():
    parser = argparse.ArgumentParser(description="Process site data and concatenate columns.")
    parser.add_argument('--input', '-i', default=INPUT_FILE, help='Input CSV file path')
    parser.add_argument('--output', '-o', default=OUTPUT_FILE, help='Output CSV file path')
    parser.add_argument('--expert-file', '-e', help='Path to expert classified CSV file. Defaults to expert_classified.csv if present.')
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    expert_file = args.expert_file

    # Automatic default logic for expert file
    if not expert_file:
        if os.path.exists(DEFAULT_EXPERT_FILE):
            expert_file = DEFAULT_EXPERT_FILE
            print(f"Found default expert file: {expert_file}")
        else:
            print(f"Note: No expert file specified and '{DEFAULT_EXPERT_FILE}' not found. Proceeding without expert classifications.")

    print(f"Reading from {input_file}...")

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    expert_data = load_expert_data(expert_file)
    matched_expert_trinomials = set()

    with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames if reader.fieldnames else []
        
        missing_cols = [c for c in COLUMNS_TO_CONCAT if c not in fieldnames]
        if missing_cols:
            print(f"Warning: The following columns were not found: {missing_cols}")

        # Determine new fieldnames
        base_fieldnames = [f for f in fieldnames if f != 'Concat_site_variables']
        new_fieldnames = base_fieldnames + ['Concat_site_variables']
        
        # Add expert columns if not present
        if 'refined_context' not in new_fieldnames:
            new_fieldnames.append('refined_context')
        if 'citation' not in new_fieldnames:
            new_fieldnames.append('citation')

        print(f"Writing to {output_file}...")
        with open(output_file, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
            writer.writeheader()
            
            row_count = 0
            input_examples = []

            for row in reader:
                clean_row = {k: clean_value(v) for k, v in row.items()}
                raw_tri = clean_row.get('trinomial', '')
                trinomial = normalize_trinomial(raw_tri)
                
                if row_count < 5 and raw_tri:
                    input_examples.append(f"'{raw_tri}' -> '{trinomial}'")

                # Check for expert match
                expert_info = expert_data.get(trinomial)
                if expert_info:
                    matched_expert_trinomials.add(trinomial)
                    clean_row['refined_context'] = expert_info['refined_context']
                    clean_row['citation'] = expert_info['citation']
                
                concat_parts = []
                for col in COLUMNS_TO_CONCAT:
                    if col in clean_row:
                        val = clean_row[col]
                        if not should_skip(val):
                            concat_parts.append(f"{col}: {val};")
                
                # Append refined_context to Concat_site_variables if it exists
                if expert_info and expert_info['refined_context']:
                     concat_parts.append(f"refined_context: {expert_info['refined_context']};")

                clean_row['Concat_site_variables'] = " ".join(concat_parts)
                
                # Filter clean_row to only include keys in new_fieldnames
                output_row = {k: clean_row.get(k, '') for k in new_fieldnames}
                
                writer.writerow(output_row)
                row_count += 1

                if row_count % 1000 == 0:
                    print(f"Processed {row_count} rows...")

            if input_examples:
                print(f"Sample Input Trinomials: {', '.join(input_examples)}")

            print(f"Finished processing {row_count} rows.")

            if expert_data:
                print(f"Total Expert Matches Found: {len(matched_expert_trinomials)}")

                missing_matches = set(expert_data.keys()) - matched_expert_trinomials
                if missing_matches:
                    print("\nMISSING MATCHES REPORT")
                    print("======================")
                    print(f"The following {len(missing_matches)} expert trinomials were NOT found in the input file:")
                    for missing in sorted(list(missing_matches)):
                        print(f" - {missing}")
                    print("======================\n")
                elif len(matched_expert_trinomials) == 0:
                    print("WARNING: Expert file loaded, but NO matches were found. Check your trinomial formats in both files.")

if __name__ == "__main__":
    main()
