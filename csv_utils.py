import sys
import csv

def increase_field_size_limit():
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
