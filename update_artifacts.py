import json
import os

ARTIFACTS_FILE = 'extracted_artifacts.json'
SCAN_FILE = 'scan_results.json'

def main():
    if os.path.exists(ARTIFACTS_FILE):
        with open(ARTIFACTS_FILE, 'r') as f:
            artifacts = json.load(f)
    else:
        artifacts = {}

    with open(SCAN_FILE, 'r') as f:
        scan_data = json.load(f)

    new_artifacts = scan_data.get('new_artifacts', {})

    count_added = 0
    for name, date in new_artifacts.items():
        name_clean = name.strip()
        # Basic filtering
        if len(name_clean) > 50 or len(name_clean) < 3:
            continue
        if "th century" in name_clean and "Majolicas" not in name_clean: # Skip "th century" garbage
             if name_clean == "th century": continue

        # Add if not present or update?
        # Let's add if not present to be safe, or print if conflict.
        if name_clean.lower() not in artifacts:
            artifacts[name_clean.lower()] = date
            count_added += 1
        else:
            print(f"Skipping duplicate: {name_clean}")

    with open(ARTIFACTS_FILE, 'w') as f:
        json.dump(artifacts, f, indent=4, sort_keys=True)

    print(f"Added {count_added} new artifacts.")

if __name__ == "__main__":
    main()
