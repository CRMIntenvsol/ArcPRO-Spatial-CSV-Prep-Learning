import csv
import sys
import os
import shutil
from collections import Counter
import csv_utils_helpers
import csv_utils

# Try to import plotting libraries (standard in ArcPro/Anaconda)
try:
    import matplotlib.pyplot as plt
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Warning: matplotlib not found. Charts will not be generated.")

# Increase CSV field size limit for Windows/Large fields
csv_utils_helpers.increase_csv_field_size_limit()

DEFAULT_INPUT_FILE = 'p3_points_classified.csv'
REPORT_DIR = 'Analysis_Reports'
SUBFOLDERS = ['Burned_Rock', 'Burned_Clay', 'Cultural_Typology', 'Soils']

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def analyze_data(input_file):
    print(f"Reading data from {input_file}...")
    
    stats = {
        'total': 0,
        # Burned Rock
        'c1': 0, 'c2': 0, 'c3': 0,
        'c1_only': 0, 'c2_only': 0, 'c3_only': 0,
        'prehistoric': 0,
        'c3_prehistoric': 0,
        'c3_historic_only': 0,

        # Burned Clay
        'burned_clay': 0,
        'burned_clay_only': 0,
        'bc_class_1': 0, # Keyword match
        'bc_class_2': 0, # Artifact/feature match
        'bc_with_c1': 0,
        'bc_with_c2': 0,
        'bc_with_c3': 0,
        'bc_prehistoric': 0,

        # Cultural Typology
        'caddo': 0,
        'henrietta': 0,
        'overlap': 0,

        # Contexts
        'time_periods': Counter(),
        'soil_contexts': Counter()
    }
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as fin:
            reader = csv.DictReader(fin)
            
            for row in reader:
                stats['total'] += 1
                
                # Check Booleans case-insensitively for robustness
                c1 = csv_utils_helpers.clean_value(row.get('Class_1_Found', 'False'), lower=True) == 'true'
                c2 = csv_utils_helpers.clean_value(row.get('Class_2_Found', 'False'), lower=True) == 'true'
                c3 = csv_utils_helpers.clean_value(row.get('Class_3_Found', 'False'), lower=True) == 'true'

                bc = csv_utils_helpers.clean_value(row.get('Burned_Clay_Found', 'False'), lower=True) == 'true'
                bc_only = csv_utils_helpers.clean_value(row.get('Burned_Clay_Only', 'False'), lower=True) == 'true'
                bc1 = csv_utils_helpers.clean_value(row.get('Burned_Clay_Class_1_Found', 'False'), lower=True) == 'true'
                bc2 = csv_utils_helpers.clean_value(row.get('Burned_Clay_Class_2_Found', 'False'), lower=True) == 'true'

                caddo = csv_utils_helpers.clean_value(row.get('Caddo_Found', 'False'), lower=True) == 'true'
                henrietta = csv_utils_helpers.clean_value(row.get('Henrietta_Found', 'False'), lower=True) == 'true'
                overlap = csv_utils_helpers.clean_value(row.get('Henrietta_Caddo_Overlap_Found', 'False'), lower=True) == 'true'
                
                is_pre_str = csv_utils_helpers.clean_value(row.get('Is_Prehistoric', 'No Data'), lower=True)
                is_pre = (is_pre_str == 'true')
                
                # Time Period
                tp = csv_utils_helpers.clean_value(row.get('Learned_Time_Period', 'Unknown'))
                if not tp: tp = 'Unknown'
                stats['time_periods'][tp] += 1

                # Soil Context
                soil = csv_utils_helpers.clean_value(row.get('Soil_Inferred_Context', ''))
                if soil:
                    # Split multiple inferences
                    inferences = [s.strip() for s in soil.split(';') if s.strip()]
                    for inf in inferences:
                        stats['soil_contexts'][inf] += 1

                # Aggregates
                if c1: stats['c1'] += 1
                if c2: stats['c2'] += 1
                if c3: stats['c3'] += 1
                
                if c1 and not c2 and not c3: stats['c1_only'] += 1
                if c2 and not c1 and not c3: stats['c2_only'] += 1
                if c3 and not c1 and not c2: stats['c3_only'] += 1
                
                if is_pre:
                    stats['prehistoric'] += 1
                
                if c3:
                    if is_pre:
                        stats['c3_prehistoric'] += 1
                    else:
                        stats['c3_historic_only'] += 1
                        
                if bc:
                    stats['burned_clay'] += 1
                    if bc1: stats['bc_class_1'] += 1
                    if bc2: stats['bc_class_2'] += 1

                    if c1: stats['bc_with_c1'] += 1
                    if c2: stats['bc_with_c2'] += 1
                    if c3: stats['bc_with_c3'] += 1
                    if is_pre: stats['bc_prehistoric'] += 1
                
                if bc_only:
                    stats['burned_clay_only'] += 1

                if caddo: stats['caddo'] += 1
                if henrietta: stats['henrietta'] += 1
                if overlap: stats['overlap'] += 1
                        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        sys.exit(1)
        
    return stats

