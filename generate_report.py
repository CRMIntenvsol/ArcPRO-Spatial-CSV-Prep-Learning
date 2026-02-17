import csv
import sys
import os
from collections import Counter

# Try to import plotting libraries (standard in ArcPro/Anaconda)
try:
    import matplotlib.pyplot as plt
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Warning: matplotlib not found. Charts will not be generated.")

# Increase CSV field size limit for Windows/Large fields
max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int/10)

DEFAULT_INPUT_FILE = os.environ.get('BURNED_ROCK_INPUT_FILE', 'classified_sites.csv')
REPORT_DIR = 'Burned_Rock_Report'

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def analyze_data(input_file):
    print(f"Reading data from {input_file}...")
    
    stats = {
        'total': 0,
        'c1': 0, 'c2': 0, 'c3': 0,
        'c1_only': 0, 'c2_only': 0, 'c3_only': 0,
        'prehistoric': 0,
        'c3_prehistoric': 0,
        'c3_historic_only': 0,
        'burned_clay': 0,
        'burned_clay_only': 0, # New Metric
        'bc_with_c1': 0,
        'bc_with_c2': 0,
        'bc_with_c3': 0,
        'bc_prehistoric': 0,
        'time_periods': Counter()
    }
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as fin:
            reader = csv.DictReader(fin)
            
            for row in reader:
                stats['total'] += 1
                
                # Check Booleans case-insensitively for robustness
                c1 = row.get('Class_1_Found', 'False').strip().lower() == 'true'
                c2 = row.get('Class_2_Found', 'False').strip().lower() == 'true'
                c3 = row.get('Class_3_Found', 'False').strip().lower() == 'true'
                bc = row.get('Burned_Clay_Found', 'False').strip().lower() == 'true'
                bc_only = row.get('Burned_Clay_Only', 'False').strip().lower() == 'true'
                
                is_pre = row.get('Is_Prehistoric', 'False').strip().lower() == 'true'
                
                # Time Period
                tp = row.get('Learned_Time_Period', 'Unknown').strip()
                if not tp: tp = 'Unknown'
                stats['time_periods'][tp] += 1

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
                    if c1: stats['bc_with_c1'] += 1
                    if c2: stats['bc_with_c2'] += 1
                    if c3: stats['bc_with_c3'] += 1
                    if is_pre: stats['bc_prehistoric'] += 1
                
                if bc_only:
                    stats['burned_clay_only'] += 1
                        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        sys.exit(1)
        
    return stats

def generate_charts(stats, output_dir):
    if not PLOTTING_AVAILABLE:
        return

    print("Generating charts...")
    
    # 1. Class Distribution Bar Chart
    classes = ['Class 1\n(Scatter)', 'Class 2\n(Hearth)', 'Class 3\n(Oven)']
    counts = [stats['c1'], stats['c2'], stats['c3']]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(classes, counts, color=['skyblue', '#ff9999', '#99ff99'])
    plt.title('Distribution of Burned Rock Features by Class')
    plt.ylabel('Number of Sites')
    
    # Add count labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height}',
                 ha='center', va='bottom')
                 
    plt.savefig(os.path.join(output_dir, 'class_distribution.png'))
    plt.close()
    
    # 2. Prehistoric vs Historic (for Class 3)
    if stats['c3'] > 0:
        labels = ['Prehistoric Evidence Found', 'No Prehistoric Evidence']
        sizes = [stats['c3_prehistoric'], stats['c3_historic_only']]
        colors = ['#ffcc99', '#d3d3d3']
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.title('Prehistoric Evidence in Class 3 (Oven) Sites')
        plt.axis('equal')
        plt.savefig(os.path.join(output_dir, 'class3_prehistoric_breakdown.png'))
        plt.close()

    # 3. Time Period Distribution (Top 10)
    tp_counts = stats['time_periods']
    most_common = tp_counts.most_common(15) # Increased to 15 to show detail
    if most_common:
        labels, values = zip(*most_common)
        plt.figure(figsize=(12, 10))
        y_pos = range(len(labels))
        plt.barh(y_pos, values, align='center', color='teal')
        plt.yticks(y_pos, labels)
        plt.xlabel('Number of Sites')
        plt.title('Top Identified Time Periods / Cultures')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'time_period_distribution.png'))
        plt.close()


