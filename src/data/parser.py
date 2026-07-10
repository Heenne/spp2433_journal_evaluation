import os
import pandas as pd
from typing import Tuple, List, Optional

def _clean_column_name(col: str) -> str:
    """Removes leading comment characters, quotes, and whitespace from a column name."""
    col = col.strip().strip("'\"")
    while col.startswith('/'):
        col = col[1:]
    return col.strip()

def parse_point_cloud_csv(filepath: str) -> Tuple[Optional[pd.DataFrame], List[str], str]:
    """
    Loads a CSV file and normalizes the X, Y, Z columns.
    
    Returns:
        Tuple containing:
        - DataFrame with normalized 'X', 'Y', 'Z' columns (if successful)
        - List of available additional columns
        - Error message (empty string if successful)
    """
    try:
        # Load CSV using pandas
        df = pd.read_csv(filepath)
        
        # Clean column names
        df.columns = [_clean_column_name(c) for c in df.columns]
        
        # Identify coordinate columns (case-insensitive)
        x_col = next((c for c in df.columns if c.lower() == 'x'), None)
        y_col = next((c for c in df.columns if c.lower() == 'y'), None)
        z_col = next((c for c in df.columns if c.lower() == 'z'), None)
        
        if not all([x_col, y_col, z_col]):
            return None, [], "Could not find X, Y, and Z columns in the CSV file."
        
        # Rename to standardized X, Y, Z
        rename_map = {x_col: 'X', y_col: 'Y', z_col: 'Z'}
        df = df.rename(columns=rename_map)
        
        # Identify additional columns
        additional_cols = [c for c in df.columns if c not in ['X', 'Y', 'Z']]
        
        return df, additional_cols, ""
        
    except Exception as e:
        return None, [], f"Error parsing CSV file: {str(e)}"