def generate_charts(stats, output_dir):
    if not PLOTTING_AVAILABLE:
        return

    print("Generating charts...")
    
    # 1. Burned Rock Class Distribution (in Burned_Rock folder)
    br_dir = os.path.join(output_dir, 'Burned_Rock')
    classes = ['Class 1\n(Scatter)', 'Class 2\n(Hearth)', 'Class 3\n(Oven)']
    counts = [stats['c1'], stats['c2'], stats['c3']]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(classes, counts, color=['skyblue', '#ff9999', '#99ff99'])
    plt.title('Distribution of Burned Rock Features by Class')
    plt.ylabel('Number of Sites')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height, f'{height}', ha='center', va='bottom')
    plt.savefig(os.path.join(br_dir, 'class_distribution.png'))
    plt.close()
    
    # 2. Cultural Typology (in Cultural_Typology folder)
    ct_dir = os.path.join(output_dir, 'Cultural_Typology')
    labels = ['Caddo (Eastern)', 'Henrietta (Western)', 'Overlap']
    sizes = [stats['caddo'], stats['henrietta'], stats['overlap']]
    # Filter out zeros for cleaner pie chart
    labels_filtered = [l for l, s in zip(labels, sizes) if s > 0]
    sizes_filtered = [s for s in sizes if s > 0]

    if sizes_filtered:
        plt.figure(figsize=(8, 8))
        plt.pie(sizes_filtered, labels=labels_filtered, autopct='%1.1f%%', startangle=140)
        plt.title('Cultural Typology Distribution')
        plt.axis('equal')
        plt.savefig(os.path.join(ct_dir, 'cultural_typology_pie.png'))
        plt.close()

    # 3. Burned Clay (in Burned_Clay folder)
    bc_dir = os.path.join(output_dir, 'Burned_Clay')
    labels = ['Class 1 (Material)', 'Class 2 (Features)']
    values = [stats['bc_class_1'], stats['bc_class_2']]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=['#e6b8a2', '#d4a373'])
    plt.title('Burned Clay Classification')
    plt.ylabel('Count')
    plt.savefig(os.path.join(bc_dir, 'burned_clay_classes.png'))
    plt.close()

def write_text_report(stats, output_dir):
    report_path = os.path.join(output_dir, 'Analysis_Summary_Report.txt')
    print(f"Writing report to {report_path}...")
    
    total = stats['total']
    if total == 0: total = 1 
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("ARCHAEOLOGICAL ANALYSIS REPORT\n")
        f.write("==============================\n\n")
        
        f.write("1. DATASET OVERVIEW\n")
        f.write(f"   - Total Sites Processed: {stats['total']}\n")
        f.write(f"   - Sites with Prehistoric Evidence: {stats['prehistoric']} ({stats['prehistoric']/total*100:.1f}%)\n\n")
        
        f.write("2. BURNED ROCK CLASSIFICATION (See 'Burned_Rock' folder)\n")
        f.write(f"   - Class 1 (Scatters): {stats['c1']} ({stats['c1']/total*100:.1f}%)\n")
        f.write(f"   - Class 2 (Hearths):  {stats['c2']} ({stats['c2']/total*100:.1f}%)\n")
        f.write(f"   - Class 3 (Ovens):    {stats['c3']} ({stats['c3']/total*100:.1f}%)\n\n")
        
        f.write("3. BURNED CLAY ANALYSIS (See 'Burned_Clay' folder)\n")
        f.write(f"   - Total Sites with Burned Clay: {stats['burned_clay']}\n")
        f.write(f"   - Class 1 (General Keywords): {stats['bc_class_1']}\n")
        f.write(f"     (burned clay, burnt clay, baked clay, etc.)\n")
        f.write(f"   - Class 2 (Features/Artifacts): {stats['bc_class_2']}\n")
        f.write(f"     (clay ball, clay blob, clay-lined hearth, etc.)\n\n")

        f.write("4. CULTURAL TYPOLOGY (See 'Cultural_Typology' folder)\n")
        f.write(f"   - Caddo (Eastern Influence): {stats['caddo']} sites\n")
        f.write(f"   - Henrietta (Western Influence): {stats['henrietta']} sites\n")
        f.write(f"   - Overlap (Both Influences): {stats['overlap']} sites\n\n")

        f.write("5. SOILS & GEOMORPHOLOGY (See 'Soils' folder)\n")
        f.write("   Inferred Contexts:\n")
        for context, count in stats['soil_contexts'].most_common():
             f.write(f"   - {context}: {count}\n")
        f.write("\n")

        f.write("6. TEMPORAL ANALYSIS\n")
        f.write("   Top 25 Identified Groups:\n")
        for period, count in stats['time_periods'].most_common(25):
            pct = (count / total) * 100
            f.write(f"   - {period}: {count} ({pct:.1f}%)\n")
        f.write("\n")

