import os
import re
import json
import glob

REPO_DIR = 'nlp_markdown_repo'
OUTPUT_FILE = 'scan_results.json'

SOIL_KEYWORDS = ['soil', 'sand', 'clay', 'loam', 'alluvium', 'terrace', 'upland', 'floodplain', 'gravel', 'silt', 'geology', 'geoarchaeology']
SITE_KEYWORDS = ['site', 'artifact', 'sherd', 'point', 'lithic', 'ceramic', 'pottery', 'hearth', 'midden', 'occupation', 'component', 'zone']
PERIOD_KEYWORDS = ['paleo', 'archaic', 'prehistoric', 'historic', 'woodland', 'caddo', 'toyah', 'austin phase']

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def scan_file(filepath):
    filename = os.path.basename(filepath)
    results = {
        "artifacts": {},
        "relationships": []
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. CERAMICS THC style extraction
    # Pattern: Name ... Age Range: date
    # We look for "Age Range:" and try to grab the name before it.

    # Split by lines or segments
    lines = content.split('\n')

    for i, line in enumerate(lines):
        clean_line = clean_text(line)

        # Check for Ceramics THC style
        if "Age Range:" in clean_line:
            # Attempt to extract name. Usually name is on the line above or earlier in the same line?
            # In the table example: "Guanajuato Polychrome Age Range: 1830+"
            # Regex: (Name) Age Range: (Date)
            match = re.search(r'([A-Za-z\s\-]+?)\s+Age Range:\s*([0-9A-Za-z\s\+\-]+)', clean_line)
            if match:
                name = match.group(1).strip()
                date = match.group(2).strip()
                # Clean up name: remove common table junk if present
                if "|" in name:
                    name = name.split("|")[-1].strip()

                # Filter out generic text
                if len(name) < 50 and len(name) > 2:
                    results["artifacts"][name] = date

        # Check for Relationships
        # We want sentences with SOIL and SITE keywords.
        # Simple sentence splitter (imperfect but okay)
        sentences = re.split(r'[.!?]', clean_line)
        for sent in sentences:
            lower_sent = sent.lower()
            has_soil = any(k in lower_sent for k in SOIL_KEYWORDS)
            has_site = any(k in lower_sent for k in SITE_KEYWORDS)

            if has_soil and has_site:
                # Highlight the keywords
                results["relationships"].append({
                    "file": filename,
                    "text": sent.strip()
                })

    return results

def main():
    all_results = {"new_artifacts": {}, "relationships": []}

    files = glob.glob(os.path.join(REPO_DIR, "*.md"))
    print(f"Scanning {len(files)} markdown files...")

    for filepath in files:
        file_res = scan_file(filepath)

        # Merge artifacts
        for name, date in file_res["artifacts"].items():
            # Basic deduplication logic or overwrite
            all_results["new_artifacts"][name] = date

        # Merge relationships
        all_results["relationships"].extend(file_res["relationships"])

    print(f"Found {len(all_results['new_artifacts'])} potential artifacts.")
    print(f"Found {len(all_results['relationships'])} potential relationship sentences.")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    main()
