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

def save_filter_config(original_filepath: str, config: dict):
    config_file = get_config_filename(original_filepath)
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

def filter_by_zscore(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    """Removes points where X, Y, or Z deviates more than threshold * std from the mean."""
    if df.empty or threshold <= 0:
        return df
    
    # Calculate Z-scores for X, Y, Z
    z_x = np.abs((df['X'] - df['X'].mean()) / df['X'].std())
    z_y = np.abs((df['Y'] - df['Y'].mean()) / df['Y'].std())
    z_z = np.abs((df['Z'] - df['Z'].mean()) / df['Z'].std())
    
    # Keep points where all Z-scores are below threshold
    mask = (z_x < threshold) & (z_y < threshold) & (z_z < threshold)
    return df[mask].copy()

def filter_by_bounding_box(df: pd.DataFrame, x_min: float = None, x_max: float = None, 
                           y_min: float = None, y_max: float = None, 
                           z_min: float = None, z_max: float = None) -> pd.DataFrame:
    """Removes points outside the specified coordinate limits."""
    if df.empty:
        return df
        
    mask = pd.Series(True, index=df.index)
    if x_min is not None: mask &= (df['X'] >= x_min)
    if x_max is not None: mask &= (df['X'] <= x_max)
    if y_min is not None: mask &= (df['Y'] >= y_min)
    if y_max is not None: mask &= (df['Y'] <= y_max)
    if z_min is not None: mask &= (df['Z'] >= z_min)
    if z_max is not None: mask &= (df['Z'] <= z_max)
    
    return df[mask].copy()

def filter_by_sor(df: pd.DataFrame, num_neighbors: int = 50, std_ratio: float = 1.0) -> pd.DataFrame:
    """
    Statistical Outlier Removal (SOR) using scipy.spatial.cKDTree.
    Removes points whose mean distance to neighbors is > mean_dist + std_ratio * std_dist.
    """
    if df.empty or num_neighbors <= 0:
        return df
        
    try:
        from scipy.spatial import cKDTree
    except ImportError:
        print("Warning: scipy is not installed. SOR filter skipped.")
        return df
        
    points = df[['X', 'Y', 'Z']].values
    if len(points) <= num_neighbors:
        return df
        
    tree = cKDTree(points)
    # k=num_neighbors+1 because the point itself is the closest neighbor (distance 0)
    distances, _ = tree.query(points, k=num_neighbors + 1)
    
    # Mean distance to k nearest neighbors (excluding self)
    mean_distances = np.mean(distances[:, 1:], axis=1)
    
    global_mean = np.mean(mean_distances)
    global_std = np.std(mean_distances)
    
    threshold = global_mean + std_ratio * global_std
    mask = mean_distances <= threshold
    
    return df[mask].copy()

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
