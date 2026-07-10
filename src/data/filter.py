import os
import pandas as pd
import numpy as np
import json

def get_config_filename(original_filepath: str) -> str:
    dir_name = os.path.dirname(original_filepath)
    base_name = os.path.basename(original_filepath)
    name, _ = os.path.splitext(base_name)
    filtered_dir = os.path.join(dir_name, "filtered")
    if not os.path.exists(filtered_dir):
        os.makedirs(filtered_dir)
    return os.path.join(filtered_dir, f"{name}_config.json")

def save_filter_config(original_filepath: str, stride: int, rand_pct: float, color_col: str, base_color: str = None, invert_x: bool = False, invert_y: bool = False, invert_z: bool = False):
    config_file = get_config_filename(original_filepath)
    config = {
        "stride": stride,
        "rand_pct": rand_pct,
        "color_col": color_col,
        "base_color": base_color,
        "invert_x": invert_x,
        "invert_y": invert_y,
        "invert_z": invert_z
    }
    with open(config_file, 'w') as f:
        json.dump(config, f)

def load_filter_config(original_filepath: str) -> dict:
    config_file = get_config_filename(original_filepath)
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None
def filter_by_stride(df: pd.DataFrame, stride: int) -> pd.DataFrame:
    """Returns every Nth row of the DataFrame."""
    if stride <= 1:
        return df
    return df.iloc[::stride].copy()

def filter_by_random_percentage(df: pd.DataFrame, percentage: float) -> pd.DataFrame:
    """Returns a random subset of the DataFrame based on the given percentage (0.0 to 1.0)."""
    if percentage >= 1.0:
        return df
    if percentage <= 0.0:
        return pd.DataFrame(columns=df.columns)
    
    # We use sample() with a fixed random state for reproducibility if desired, but 
    # for a visualization tool, true randomness is fine.
    return df.sample(frac=percentage).copy()

def get_filtered_filename(original_filepath: str, filter_type: str, filter_val: str) -> str:
    """Generates the filepath for the filtered dataset."""
    dir_name = os.path.dirname(original_filepath)
    base_name = os.path.basename(original_filepath)
    name, ext = os.path.splitext(base_name)
    
    filtered_dir = os.path.join(dir_name, "filtered")
    if not os.path.exists(filtered_dir):
        os.makedirs(filtered_dir)
        
    return os.path.join(filtered_dir, f"{name}_{filter_type}_{filter_val}{ext}")

def save_filtered_data(df: pd.DataFrame, original_filepath: str, filter_type: str, filter_val: str) -> str:
    """Saves the filtered DataFrame and returns the new filepath."""
    new_filepath = get_filtered_filename(original_filepath, filter_type, filter_val)
    df.to_csv(new_filepath, index=False)
    return new_filepath

def check_cached_filtered_files(original_filepath: str) -> list:
    """Checks if there are any cached filtered files for the given original file."""
    dir_name = os.path.dirname(original_filepath)
    base_name = os.path.basename(original_filepath)
    name, _ = os.path.splitext(base_name)
    
    filtered_dir = os.path.join(dir_name, "filtered")
    if not os.path.exists(filtered_dir):
        return []
        
    cached_files = []
    for f in os.listdir(filtered_dir):
        if f.startswith(f"{name}_") and f.endswith(".csv"):
            cached_files.append(os.path.join(filtered_dir, f))
            
    return cached_files
