
import csv
import sys
import os

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

COLUMNS_TO_CONCAT = [
    'type_site', 'explain', 'additional', 'surf_tech', 'map_meth', 'test_meth',
    'exca_meth', 'records', 'materials', 'samples', 'time_occ', 'drainage',
    'soil_desc', 'surf_tex', 'visible', 'env_desc', 'time_desc', 'site_size',
    'basis', 'cult_desc', 'basis_size', 'artifact', 'intact', 'value',
    'invest', 'disc_desc', 'unmatched'
]

def clean_value(val):
    if val is None:
        return ""
    # Replace newlines with spaces and double quotes with single quotes
    return str(val).replace('\r', ' ').replace('\n', ' ').replace('"', "'").strip()

def should_skip(val):
    v = clean_value(val).lower()
    return v in ['no data', 'false', '']

def main():
    print(f"Reading from {INPUT_FILE}...")

    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace', newline='') as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames if reader.fieldnames else []

        missing_cols = [c for c in COLUMNS_TO_CONCAT if c not in fieldnames]
        if missing_cols:
            print(f"Warning: The following columns were not found: {missing_cols}")

        base_fieldnames = [f for f in fieldnames if f != 'Concat_site_variables']
        new_fieldnames = base_fieldnames + ['Concat_site_variables']

        print(f"Writing to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
            writer.writeheader()

            row_count = 0
            for row in reader:
                clean_row = {k: clean_value(v) for k, v in row.items()}

                concat_parts = []
                for col in COLUMNS_TO_CONCAT:
                    if col in clean_row:
                        val = clean_row[col]
                        if not should_skip(val):
                            concat_parts.append(f"{col}: {val};")

                clean_row['Concat_site_variables'] = " ".join(concat_parts)

                # Filter clean_row to only include keys in new_fieldnames
                # This prevents ValueError if row had extra keys not in fieldnames
                output_row = {k: clean_row.get(k, '') for k in new_fieldnames}

                writer.writerow(output_row)
                row_count += 1

                if row_count % 1000 == 0:
                    print(f"Processed {row_count} rows...")

            print(f"Finished processing {row_count} rows.")

if __name__ == "__main__":
    main()
