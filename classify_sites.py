import csv
import sys
import re
import json
import os
import difflib
import argparse
import functools
from collections import Counter
import csv_utils_helpers
import csv_utils

# Increase CSV field size limit
csv_utils_helpers.increase_csv_field_size_limit()
max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int/10)

INPUT_FILE = 'p3_points_concatenated.csv'
OUTPUT_FILE = 'p3_points_classified.csv'
SYNONYMS_FILE = 'potential_synonyms.txt'
ARTIFACT_DB_FILE = 'extracted_artifacts.json'
RELATIONSHIP_ANALYSIS_FILE = 'relationship_analysis.txt'
RELATIONSHIP_SUMMARY_FILE = 'relationship_summary.txt'

# --- 1. Keywords Definitions ---

CLASS_1_KEYWORDS = [
    "fire cracked rock", "fire-cracked rock", "fcr", "burned rock", 
    "burned-rock", "burnt rock", "burnt-rock", "thermal spall", 
    "heat spall", "pot lid", "burned caliche", "burned limestone"
]

CLASS_2_KEYWORDS = [
    "hearth", "rock filled hearth", "rock lined hearth", "rock-filled hearth",
    "rock-lined hearth", "rock hearth", "burned rock concentration",
    "fcr concentration", "burned clay", "hearth basin", "ash lens", 
    "charcoal stain", "burned clay concentration", "thermal feature"
]

CLASS_3_KEYWORDS = [
    "rock oven", "earth oven", "oven", "roasting pit", "burned rock mound",
    "burned rock midden", "brm", "pit feature", "baking pit", 
    "cooking pit", "annular mound", "annular midden", "annular brm"
]

# Burned Clay Classes
BURNED_CLAY_CLASS_1_KEYWORDS = [
    "burned clay", "burnt clay", "fired clay", "baked clay", "daub", 
    "oxidized clay", "rubefied clay", "vitrified clay"
]

BURNED_CLAY_CLASS_2_KEYWORDS = [
    "clay ball", "clay blob", "clay object", "clay lump", "clay mass",
    "clay-lined hearth", "clay lined hearth", "clay nodule"
]

# Cultural Typology
CADDO_ARTIFACTS = [
    "caddo", "caddoan", "grog tempered", "grog-tempered", "williams plain",
    "pennington punctate", "pennington punctate-incised", "poynor engraved",
    "sanders engraved", "killough pinched", "monkstown", "foster trailed-incised",
    "maydelle incised", "weches", "alba", "bonham", "steiner", "hays",
    "cliffton", "bassett", "cuney", "gahagan knife", "friday biface", "beamer"
]

HENRIETTA_ARTIFACTS = [
    "henrietta", "toyah", "shell tempered", "shell-tempered", "nocona",
    "washita", "harrell", "fresno", "maud", "bison scapula hoe",
    "beveled knife", "diamond beveled knife"
]

PREHISTORIC_KEYWORDS = [
    'paleo', 'archaic', 'prehistoric', 'neo-american', 'neo american', 
    'ceramic age', 'lithic', 'flake', 'debitage', 'dart point', 
    'arrow point', 'biface', 'uniface', 'metate', 'mano', 'chert', 
    'flint', 'grog tempered', 'bone tempered', 'shell tempered'
]

HISTORIC_KEYWORDS = [
    'historic', 'modern', 'glass', 'metal', 'plastic', 'brick', 'concrete', 'wire'
]

ROCK_MATERIAL_KEYWORDS = [
    "rock", "stone", "limestone", "caliche", "sandstone", "fcr", "spall"
]

TYPO_TARGETS = [
    "burned", "burnt", "rock", "hearth", "oven", "midden", "cracked", 
    "fire", "earth", "pit", "clay", "fcr"
]

EXCLUSION_TERMS = {
    "oven": ["stove", "enamel", "dutch", "microwave", "gas", "electric", "safe", "pottery", "ceramic"],
    "hearth": ["fireplace", "chimney"]
}

NEGATION_TERMS = ["no", "not", "non", "lack", "absence", "negative"]

