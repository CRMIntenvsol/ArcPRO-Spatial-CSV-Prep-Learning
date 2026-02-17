import csv
import sys
import re
import json
import os
import difflib
from collections import Counter

# Increase CSV field size limit
max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int/10)

INPUT_FILE = '/tmp/p3_points_concatenated.csv'
OUTPUT_FILE = '/tmp/p3_points_classified.csv'
SYNONYMS_FILE = '/tmp/potential_synonyms.txt'
ARTIFACT_DB_FILE = 'extracted_artifacts.json'

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

CLASS_2_DEPENDENCY_KEYWORDS = ["hearth", "hearths"]

CLASS_3_KEYWORDS = [
    "rock oven", "earth oven", "oven", "roasting pit", "burned rock mound",
    "burned rock midden", "brm", "pit feature", "baking pit", 
    "cooking pit", "annular mound", "annular midden", "annular brm"
]

BURNED_CLAY_KEYWORDS = [
    "burned clay", "burnt clay", "fired clay", "baked clay", "daub", 
    "clay nodule", "clay lump", "terracotta", "oxidized clay", "rubefied clay",
    "vitrified clay", "clay balls"
]

PREHISTORIC_KEYWORDS = [
    'paleo', 'archaic', 'prehistoric', 'neo-american', 'neo american', 
    'ceramic age', 'lithic', 'flake', 'debitage', 'dart point', 
    'arrow point', 'biface', 'uniface', 'metate', 'mano', 'chert', 
    'flint', 'grog tempered', 'bone tempered', 'shell tempered'
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

EXCLUSION_REGEXES = {
    base_kw: re.compile(r'\b(?:' + '|'.join(re.escape(term) for term in terms) + r')\b')
    for base_kw, terms in EXCLUSION_TERMS.items() if terms
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
    "archaic": "Archaic"
}

# --- 2. Helper Functions ---

def load_artifact_db():
    if os.path.exists(ARTIFACT_DB_FILE):
        try:
            with open(ARTIFACT_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
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

CLASS_1_SET = generate_variations(CLASS_1_KEYWORDS)
CLASS_2_SET = generate_variations(CLASS_2_KEYWORDS)
CLASS_3_SET = generate_variations(CLASS_3_KEYWORDS)
BURNED_CLAY_SET = generate_variations(BURNED_CLAY_KEYWORDS)
ROCK_MATERIAL_SET = generate_variations(ROCK_MATERIAL_KEYWORDS)

BURNED_CLAY_RE = None
CLASS_1_RE_LIST = []
CLASS_2_RE_LIST = []
CLASS_3_RE_LIST = []
ROCK_MATERIAL_RE_LIST = []
TIME_PERIOD_RE_LIST = []
ARTIFACT_RE_LIST = []

def clean_value(val):
    if val is None: return ""
    return str(val).replace('\r', ' ').replace('\n', ' ').replace('"', "'").strip()

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

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
        matches = difflib.get_close_matches(word, TYPO_TARGETS, n=1, cutoff=0.85)
        if matches:
            corrected_words.append(matches[0])
        else:
            corrected_words.append(word)
            
    return " ".join(corrected_words)

def is_negated(text_before, window=5):
    words = text_before.split()
    check_window = words[-window:] if len(words) >= window else words
    for word in check_window:
        if word in NEGATION_TERMS:
            return True
    return False

def is_excluded_context(text_around, keyword):
    for base_kw, regex in EXCLUSION_REGEXES.items():
        if base_kw in keyword:
            if regex.search(text_around):
                return True
    return False

def find_classes_robust(normalized_text):
    """
    Robust classification handling negation, context exclusion, and dependencies.
    Runs on pre-corrected text.
    """
    c1_found = set()
    c2_found = set()
    c3_found = set()
    
    # Check Rock Presence with Negation Check
    rock_present = False
    for kw, regex in ROCK_MATERIAL_RE_LIST:
        for match in regex.finditer(normalized_text):
            start = match.start()
            # Check negation for this rock match
            text_before = normalized_text[max(0, start-30):start]
            if not is_negated(text_before):
                rock_present = True
                break # Found at least one non-negated rock term
        if rock_present: break
            
    def process_set(regex_list, target_set, class_id):
        for kw, regex in regex_list:
            for match in regex.finditer(normalized_text):
                start, end = match.span()
                
                # 1. Negation Check
                text_before = normalized_text[max(0, start-30):start]
                if is_negated(text_before):
                    continue 
                
                # 2. Context Exclusion
                text_around = normalized_text[max(0, start-50):min(len(normalized_text), end+50)]
                if is_excluded_context(text_around, kw):
                    continue
                    
                # 3. Dependency Check (Specific to Class 2 'hearth')
                if class_id == 2:
                    if (kw == "hearth" or kw == "hearths") and not rock_present:
                         continue

                target_set.add(kw)

    process_set(CLASS_1_RE_LIST, c1_found, 1)
    process_set(CLASS_2_RE_LIST, c2_found, 2)
    process_set(CLASS_3_RE_LIST, c3_found, 3)
                 
    return c1_found, c2_found, c3_found

def determine_time_period(normalized_text, artifact_db, is_prehistoric):
    found_periods = set()
    
    for period_name, regex in TIME_PERIOD_RE_LIST:
        if regex.search(normalized_text):
            found_periods.add(period_name)
    
    for period_name, regex in ARTIFACT_RE_LIST:
        if regex.search(normalized_text):
            found_periods.add(period_name)
    
    if found_periods:
        return "; ".join(sorted(list(found_periods)))

    if is_prehistoric:
        return "Inferred: Prehistoric"
    
    if "historic" in normalized_text:
        return "Inferred: Historic"
        
    return "Unknown"

def get_ngrams(text, n):
    words = text.split()
    if len(words) < n: return []
    return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]

def main(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    print("Preparing word banks and artifact DB...")
    artifact_db = load_artifact_db()
    
    global CLASS_1_SET, CLASS_2_SET, CLASS_3_SET, BURNED_CLAY_SET, ROCK_MATERIAL_SET
    CLASS_1_SET = {normalize_text(k) for k in CLASS_1_SET}
    CLASS_2_SET = {normalize_text(k) for k in CLASS_2_SET}
    CLASS_3_SET = {normalize_text(k) for k in CLASS_3_SET}
    BURNED_CLAY_SET = {normalize_text(k) for k in BURNED_CLAY_SET}
    global BURNED_CLAY_RE
    BURNED_CLAY_RE = re.compile(r'\b(?:' + '|'.join(re.escape(kw) for kw in BURNED_CLAY_SET) + r')\b')
    ROCK_MATERIAL_SET = {normalize_text(k) for k in ROCK_MATERIAL_SET}

    global CLASS_1_RE_LIST, CLASS_2_RE_LIST, CLASS_3_RE_LIST, ROCK_MATERIAL_RE_LIST
    CLASS_1_RE_LIST = [(kw, re.compile(r'\b' + re.escape(kw) + r'\b')) for kw in CLASS_1_SET]
    CLASS_2_RE_LIST = [(kw, re.compile(r'\b' + re.escape(kw) + r'\b')) for kw in CLASS_2_SET]
    CLASS_3_RE_LIST = [(kw, re.compile(r'\b' + re.escape(kw) + r'\b')) for kw in CLASS_3_SET]
    ROCK_MATERIAL_RE_LIST = [(kw, re.compile(r'\b' + re.escape(kw) + r'\b')) for kw in ROCK_MATERIAL_SET]

    global TIME_PERIOD_RE_LIST, ARTIFACT_RE_LIST
    sorted_tp_keywords = sorted(TIME_PERIOD_KEYWORDS.keys(), key=len, reverse=True)
    TIME_PERIOD_RE_LIST = [(TIME_PERIOD_KEYWORDS[kw], re.compile(r'\b' + re.escape(normalize_text(kw)) + r'\b')) for kw in sorted_tp_keywords]

    sorted_artifacts = sorted(artifact_db.keys(), key=len, reverse=True)
    ARTIFACT_RE_LIST = [(artifact_db[art], re.compile(r'\b' + re.escape(normalize_text(art)) + r'\b')) for art in sorted_artifacts]

    unigrams = Counter()
    bigrams = Counter()
    trigrams = Counter()
    STOPWORDS = set(['the', 'and', 'of', 'in', 'a', 'to', 'with', 'is', 'was', 'for', 'on', 'at', 'from', 'by', 'an', 'or', 'as', 'no', 'data', 'site', 'sites', 'area', 'areas', 'cm', 'm', 'ft', 'project', 'survey', 'texas', 'county', 'recorded', 'found'])

    print(f"Reading {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames if reader.fieldnames else []
        
        new_cols = [
            'Normalized_Text', 
            'Class_1_Found', 'Class_1_Keywords',
            'Class_2_Found', 'Class_2_Keywords',
            'Class_3_Found', 'Class_3_Keywords',
            'Burned_Clay_Found', 'Burned_Clay_Only', 
            'Is_Prehistoric', 'Learned_Time_Period', 'Prehistoric_Evidence'
        ]
        
        base_fieldnames = [f for f in fieldnames if f not in new_cols]
        new_fieldnames = base_fieldnames + new_cols
        
        print(f"Writing to {output_file}...")
        with open(output_file, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
            writer.writeheader()
            
            row_count = 0
            
            for row in reader:
                clean_row = {k: clean_value(v) for k, v in row.items()}
                original_text = clean_row.get('Concat_site_variables', '')
                normalized_text = normalize_text(original_text)
                
                corrected_text = correct_typos(normalized_text)
                c1_kws, c2_kws, c3_kws = find_classes_robust(corrected_text)
                
                c1 = len(c1_kws) > 0
                c2 = len(c2_kws) > 0
                c3 = len(c3_kws) > 0
                
                burned_clay_found = bool(BURNED_CLAY_RE.search(corrected_text))

                burned_clay_only = False
                if burned_clay_found and not c1 and not c2 and not c3:
                    burned_clay_only = True

                prehist_evidence = []
                for kw in PREHISTORIC_KEYWORDS:
                    if kw in corrected_text:
                        prehist_evidence.append(kw)
                
                is_prehistoric = len(prehist_evidence) > 0
                
                time_period = determine_time_period(corrected_text, artifact_db, is_prehistoric)
                
                clean_row['Normalized_Text'] = corrected_text
                clean_row['Class_1_Found'] = c1
                clean_row['Class_1_Keywords'] = "; ".join(c1_kws)
                clean_row['Class_2_Found'] = c2
                clean_row['Class_2_Keywords'] = "; ".join(c2_kws)
                clean_row['Class_3_Found'] = c3
                clean_row['Class_3_Keywords'] = "; ".join(c3_kws)
                clean_row['Burned_Clay_Found'] = burned_clay_found
                clean_row['Burned_Clay_Only'] = burned_clay_only
                clean_row['Is_Prehistoric'] = is_prehistoric
                clean_row['Learned_Time_Period'] = time_period
                clean_row['Prehistoric_Evidence'] = "; ".join(prehist_evidence)
                
                writer.writerow(clean_row)
                
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
    
    if output_file == OUTPUT_FILE: 
        print("Analyzing frequencies for potential synonyms...")
        with open(SYNONYMS_FILE, 'w', encoding='utf-8') as f_syn:
            f_syn.write("Potential Synonyms / High Frequency Terms Analysis\n")
            f_syn.write("================================================\n\n")
            f_syn.write("Top 50 Unigrams (excluding common stopwords):\n")
            for word, count in unigrams.most_common(50):
                f_syn.write(f"{word}: {count}\n")
            f_syn.write("\n")
            
            f_syn.write("Top 50 Bigrams (2-word phrases):\n")
            interesting_terms = ['rock', 'stone', 'fire', 'thermal', 'burned', 'burnt', 'heat', 'ash', 'charcoal', 'hearth', 'midden', 'oven', 'pit', 'scatter']
            count_shown = 0
            for phrase, count in bigrams.most_common(1000):
                if count_shown >= 50: break
                if any(term in phrase for term in interesting_terms):
                     f_syn.write(f"{phrase}: {count}\n")
                     count_shown += 1
            f_syn.write("\n")
            
            f_syn.write("Top 50 Trigrams (3-word phrases):\n")
            count_shown = 0
            for phrase, count in trigrams.most_common(1000):
                if count_shown >= 50: break
                if any(term in phrase for term in interesting_terms):
                     f_syn.write(f"{phrase}: {count}\n")
                     count_shown += 1
                     
        print(f"Frequency analysis written to {SYNONYMS_FILE}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        main('test_edge_cases.csv', 'test_results.csv')
    else:
        main()
