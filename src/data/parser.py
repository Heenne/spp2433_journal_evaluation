import os
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional

def _clean_column_name(col: str) -> str:
    """Removes leading comment characters, quotes, and whitespace from a column name."""
    col = col.strip().strip("'\"")
    while col.startswith('/'):
        col = col[1:]
    return col.strip()

def parse_point_cloud_file(filepath: str) -> Tuple[Optional[pd.DataFrame], List[str], str]:
    """
    Loads a point cloud file (CSV or PLY) and normalizes the X, Y, Z columns.
    
    Returns:
        Tuple containing:
        - DataFrame with normalized 'X', 'Y', 'Z' columns (if successful)
        - List of available additional columns
        - Error message (empty string if successful)
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        return parse_point_cloud_csv(filepath)
    elif ext == '.ply':
        return parse_point_cloud_ply(filepath)
    else:
        return None, [], f"Unsupported file format: {ext}"

def parse_point_cloud_ply(filepath: str) -> Tuple[Optional[pd.DataFrame], List[str], str]:
    """Loads a PLY file and normalizes the X, Y, Z columns."""
    try:
        with open(filepath, 'rb') as f:
            first_line = f.readline()
            if not first_line:
                return None, [], "The PLY file is empty."

            # Older filtered exports could contain CSV text while keeping the
            # source .ply extension. Accept those files by their actual header.
            first_line_text = first_line.decode('utf-8-sig', errors='replace').strip()
            csv_columns = [
                column.strip().strip('\"').lower()
                for column in first_line_text.split(',')
            ]
            if {'x', 'y', 'z'}.issubset(csv_columns):
                return parse_point_cloud_csv(filepath)
            if first_line_text.lower() != 'ply':
                return None, [], (
                    "This file is not a valid PLY file. Its content may be CSV; "
                    "if so, rename it with a .csv extension and try again."
                )

            f.seek(0)
            header = []
            vertex_count = 0
            while True:
                raw_line = f.readline()
                if not raw_line:
                    return None, [], "Invalid PLY file: header is missing 'end_header'."
                line = raw_line.decode('utf-8').strip()
                header.append(line)
                if line.startswith('element vertex'):
                    vertex_count = int(line.split()[-1])
                elif line == 'end_header':
                    break
            
            dtype_list = []
            for h in header:
                if h.startswith('property'):
                    parts = h.split()
                    prop_type = parts[1]
                    prop_name = parts[2]
                    
                    if prop_type in ['float', 'float32']:
                        np_type = 'f4'
                    elif prop_type in ['double', 'float64']:
                        np_type = 'f8'
                    elif prop_type in ['uchar', 'uint8']:
                        np_type = 'u1'
                    elif prop_type in ['int', 'int32']:
                        np_type = 'i4'
                    else:
                        np_type = 'f4'
                        
                    dtype_list.append((prop_name, np_type))
            
            if not dtype_list:
                dtype_list = [('x', 'f4'), ('y', 'f4'), ('z', 'f4')]
                
            data = np.fromfile(f, dtype=np.dtype(dtype_list), count=vertex_count)
            df = pd.DataFrame(data)
            
            df.columns = [_clean_column_name(c) for c in df.columns]
            
            x_col = next((c for c in df.columns if c.lower() == 'x'), None)
            y_col = next((c for c in df.columns if c.lower() == 'y'), None)
            z_col = next((c for c in df.columns if c.lower() == 'z'), None)
            
            if not all([x_col, y_col, z_col]):
                return None, [], "Could not find X, Y, and Z columns in the PLY file."
            
            rename_map = {x_col: 'X', y_col: 'Y', z_col: 'Z'}
            df = df.rename(columns=rename_map)
            
            additional_cols = [c for c in df.columns if c not in ['X', 'Y', 'Z']]
            
            return df, additional_cols, ""
            
    except Exception as e:
        return None, [], f"Error parsing PLY file: {str(e)}"

def parse_point_cloud_csv(filepath: str) -> Tuple[Optional[pd.DataFrame], List[str], str]:
    """
    Loads a CSV file and normalizes the X, Y, Z columns.
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