def write_text_report(stats, output_dir):
    report_path = os.path.join(output_dir, 'Burned_Rock_Analysis_Report.txt')
    print(f"Writing report to {report_path}...")
    
    total = stats['total']
    if total == 0: total = 1 
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("BURNED ROCK ANALYSIS REPORT\n")
        f.write("===========================\n\n")
        
        f.write("1. DATASET OVERVIEW\n")
        f.write(f"   - Total Sites Processed: {stats['total']}\n")
        f.write(f"   - Sites with Prehistoric Evidence: {stats['prehistoric']} ({stats['prehistoric']/total*100:.1f}%)\n\n")
        
        f.write("2. BURNED ROCK CLASSIFICATION RESULTS\n")
        f.write(f"   - Class 1 (Scatters): {stats['c1']} sites ({stats['c1']/total*100:.1f}%)\n")
        f.write(f"   - Class 2 (Hearths):  {stats['c2']} sites ({stats['c2']/total*100:.1f}%)\n")
        f.write(f"   - Class 3 (Ovens):    {stats['c3']} sites ({stats['c3']/total*100:.1f}%)\n\n")
        
        f.write("3. FEATURE ISOLATION (Sites containing ONLY one type)\n")
        f.write(f"   - Pure Scatters (Class 1 only): {stats['c1_only']}\n")
        f.write(f"   - Discrete Hearths (Class 2 only): {stats['c2_only']}\n")
        f.write(f"   - Discrete Ovens (Class 3 only): {stats['c3_only']}\n")
        if stats['c3'] > 0:
            c3_discrete_pct = stats['c3_only'] / stats['c3'] * 100
            f.write(f"     * Observation: {c3_discrete_pct:.1f}% of Class 3 features appear without associated scatters or hearths description.\n\n")
        else:
            f.write("\n")

        f.write("4. TEMPORAL ANALYSIS (Top 25 Identified Groups)\n")
        f.write("   --------------------------------------------\n")
        for period, count in stats['time_periods'].most_common(25):
            pct = (count / total) * 100
            f.write(f"   - {period}: {count} ({pct:.1f}%)\n")
        f.write("\n")

        f.write("5. CULTURAL OBSERVATIONS\n")
        f.write(f"   - Prehistoric Class 3 Sites: {stats['c3_prehistoric']}\n")
        f.write(f"   - Potential Historic/Unclassified Class 3 Sites: {stats['c3_historic_only']}\n")
        
        f.write("\n6. BURNED CLAY ANALYSIS\n")
        f.write(f"   - Total Sites with Burned Clay: {stats['burned_clay']}\n")
        f.write(f"   - Burned Clay ONLY (No Burned Rock): {stats['burned_clay_only']}\n")
        if stats['burned_clay'] > 0:
            bc_total = stats['burned_clay']
            f.write(f"   - Co-occurrence with Class 1 (Scatters): {stats['bc_with_c1']} ({stats['bc_with_c1']/bc_total*100:.1f}%)\n")
            f.write(f"   - Co-occurrence with Class 2 (Hearths): {stats['bc_with_c2']} ({stats['bc_with_c2']/bc_total*100:.1f}%)\n")
            f.write(f"   - Co-occurrence with Class 3 (Ovens): {stats['bc_with_c3']} ({stats['bc_with_c3']/bc_total*100:.1f}%)\n")
            f.write(f"   - Burned Clay in Prehistoric Context: {stats['bc_prehistoric']} ({stats['bc_prehistoric']/bc_total*100:.1f}%)\n")
        else:
            f.write("   - No Burned Clay sites identified.\n")

        f.write("\n7. KEY FINDINGS & RECOMMENDATIONS\n")
        
        # Dynamic Observations
        if stats['c1'] > stats['c2'] and stats['c1'] > stats['c3']:
            f.write("   - PREVALENCE: Dispersed scatters (Class 1) are the most common manifestation of burned rock in this dataset.\n")
            
        if stats['c3_historic_only'] > stats['c3_prehistoric']:
             f.write("   - POTENTIAL BIAS: A majority of Class 3 (Oven) sites do NOT contain explicit prehistoric keywords.\n")
             f.write("     * Recommendation: Review 'Class 3' sites manually to ensure Historic trash pits or fireplaces are not being misclassified.\n")
        else:
             f.write("   - PREHISTORIC CONTEXT: A majority of Class 3 sites contain prehistoric evidence, supporting the classification of earth ovens.\n")
             
        if stats['c2'] < stats['c3']:
             f.write("   - FEATURE VISIBILITY: 'Ovens' (Class 3) are reported more frequently than 'Hearths' (Class 2).\n")
             f.write("     * This may indicate that large features (middens/mounds) are more easily identified during survey than smaller hearth features.\n")
             
        f.write("\n   - NEXT STEPS:\n")
        f.write("     * Use ArcPro to plot 'Class 3' sites. Perform a Hot Spot Analysis to identify intensive processing zones.\n")
        f.write("     * Filter the dataset using the 'Is_Prehistoric' column to create a clean prehistoric distribution map.\n")

