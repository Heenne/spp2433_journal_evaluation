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
            initial_transform: np.ndarray = np.eye(4), max_correspondence_distance: float = 10.0,
            method: str = "Standard ICP", progress_callback=None, is_cancelled_callback=None):
    """
    Runs Registration to align source_df to target_df.
    Returns:
        tuple: (new_tx, new_ty, new_tz, new_rx, new_ry, new_rz), fitness_score
    """
    try:
        import open3d as o3d
    except ImportError:
        if progress_callback:
            progress_callback("Warning: open3d is not installed. ICP skipped.")
        return None, 0.0
        
    if source_df.empty or target_df.empty:
        return None, 0.0
        
    source_pcd = o3d.geometry.PointCloud()
    source_points = source_df[['X', 'Y', 'Z']].values
    source_pcd.points = o3d.utility.Vector3dVector(source_points)
    
    target_pcd = o3d.geometry.PointCloud()
    target_points = target_df[['X', 'Y', 'Z']].values
    target_pcd.points = o3d.utility.Vector3dVector(target_points)
    
    if method == "SciPy Custom Optimizer":
        if progress_callback:
            progress_callback("Setting up SciPy KDTree...")
            
        import scipy.optimize
        from scipy.spatial import cKDTree
        
        # Build KDTree for target to quickly find nearest neighbors
        tree = cKDTree(target_points)
        
        def objective_function(x):
            if is_cancelled_callback and is_cancelled_callback():
                raise Exception("Cancelled by User")
                
            # x is [tx, ty, tz, rx, ry, rz]
            mat = euler_translation_to_matrix(*x)
            
            # Apply to source points
            ones = np.ones((source_points.shape[0], 1))
            points_4d = np.hstack([source_points, ones])
            transformed = (mat @ points_4d.T).T[:, :3]
            
            # Find nearest neighbor distances
            distances, _ = tree.query(transformed)
            
            # Optimize median distance to handle up to 50% outliers natively
            return np.median(distances)
            
        initial_guess = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        iteration = [0]
        def callback(xk):
            if is_cancelled_callback and is_cancelled_callback():
                raise Exception("Cancelled by User")
            iteration[0] += 1
            if progress_callback:
                progress_callback(f"SciPy Optimizer: Completed Iteration {iteration[0]}...")
                
        if progress_callback:
            progress_callback("Running SciPy Powell Optimization...")
            
        res = scipy.optimize.minimize(objective_function, initial_guess, method='Powell', callback=callback)
        
        if progress_callback:
            progress_callback("Computing final fitness score...")
            
        final_transform = euler_translation_to_matrix(*res.x)
        # Compute fitness manually
        final_points = (final_transform @ np.hstack([source_points, np.ones((source_points.shape[0], 1))]).T).T[:, :3]
        dist, _ = tree.query(final_points)
        inliers = np.sum(dist < max_correspondence_distance)
        fitness = inliers / len(source_points)
        
    elif method == "Robust ICP (Partial Overlap)":
        if progress_callback:
            progress_callback("Estimating point cloud normals (this may take a moment)...")
            
        # Estimate normals for point-to-plane ICP
        source_pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=max_correspondence_distance*5, max_nn=30))
        target_pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=max_correspondence_distance*5, max_nn=30))
        
        # Point-to-plane ICP with Tukey loss (outlier rejection)
        loss = o3d.pipelines.registration.TukeyLoss(k=max_correspondence_distance)
        p2l = o3d.pipelines.registration.TransformationEstimationPointToPlane(loss)
        
        if progress_callback:
            progress_callback("Running Open3D Robust ICP in C++ (cannot estimate time remaining)...")
            
        reg_result = o3d.pipelines.registration.registration_icp(
            source_pcd, target_pcd, max_correspondence_distance, initial_transform,
            p2l,
            o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=2000)
        )
        final_transform = reg_result.transformation
        fitness = reg_result.fitness
        
    else:
        # Standard ICP
        if progress_callback:
            progress_callback("Running Open3D Standard ICP in C++ (cannot estimate time remaining)...")
            
        reg_result = o3d.pipelines.registration.registration_icp(
            source_pcd, target_pcd, max_correspondence_distance, initial_transform,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=2000)
        )
        final_transform = reg_result.transformation
        fitness = reg_result.fitness
        
    if progress_callback:
        progress_callback("Optimization complete.")
    
    return matrix_to_euler_translation(final_transform), fitness
