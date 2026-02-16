import json
import re
from collections import Counter

INPUT_FILE = 'scan_results.json'
OUTPUT_FILE = 'relationship_analysis.txt'

SOIL_TYPES = ['sand', 'clay', 'loam', 'alluvium', 'terrace', 'upland', 'floodplain', 'gravel', 'silt', 'caliche']
SITE_TYPES = ['paleo', 'archaic', 'prehistoric', 'historic', 'woodland', 'caddo', 'toyah', 'austin phase', 'hearth', 'midden', 'lithic', 'ceramic']

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sentences = data.get('relationships', [])
    print(f"Analyzing {len(sentences)} sentences...")

    co_occurrences = Counter()
    examples = {}

    for item in sentences:
        text = item['text'].lower()

        found_soils = [s for s in SOIL_TYPES if s in text]
        found_sites = [s for s in SITE_TYPES if s in text]

        if found_soils and found_sites:
            for soil in found_soils:
                for site in found_sites:
                    pair = f"{soil} + {site}"
                    co_occurrences[pair] += 1

                    if pair not in examples:
                        examples[pair] = []
                    if len(examples[pair]) < 5:
                        examples[pair].append(item['text'])

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("RELATIONSHIP ANALYSIS\n")
        f.write("=====================\n\n")

        # Sort by count
        for pair, count in co_occurrences.most_common():
            f.write(f"{pair}: {count} occurrences\n")
            for ex in examples[pair]:
                f.write(f"  - {ex}\n")
            f.write("\n")

    print(f"Analysis written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