def write_methodology_report(output_dir):
    report_path = os.path.join(output_dir, 'Methodology_Summary.txt')
    print(f"Writing methodology summary to {report_path}...")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("""# Burned Rock Analysis - Methodology Summary

## 1. Data Preparation (`process_sites.py`)
The raw CSV export from ArcPro/Database often contains text fields with formatting issues (embedded newlines, quotes) or Windows-specific limitations (integer overflow on field size). The processing step performs the following:
- **Field Concatenation:** Combines relevant descriptive text fields (e.g., `Site_Description`, `Features`, `Artifacts`) into a single searchable text block (`Concat_site_variables`).
- **Sanitization:** Removes hidden characters (carriage returns), replaces smart quotes with standard quotes, and ensures `utf-8` encoding.
- **Handling Limits:** Automatically adjusts the CSV field size limit to handle extremely large text descriptions.

## 2. Classification Logic (`classify_sites.py`)
The core classification uses a **Keyword-Driven Approach** supplemented by **Robust Validation Rules** to ensure accuracy.

### A. Feature Classification (Burned Rock & Clay)
The script processes text through several stages:
1.  **Normalization:** Lowercasing and punctuation removal.
2.  **Typo Correction:** Automatically identifies and fixes common typos (e.g., "herth" -> "hearth", "bunred" -> "burned") using fuzzy matching against a target dictionary.
3.  **Keyword Search with Validation:**
    *   **Class 1 (Scatters):** "fire cracked rock", "burned rock", etc.
    *   **Class 2 (Hearths):** "hearth", "burned rock concentration", etc.
    *   **Class 3 (Ovens):** "earth oven", "burned rock midden", etc.
    *   **Burned Clay:** "burned clay", "daub", "vitrified clay", "clay balls".

**Validation Rules:**
*   **Negation Detection:** Matches are ignored if preceded by "no", "not", "lack", or "absence" (e.g., "no oven features").
*   **Context Exclusion:** Matches are ignored if exclusion terms appear nearby (e.g., "oven" is ignored if "stove", "enamel", or "microwave" are present).
*   **Dependency Checks:** Specific terms like "hearth" only trigger a positive classification if associated **rock material** (e.g., "stone", "limestone", "fcr") is confirmed present and not negated. This prevents "oxidized clay hearths" (without rock) from being misclassified as Burned Rock features.

**Output:**
- Boolean flags (e.g., `Class_1_Found`).
- Keyword lists (e.g., `Class_1_Keywords`) documenting *exactly* which terms triggered the classification.
- "Burned Clay Only" flag for sites with burned clay but no burned rock.

### B. Temporal Analysis (Time Period Inference)
Time periods are determined using a hierarchical two-step process to ensure maximum specificity.

1.  **Diagnostic Artifact Matching:**
    - The text is cross-referenced against a dictionary of **817 diagnostic artifacts** (e.g., "Clovis", "Perdiz", "Pedernales").
    - Each artifact is mapped to a specific time period based on the project schema (e.g., "Perdiz" -> "Late Prehistoric II (Toyah Phase)").

2.  **Explicit Period Keywords:**
    - The text is searched for explicit mentions of time periods (e.g., "Republic of Texas", "Civil War", "Austin Phase").

3.  **Inference Fallback:**
    - If no specific artifacts or period names are found, the script checks for general context keywords (e.g., "lithic", "flake") to assign "Inferred: Prehistoric" or "Inferred: Historic".

**Hierarchy of Specificity:**
The system prioritizes specific labels (e.g., "Paleoindian - Early") over general ones ("Paleoindian").

## 3. Reporting (`generate_report.py`)
The final step aggregates the site-level data to produce:
- **Statistical Summary:** Counts and percentages for all classes and time periods.
- **Co-occurrence Analysis:** How often Burned Clay appears with each rock class.
- **Visualizations:** Bar charts for class distribution and time periods, and pie charts for prehistoric context.
""")

def main():
    print("--- Burned Rock Analysis Tool ---")
    input_file = DEFAULT_INPUT_FILE
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    ensure_dir(REPORT_DIR)
    
    stats = analyze_data(input_file)
    write_text_report(stats, REPORT_DIR)
    write_methodology_report(REPORT_DIR)
    generate_charts(stats, REPORT_DIR)
    
    print(f"\nAnalysis complete. Report and charts saved to: {os.path.abspath(REPORT_DIR)}")

if __name__ == "__main__":
    main()
