import numpy as np
import pandas as pd

def euler_translation_to_matrix(tx: float, ty: float, tz: float, rx: float, ry: float, rz: float) -> np.ndarray:
    """Converts translation and Euler angles (degrees) to a 4x4 transformation matrix."""
    from scipy.spatial.transform import Rotation as R
    r = R.from_euler('xyz', [rx, ry, rz], degrees=True)
    rot_matrix = r.as_matrix()
    
    transform = np.eye(4)
    transform[:3, :3] = rot_matrix
    transform[:3, 3] = [tx, ty, tz]
    return transform

def matrix_to_euler_translation(matrix: np.ndarray) -> tuple:
    """Converts a 4x4 transformation matrix to (tx, ty, tz, rx, ry, rz) with angles in degrees."""
    from scipy.spatial.transform import Rotation as R
    tx, ty, tz = matrix[:3, 3]
    rot_matrix = matrix[:3, :3]
    r = R.from_matrix(rot_matrix)
    rx, ry, rz = r.as_euler('xyz', degrees=True)
    return tx, ty, tz, rx, ry, rz

def run_icp(source_df: pd.DataFrame, target_df: pd.DataFrame, 
            initial_transform: np.ndarray = np.eye(4), max_correspondence_distance: float = 10.0):
    """
    Runs ICP to align source_df to target_df using Open3D.
    Returns:
        tuple: (new_tx, new_ty, new_tz, new_rx, new_ry, new_rz), fitness_score
    """
    try:
        import open3d as o3d
    except ImportError:
        print("Warning: open3d is not installed. ICP skipped.")
        return None, 0.0
        
    if source_df.empty or target_df.empty:
        return None, 0.0
        
    source_pcd = o3d.geometry.PointCloud()
    source_pcd.points = o3d.utility.Vector3dVector(source_df[['X', 'Y', 'Z']].values)
    
    target_pcd = o3d.geometry.PointCloud()
    target_pcd.points = o3d.utility.Vector3dVector(target_df[['X', 'Y', 'Z']].values)
    
    reg_p2p = o3d.pipelines.registration.registration_icp(
        source_pcd, target_pcd, max_correspondence_distance, initial_transform,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=2000)
    )
    
    final_transform = reg_p2p.transformation
    fitness = reg_p2p.fitness
    
    return matrix_to_euler_translation(final_transform), fitness