def write_methodology_report(output_dir):
    report_path = os.path.join(output_dir, 'Methodology_Summary.txt')
    print(f"Writing methodology summary to {report_path}...")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("""# Methodology Summary

## 1. Classification Logic

### A. Burned Rock Features
- **Class 1 (Scatters):** Dispersed thermal refuse (e.g., "fire cracked rock", "burned rock").
- **Class 2 (Hearths):** Discrete thermal features (e.g., "hearth", "rock concentration").
- **Class 3 (Ovens):** Earth oven facilities (e.g., "burned rock midden", "oven", "pit feature").

### B. Burned Clay Classification
- **Class 1 (General):** Presence of generic terms like "burned clay", "baked clay", "daub".
- **Class 2 (Features/Artifacts):** Presence of specific formed items or features: "clay ball", "clay blob", "clay-lined hearth", "clay nodule".

### C. Cultural Typology
Analysis of Eastern vs. Western influences based on diagnostic artifacts.
- **Class 1 (Caddo/Eastern):** Defined by Caddoan ceramics (e.g., "grog tempered", "Williams Plain", "Poynor Engraved") and lithics ("Alba", "Bonham", "Gahagan").
- **Class 2 (Henrietta/Western):** Defined by Plains/Henrietta traits (e.g., "shell tempered", "Nocona", "Washita", "Harrell", "bison scapula hoe").
- **Class 3 (Overlap):** Sites containing diagnostic elements from both classes.

### D. Time Period & Expert Priority
- **Expert Classification:** If a site matches an entry in the Expert Dataset, the `refined_context` from the expert is prioritized and labeled as "Prioritized expert classification".
- **Inference:** Otherwise, the system infers time periods from diagnostic artifacts and keywords.
- **Is_Prehistoric:** Defaults to "No Data". Sets to TRUE if prehistoric evidence is found. Sets to FALSE only if explicit Historic evidence is found AND no prehistoric evidence exists.

### E. Soil & Geomorphology
- Inferences are drawn from soil descriptions (e.g., "deep alluvium" -> Paleoindian potential, "sandy loam terrace" -> Archaic potential).

## 2. Relationship Analysis
A text co-occurrence analysis scans for associations between soil types, site types, and artifacts to identify patterns (e.g., "Paleoindian" sites associated with "Deep Alluvium").
""")

def move_relationship_files(output_dir):
    # Files generated by classify_sites.py in root
    files = ['relationship_analysis.txt', 'relationship_summary.txt']
    dest = output_dir # Root of Analysis_Reports

    for filename in files:
        if os.path.exists(filename):
            print(f"Moving {filename} to {dest}...")
            shutil.move(filename, os.path.join(dest, filename))
        else:
            print(f"Warning: {filename} not found (may not have been generated).")

def main(input_file=DEFAULT_INPUT_FILE):
    print("--- Archaeological Analysis Reporting ---")

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    elif os.environ.get('BURNED_ROCK_INPUT_FILE'):
        input_file = os.environ['BURNED_ROCK_INPUT_FILE']
    else:
        input_file = DEFAULT_INPUT_FILE
    
    ensure_dir(REPORT_DIR)
    for sub in SUBFOLDERS:
        ensure_dir(os.path.join(REPORT_DIR, sub))
    
    stats = analyze_data(input_file)
    write_text_report(stats, REPORT_DIR)
    write_methodology_report(REPORT_DIR)
    generate_charts(stats, REPORT_DIR)
    move_relationship_files(REPORT_DIR)
    
    print(f"\nAnalysis complete. Reports and charts saved to: {os.path.abspath(REPORT_DIR)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate reports and charts from classified site data.")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT_FILE, help="Path to the input classified CSV file.")
    args = parser.parse_args()

    main(args.input)
