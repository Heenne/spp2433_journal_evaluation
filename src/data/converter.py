import csv
import os
from typing import Tuple

def convert_txt_to_csv(txt_path: str, csv_path: str) -> Tuple[int, str]:
    """
    Converts a specific TXT format to CSV. 
    Format example: "1: -231.51453 -178.57643 61.62284"
    Returns a tuple of (lines_processed, error_message).
    """
    try:
        lines_processed = 0
        with open(txt_path, 'r') as infile, open(csv_path, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['ID', 'X', 'Y', 'Z'])
            
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                if ':' in line:
                    id_part, coords_part = line.split(':', 1)
                    id_val = id_part.strip()
                    coords = coords_part.strip().split()
                    if len(coords) >= 3:
                        writer.writerow([id_val, coords[0], coords[1], coords[2]])
                        lines_processed += 1
        return lines_processed, ""
    except Exception as e:
        return 0, str(e)
