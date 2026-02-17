import csv
import csv_utils_helpers

# Increase CSV field size limit to handle large fields
csv_utils_helpers.increase_csv_field_size_limit()

INPUT_FILE = '/tmp/file_attachments/Analysis/p3_points_export_for_cleaning.csv'
OUTPUT_FILE = '/tmp/p3_points_concatenated.csv'

COLUMNS_TO_CONCAT = [
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

def should_skip(val):
    """
    Returns True if the value should be skipped (e.g. 'No Data', 'False', empty).
    """
    v = csv_utils_helpers.clean_value(val, lower=True)
    return v in ['no data', 'false', '']

def main():
    print(f"Reading from {INPUT_FILE}...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace', newline='') as fin:
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
        
        print(f"Writing to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
            writer.writeheader()
            
            row_count = 0
            for row in reader:
                # Clean all fields in the row to ensure no newlines exist in the output
                clean_row = {k: csv_utils_helpers.clean_value(v) for k, v in row.items()}
                
                concat_parts = []
                for col in COLUMNS_TO_CONCAT:
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

if __name__ == "__main__":
    main()