TIME_PERIOD_KEYWORDS = {
    "mexican republic": "Historic - Mexican Republic",
    "republic of texas": "Historic - Republic of Texas",
    "early statehood": "Historic - Early Statehood (1845-1860)",
    "civil war": "Historic - Civil War",
    "late statehood": "Historic - Late Statehood (1865-1900)",
    "modern": "Historic - Modern (1901-present)",
    "colonial": "Historic - Colonial/Contact",
    "point of contact": "Historic - Colonial/Contact",
    "late prehistoric i": "Late Prehistoric I",
    "late prehistoric ii": "Late Prehistoric II",
    "austin phase": "Late Prehistoric I (Austin Phase)",
    "toyah": "Late Prehistoric II (Toyah Phase)",
    "woodland": "Woodland",
    "neoamerican": "Archaic - Transitional/NeoAmerican",
    "neo-american": "Archaic - Transitional/NeoAmerican",
    "terminal archaic": "Archaic - Transitional/Terminal",
    "paleoindian": "Paleoindian",
    "early archaic": "Early Archaic",
    "middle archaic": "Middle Archaic",
    "late archaic": "Late Archaic",
    "archaic": "Archaic"
}

# Relationship Analysis Lists
REL_SOIL_TYPES = ['sand', 'clay', 'loam', 'alluvium', 'terrace', 'upland', 'floodplain', 'gravel', 'silt', 'caliche', 'vertisol']
REL_SITE_TYPES = ['paleo', 'archaic', 'prehistoric', 'historic', 'woodland', 'caddo', 'toyah', 'austin phase', 'hearth', 'midden', 'lithic', 'ceramic', 'henrietta', 'burned clay']

SOIL_CONTEXT_RULES = {
    "paleo_potential": {
        "keywords": ["deep alluvium", "pleistocene terrace", "clay rich vertisol", "aubrey clovis", "holocene alluvium", "deeply buried", "buried soil", "paleosol"],
        "inference": "High Probability: Paleoindian Context (Deep Alluvium)"
    },
    "archaic_campsite": {
        "keywords": ["sandy loam terrace", "terrace sandy loam", "upland gravel", "lag gravel", "uvalde gravel", "sandy knoll"],
        "inference": "Potential Archaic Context (Sandy Loam/Gravels)"
    },
    "late_prehistoric_floodplain": {
        "keywords": ["floodplain silt", "active floodplain", "recent alluvium", "caddoan", "toyah phase", "sandy clay loam"],
        "inference": "Potential Late Prehistoric Context (Floodplain)"
    }
}

STOPWORDS = set(['the', 'and', 'of', 'in', 'a', 'to', 'with', 'is', 'was', 'for', 'on', 'at', 'from', 'by', 'an', 'or', 'as', 'no', 'data', 'site', 'sites', 'area', 'areas', 'cm', 'm', 'ft', 'project', 'survey', 'texas', 'county', 'recorded', 'found'])

# --- 2. Helper Functions ---

def load_artifact_db():
    if os.path.exists(ARTIFACT_DB_FILE):
        try:
            with open(ARTIFACT_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load artifact DB: {e}")
            return {}
    return {}

def generate_variations(keywords):
    variations = set()
    for kw in keywords:
        kw = kw.lower()
        variations.add(kw)
        if not kw.endswith('s'):
            variations.add(kw + 's')
        if '-' in kw:
            variations.add(kw.replace('-', ' '))
            if not kw.endswith('s'):
                variations.add(kw.replace('-', ' ') + 's')
    return variations

def clean_value(val):
    if val is None: return ""
    return str(val).replace('\r', ' ').replace('\n', ' ').replace('"', "'").strip()

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@functools.lru_cache(maxsize=32768)
def _get_correction_cached(word):
    matches = difflib.get_close_matches(word, TYPO_TARGETS, n=1, cutoff=0.85)
    return matches[0] if matches else word

def correct_typos(text):
    words = text.split()
    corrected_words = []
    
    for word in words:
        if len(word) < 4: 
            corrected_words.append(word)
            continue
        if word in TYPO_TARGETS:
            corrected_words.append(word)
            continue

        corrected_words.append(_get_correction_cached(word))
            
    return " ".join(corrected_words)

def is_negated(text_before, window=5):
    words = text_before.split()
    check_window = words[-window:] if len(words) >= window else words
    for word in check_window:
        if word in NEGATION_TERMS:
            return True
    return False

# Pre-compile exclusion patterns
EXCLUSION_REGEXES = {}
for base_kw, exclusion_list in EXCLUSION_TERMS.items():
    if not exclusion_list:
        continue
    pattern = r'\b(?:' + '|'.join(re.escape(term) for term in exclusion_list) + r')\b'
    EXCLUSION_REGEXES[base_kw] = re.compile(pattern)

def is_excluded_context(text_around, keyword):
    for base_kw, regex in EXCLUSION_REGEXES.items():
        if base_kw in keyword:
            if regex.search(text_around):
                return True
    return False

def get_ngrams(text, n):
    words = text.split()
    if len(words) < n: return []
    return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]

