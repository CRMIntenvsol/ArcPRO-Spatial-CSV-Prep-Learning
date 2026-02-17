import csv
import sys

def increase_csv_field_size_limit():
    """
    Increases the CSV field size limit to handle large fields.
    Handles OverflowError on Windows by finding the max supported integer.
    """
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int/10)

def clean_value(val, lower=False):
    """
    Cleans a value for CSV processing.
    - Replaces newlines with spaces.
    - Replaces double quotes with single quotes.
    - Strips leading/trailing whitespace.
    - Optionally converts to lowercase.
    """
    if val is None:
        return ""
    # Replace newlines with spaces and double quotes with single quotes to ensure robust CSV structure
    cleaned = str(val).replace('\r', ' ').replace('\n', ' ').replace('"', "'").strip()
    if lower:
        return cleaned.lower()
    return cleaned