def infer_soil_context(text):
    inferences = []
    for rule_name, rule in SOIL_CONTEXT_RULES.items():
        for kw in rule["keywords"]:
            if kw in text:
                inferences.append(rule["inference"])
                break
    return "; ".join(inferences)

class SiteClassifier:
    def __init__(self, artifact_db=None):
        if artifact_db is None:
            self.artifact_db = load_artifact_db()
        else:
            self.artifact_db = artifact_db

        # Compile Burned Rock Class Regexes
        self.class_1_re_list = self._compile_regex_list(generate_variations(CLASS_1_KEYWORDS))
        self.class_2_re_list = self._compile_regex_list(generate_variations(CLASS_2_KEYWORDS))
        self.class_3_re_list = self._compile_regex_list(generate_variations(CLASS_3_KEYWORDS))
        self.rock_material_re_list = self._compile_regex_list(generate_variations(ROCK_MATERIAL_KEYWORDS))

        # Compile Burned Clay Class Regexes
        self.bc_class_1_re_list = self._compile_regex_list(generate_variations(BURNED_CLAY_CLASS_1_KEYWORDS))
        self.bc_class_2_re_list = self._compile_regex_list(generate_variations(BURNED_CLAY_CLASS_2_KEYWORDS))

        # Compile Cultural Typology Regexes
        self.caddo_re_list = self._compile_regex_list(generate_variations(CADDO_ARTIFACTS))
        self.henrietta_re_list = self._compile_regex_list(generate_variations(HENRIETTA_ARTIFACTS))

        # Time Period Regexes
        sorted_tp_keywords = sorted(TIME_PERIOD_KEYWORDS.keys(), key=len, reverse=True)
        self.time_period_re_list = [(TIME_PERIOD_KEYWORDS[kw], re.compile(r'\b' + re.escape(normalize_text(kw)) + r'\b')) for kw in sorted_tp_keywords]

        # Artifact DB Regexes
        sorted_artifacts = sorted(self.artifact_db.keys(), key=len, reverse=True)
        self.artifact_re_list = [(self.artifact_db[art], re.compile(r'\b' + re.escape(normalize_text(art)) + r'\b')) for art in sorted_artifacts]

    def _compile_regex_list(self, keyword_set):
        normalized = {normalize_text(k) for k in keyword_set}
        return [(kw, re.compile(r'\b' + re.escape(kw) + r'\b')) for kw in normalized]

    def find_classes_robust(self, normalized_text):
        c1_found = set()
        c2_found = set()
        c3_found = set()

        # Check Rock Presence with Negation Check
        rock_present = False
        for kw, regex in self.rock_material_re_list:
            for match in regex.finditer(normalized_text):
                start = match.start()
                text_before = normalized_text[max(0, start-30):start]
                if not is_negated(text_before):
                    rock_present = True
                    break
            if rock_present: break
                
        def process_set(regex_list, target_set, class_id):
            for kw, regex in regex_list:
                for match in regex.finditer(normalized_text):
                    start, end = match.span()
                    
                    text_before = normalized_text[max(0, start-30):start]
                    if is_negated(text_before):
                        continue

                    text_around = normalized_text[max(0, start-50):min(len(normalized_text), end+50)]
                    if is_excluded_context(text_around, kw):
                        continue

                    if class_id == 2:
                        if (kw == "hearth" or kw == "hearths") and not rock_present:
                             continue

                    target_set.add(kw)

        process_set(self.class_1_re_list, c1_found, 1)
        process_set(self.class_2_re_list, c2_found, 2)
        process_set(self.class_3_re_list, c3_found, 3)

        return c1_found, c2_found, c3_found

    def find_burned_clay_classes(self, normalized_text):
        bc1_found = False
        bc2_found = False

        for kw, regex in self.bc_class_1_re_list:
             if regex.search(normalized_text):
                 bc1_found = True
                 break

        for kw, regex in self.bc_class_2_re_list:
             if regex.search(normalized_text):
                 bc2_found = True
                 break

        return bc1_found, bc2_found

    def find_cultural_typology(self, normalized_text):
        caddo_found = False
        henrietta_found = False

        for kw, regex in self.caddo_re_list:
             if regex.search(normalized_text):
                 caddo_found = True
                 break

        for kw, regex in self.henrietta_re_list:
             if regex.search(normalized_text):
                 henrietta_found = True
                 break

        overlap_found = caddo_found and henrietta_found
        return caddo_found, henrietta_found, overlap_found

    def determine_time_period(self, normalized_text, is_prehistoric, refined_context=""):
        found_periods = set()

        # 1. Prioritize Expert Classification
        if refined_context:
            return f"Prioritized expert classification: {refined_context}"

        for period_name, regex in self.time_period_re_list:
            if regex.search(normalized_text):
                found_periods.add(period_name)
        
        for period_name, regex in self.artifact_re_list:
            if regex.search(normalized_text):
                found_periods.add(period_name)

        if found_periods:
            return "; ".join(sorted(list(found_periods)))

        # Fallback Logic
        if is_prehistoric == True:
            return "Inferred: Prehistoric"

        if is_prehistoric == False:
             return "Inferred: Historic"

        if is_prehistoric == "No Data" and "historic" in normalized_text:
             return "Inferred: Historic"

        return "Unknown"

def process_single_row(row, classifier):
    clean_row = {k: clean_value(v) for k, v in row.items()}
    original_text = clean_row.get('Concat_site_variables', '')
    refined_context = clean_row.get('refined_context', '')

    normalized_text = normalize_text(original_text)
    corrected_text = correct_typos(normalized_text)

    # 1. Burned Rock Classification
    c1_kws, c2_kws, c3_kws = classifier.find_classes_robust(corrected_text)
    c1 = len(c1_kws) > 0
    c2 = len(c2_kws) > 0
    c3 = len(c3_kws) > 0

    # 2. Burned Clay Classification
    bc1, bc2 = classifier.find_burned_clay_classes(corrected_text)
    burned_clay_found = bc1 or bc2
    burned_clay_only = burned_clay_found and not (c1 or c2 or c3)

    # 3. Cultural Typology
    caddo_found, henrietta_found, overlap_found = classifier.find_cultural_typology(corrected_text)

    # 4. Prehistoric / Time Period Logic
    prehist_evidence = []
    for kw in PREHISTORIC_KEYWORDS:
        if kw in corrected_text:
            prehist_evidence.append(kw)

    has_prehistoric_evidence = len(prehist_evidence) > 0

    # "No Data" Logic
    # Default to "No Data"
    # Set to False ONLY if NO prehistoric evidence AND explicit Historic evidence
    # Set to True if prehistoric evidence found

    has_historic_evidence = False
    for kw in HISTORIC_KEYWORDS:
        if kw in corrected_text:
            has_historic_evidence = True
            break

    if has_prehistoric_evidence:
        is_prehistoric = True
    elif has_historic_evidence and not has_prehistoric_evidence:
        is_prehistoric = False
    else:
        is_prehistoric = "No Data"

    # Time Period
    time_period = classifier.determine_time_period(corrected_text, is_prehistoric, refined_context)

    # If time period indicates prehistoric, force is_prehistoric to True (if it was "No Data" or even False, though unlikely)
    if time_period and ("Prehistoric" in time_period or "Archaic" in time_period or "Paleo" in time_period or "Caddo" in time_period or "Toyah" in time_period):
         is_prehistoric = True

    soil_context = infer_soil_context(corrected_text)

    # Update Row
    clean_row['Normalized_Text'] = corrected_text
    clean_row['Class_1_Found'] = c1
    clean_row['Class_1_Keywords'] = "; ".join(c1_kws)
    clean_row['Class_2_Found'] = c2
    clean_row['Class_2_Keywords'] = "; ".join(c2_kws)
    clean_row['Class_3_Found'] = c3
    clean_row['Class_3_Keywords'] = "; ".join(c3_kws)

    clean_row['Burned_Clay_Found'] = burned_clay_found
    clean_row['Burned_Clay_Only'] = burned_clay_only
    clean_row['Burned_Clay_Class_1_Found'] = bc1
    clean_row['Burned_Clay_Class_2_Found'] = bc2

    clean_row['Caddo_Found'] = caddo_found
    clean_row['Henrietta_Found'] = henrietta_found
    clean_row['Henrietta_Caddo_Overlap_Found'] = overlap_found

    clean_row['Is_Prehistoric'] = is_prehistoric
    clean_row['Learned_Time_Period'] = time_period
    clean_row['Prehistoric_Evidence'] = "; ".join(prehist_evidence)
    clean_row['Soil_Inferred_Context'] = soil_context

    return clean_row, corrected_text

def perform_relationship_analysis(all_text_rows):
    print(f"Performing relationship analysis on {len(all_text_rows)} rows...")
    co_occurrences = Counter()
    examples = {}

    for text in all_text_rows:
        # Simple analysis: check if terms exist in the same site description
        # We can split by ';' if we want "sentence" level from the concat process,
        # but Normalized_Text is already flattened.
        # Let's approximate "sentence" or "context" by checking the whole description for now,
        # or split by periods if they exist (they usually don't in the cleaned text).

        # User's script used "sentences". Concat fields are separated by ";".
        # Let's try to verify if we can check "within same field" context.
        # But normalized_text stripped punctuation.
        # Let's assume the whole site text is the context unit.

        found_soils = [s for s in REL_SOIL_TYPES if s in text]
        found_sites = [s for s in REL_SITE_TYPES if s in text]

        if found_soils and found_sites:
            for soil in found_soils:
                for site in found_sites:
                    pair = f"{soil} + {site}"
                    co_occurrences[pair] += 1

                    if pair not in examples:
                        examples[pair] = []
                    if len(examples[pair]) < 5:
                        examples[pair].append(text[:200] + "...") # Store snippet

    # Write Results
    with open(RELATIONSHIP_ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        f.write("RELATIONSHIP ANALYSIS\n")
        f.write("=====================\n\n")
        for pair, count in co_occurrences.most_common():
            f.write(f"{pair}: {count} occurrences\n")
            for ex in examples[pair]:
                f.write(f"  - {ex}\n")
            f.write("\n")

    # Write Summary
    with open(RELATIONSHIP_SUMMARY_FILE, 'w', encoding='utf-8') as f:
         f.write("RELATIONSHIP SUMMARY\n")
         f.write("====================\n\n")
         f.write(f"Total Associations Found: {sum(co_occurrences.values())}\n")
         f.write(f"Unique Pairs: {len(co_occurrences)}\n")
         f.write("Top 10 Associations:\n")
         for pair, count in co_occurrences.most_common(10):
             f.write(f" - {pair}: {count}\n")

    print(f"Relationship analysis written to {RELATIONSHIP_ANALYSIS_FILE} and {RELATIONSHIP_SUMMARY_FILE}")

def main(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    print("Initializing classifier...")
    classifier = SiteClassifier()

    print(f"Reading {input_file}...")
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    unigrams = Counter()
    bigrams = Counter()
    trigrams = Counter()
    all_normalized_texts = []

    with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames if reader.fieldnames else []
        
        new_cols = [
            'Normalized_Text', 
            'Class_1_Found', 'Class_1_Keywords',
            'Class_2_Found', 'Class_2_Keywords',
            'Class_3_Found', 'Class_3_Keywords',
            'Burned_Clay_Found', 'Burned_Clay_Only', 
            'Burned_Clay_Class_1_Found', 'Burned_Clay_Class_2_Found',
            'Caddo_Found', 'Henrietta_Found', 'Henrietta_Caddo_Overlap_Found',
            'Is_Prehistoric', 'Learned_Time_Period', 'Prehistoric_Evidence',
            'Soil_Inferred_Context'
        ]
        
        base_fieldnames = [f for f in fieldnames if f not in new_cols]
        new_fieldnames = base_fieldnames + new_cols
        
        print(f"Writing to {output_file}...")
        with open(output_file, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
            writer.writeheader()
            
            row_count = 0
            
            for row in reader:
                clean_row, corrected_text = process_single_row(row, classifier)
                
                # Filter output
                output_row = {k: clean_row.get(k, '') for k in new_fieldnames}
                writer.writerow(output_row)
                
                all_normalized_texts.append(corrected_text)

                words = corrected_text.split()
                clean_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
                unigrams.update(clean_words)
                
                bg = get_ngrams(corrected_text, 2)
                bigrams.update(bg)
                
                tg = get_ngrams(corrected_text, 3)
                trigrams.update(tg)
                
                row_count += 1
                if row_count % 1000 == 0:
                    print(f"Processed {row_count} rows...")

    print(f"Finished processing {row_count} rows.")
    
    # Post-processing Analysis
    perform_relationship_analysis(all_normalized_texts)

    # Synonym Analysis (Default behavior or flag)
    # We'll just run it if using default filenames as a heuristic for "full run"
    if output_file == OUTPUT_FILE:
        print(f"Analyzing frequencies for potential synonyms...")
        with open(SYNONYMS_FILE, 'w', encoding='utf-8') as f_syn:
            f_syn.write("Potential Synonyms / High Frequency Terms Analysis\n")
            f_syn.write("================================================\n\n")
            f_syn.write("Top 50 Unigrams:\n")
            for word, count in unigrams.most_common(50):
                f_syn.write(f"{word}: {count}\n")
            f_syn.write("\nTop 50 Bigrams:\n")
            for phrase, count in bigrams.most_common(50):
                f_syn.write(f"{phrase}: {count}\n")
            f_syn.write("\nTop 50 Trigrams:\n")
            for phrase, count in trigrams.most_common(50):
                f_syn.write(f"{phrase}: {count}\n")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Dummy test mode if needed
        pass
    else:
        main()
