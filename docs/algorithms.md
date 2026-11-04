# Algorithms and result metrics

This page explains what the application calculates, what the controls change, and what a result does **not** mean. Numerical comparisons depend on coordinate units and alignment: check the overlay before interpreting deviations. Point-cloud registration and deviation analysis are descriptive geometric calculations; they do not by themselves establish measurement uncertainty or independent ground-truth accuracy.

## Coordinate transforms and filters

For every cloud, the app applies coordinate inversion first, then uniform scale, then the manual XYZ Euler rotation, and finally translation. A rigid registration estimates only rotation and translation. Scale and unit conversion remain the user's responsibility.

| Control | What it does | Parameter meaning |
| --- | --- | --- |
| **Invert X/Y/Z** | Reverses the sign of a coordinate axis. | Use only to reconcile the input coordinate convention; it is applied before scale and pose. |
| **Uniform scale** | Multiplies X, Y, and Z by one factor. | Example: `1000` converts metre-valued coordinates to millimetres. The distance-unit label does not perform conversion. |
| **Z-Bounds** | Keeps points whose Z is between the inclusive minimum and maximum. | Useful for excluding known regions above/below the comparison area. |
| **Z-Score** | Removes a point if any of X, Y, or Z differs from that axis mean by at least the threshold times its standard deviation. | Lower thresholds remove more extreme points. Use cautiously if the object has legitimate long or thin geometry. |
| **SOR** | Computes each point's mean distance to its `k` nearest neighbours (excluding itself), then removes points above `global mean + Std × global standard deviation`. | `k` controls neighbourhood size; **Std** controls how tolerant the filter is. Larger values retain more isolated points. The global standard deviation here is the population SD. |
| **Voxel Grid Downsampling** | Replaces the points in each 3-D voxel with their centroid. When extra data columns exist, the app retains attributes from the nearest original point. | **Voxel Size** is the cell width in the coordinate unit. It reduces display density and is included in filtered-cloud export; registration uses its own resolution. |

The quality filters Z-Bounds, Z-Score, and SOR are used for bounded/global alignment and surface-error calculation. Voxel downsampling is a display/export control; bounded/global registration chooses its own point samples and voxel size. The legacy Standard/Robust ICP actions use transformed coordinates without the quality filters; when either cloud exceeds 50,000 points, they also apply a fixed `0.5`-unit voxel reduction for speed. The original source file is never changed.

## Alignment methods

All aligners treat the selected measurement as **source** and the chosen fixed cloud as **reference/target**. ICP means *iterative closest point*: it repeatedly finds nearby point correspondences and refines a pose from an initial transform. It is a local method; a plausible initial placement matters. See [Besl & McKay (1992)](https://doi.org/10.1109/34.121791) and the [Open3D ICP guide](https://www.open3d.org/docs/latest/tutorial/pipelines/icp_registration.html).

### Manual transform

Manual translation and Euler rotations change the current pose; **Uniform scale** and axis inversions are separate inputs. Rotation is about the origin of the transformed coordinates. Use camera views and the overlay to establish a plausible rough placement before local alignment.

### Standard ICP

Standard ICP uses point-to-point correspondences and minimizes the squared Euclidean distance between matched points. **Max distance** is the correspondence radius: pairs farther apart are not matched. The action permits an unbounded pose update, so a large radius or poor starting pose can pull the measurement onto a nearby but incorrect surface. The implementation allows up to 2,000 ICP iterations.

### Robust ICP (Partial Overlap)

This legacy option uses point-to-plane ICP: it minimizes residuals along target surface normals rather than full 3-D point-to-point distances. It estimates normals with a search radius five times **Max distance** and at most 30 neighbours, and applies a Tukey robust loss to reduce the influence of large residuals. It remains an unbounded local update; the name does not guarantee correct handling of arbitrary partial overlap. The theory and robust weighting are described in [Chen & Medioni](https://graphics.stanford.edu/~smr/ICP/comparison/chen-medioni-align-rob91.pdf) and the [Open3D robust-kernel guide](https://www.open3d.org/docs/latest/tutorial/pipelines/robust_kernels.html).

### Bounded fine alignment (recommended after rough placement)

This optimizer starts at the current manual pose and estimates only a bounded delta. Set independent `+/- X`, `+/- Y`, `+/- Z`, `+/- Rx`, `+/- Ry`, and `+/- Rz` limits. A zero limit locks that degree of freedom. Rotation corrections are around the selected cloud's current transformed centroid.

The optimizer uses a robust, bidirectional closest-point objective and a three-stage point schedule (up to 3,000, 10,000, then 20,000 points). The **Registration points** control (default 30,000; range 1,000–100,000) controls the adaptive input resolution, not the optimizer's three stage caps. For partial scans it first crops to the shared current X/Y footprint, so unmatched scan extensions do not dominate the fit. It does not use PCA or feature matching. Translation limits default to `±10` coordinate units per axis; rotation limits default to `±5°` per axis and are capped at `±30°`. The app retains the original manual pose unless both directions retain at least 5% overlap and enough matches, the trimmed score improves by at least 2% (or a small voxel-based tolerance), and neither directional overlap drops by more than two percentage points. The result dialog reports source overlap, reference overlap, and a trimmed registration RMSE. These are alignment diagnostics, not the surface-error report below.

Choose limits that describe the remaining placement uncertainty, not the whole object's size. For example, after a close manual fit, try a few units of translation and a few degrees of rotation. If the correction reaches a limit, inspect the overlay and consider whether the limits or rough pose are appropriate.

### Global PCA / FPFH alignment

Use this broader search when the initial pose is not close enough for local ICP. It prepares a shared adaptive voxel resolution, keeping at most the requested **Registration points** per cloud after downsampling (default 30,000). Oversized source files are first reproducibly sampled to bound memory.

The app tests the current pose, a centre-of-gravity translation, and candidate orientations derived from principal component analysis (PCA). PCA axes can be permuted or reversed, so the algorithm evaluates proper rotations and retains the best candidates. It also computes **Fast Point Feature Histograms (FPFH)**, which describe local geometry, matches those features, and uses **RANSAC** to find a robust coarse pose. False matches are pruned by distance and edge-length checks. Each candidate is refined by three coarse-to-fine robust point-to-plane ICP stages. The app selects the result primarily by source-cloud overlap, then trimmed RMSE, then symmetric overlap.

FPFH is described by [Rusu, Blodow & Beetz (2009)](https://doi.org/10.1109/ROBOT.2009.5152473); the RANSAC method originates with [Fischler & Bolles (1981)](https://doi.org/10.1145/358669.358692). See the [Open3D global-registration guide](https://www.open3d.org/docs/latest/tutorial/pipelines/global_registration.html) for the FPFH/RANSAC pipeline and the [robust-kernel guide](https://www.open3d.org/docs/latest/tutorial/pipelines/robust_kernels.html) for point-to-plane refinement.

For reproducibility, the current implementation estimates normals with radius `2.5v` and up to 40 neighbours, computes FPFH with radius `6v` and up to 100 neighbours, and scores PCA initializations at `8v`. Feature RANSAC uses mutual matching, a `2.5v` distance threshold, three-point hypotheses, an edge-length ratio check of `0.9`, at most 100,000 iterations, and confidence `0.999`. Candidate refinements use point-to-plane ICP with Tukey loss over radii `8v`, `3v`, and `1.25v`, up to 80 iterations per stage. The best three PCA poses are refined along with the current pose, centroid translation, and any successful FPFH/RANSAC pose. The program reports the chosen voxel size and actual downsampled point counts.

Global alignment is not guaranteed to resolve symmetric or repetitive shapes. Inspect the result at distinctive edges or landmarks. When the pose is already close, bounded fine alignment is usually the safer choice.

## Surface-error methods and statistics

The comparison is directed: it evaluates selected **source** points against the **reference**. It first identifies points inside the reference's projected X/Y footprint and excludes a narrow outer reference-edge band. There is no 3-D error cutoff: every remaining source point contributes its full error, even if its deviation is large. The requested edge margin controls the band width, capped internally at 2% of the shorter reference span. This avoids counting uncertain boundary points as if they were well-supported comparisons.

### Unsigned nearest-reference distance

For each eligible source point `pᵢ`, the app finds its nearest point `q` in the eligible reference set and reports the Euclidean distance:

`dᵢ = min_q ||pᵢ − q||₂`

Distances are nonnegative. This is a one-way nearest-point distance distribution, not a symmetric Chamfer distance and not an exact distance to a reconstructed continuous surface. Dense areas of the reference provide more candidate nearest points.

### Signed local normal / plane distance

The app estimates a local plane around each reference point by PCA of neighbouring reference samples. The plane centre `c` is the neighbourhood centroid; the normal `n` is the eigenvector of the smallest covariance eigenvalue. Each source point is paired with its nearest eligible reference point and evaluated as:

`eᵢ = (pᵢ − c) · n`

Positive direction follows the selected **Normal orientation** (`+/- X`, `+/- Y`, or `+/- Z`) in transformed reference coordinates. This is a signed local-plane approximation, not a signed nearest-point magnitude or a reconstructed curved surface. It can be biased by curvature if **Normal radius** is too large. Radius `0` selects three times the median positive reference nearest-neighbour spacing; **Maximum normal neighbours** defaults to 30. Unsupported, collinear, insufficiently planar, or direction-ambiguous neighbourhoods are excluded from the statistics and appear grey. See the original point-to-plane formulation in [Chen & Medioni](https://graphics.stanford.edu/~smr/ICP/comparison/chen-medioni-align-rob91.pdf). For cloud-to-cloud change detection methods designed around local roughness and point-cloud uncertainty, [M3C2 by Lague, Brodu & Leroux (2013)](https://doi.org/10.1016/j.isprsjprs.2013.04.009) is a distinct alternative; it is not the method implemented here.

### Coverage measures

The two coverage metrics answer different questions and do not depend on Z error, normal support, edge-band exclusion, or the error-analysis point cap:

- **System points within reference area (%)** = source points inside the reference X/Y footprint divided by all finite source points. A large system scan may have a low value even when the reference lies entirely within it.
- **Reference area covered (%)** estimates how much projected reference area has system support. The app rasterizes the reference footprint into equal-area cells and builds the system footprint from locally supported Delaunay triangles in X/Y. It reports covered reference-cell area divided by total reference mask area. This is an application-defined projected-area estimate, not a universal point-cloud metric or 3-D surface-area fraction. Very sparse samples, narrow gaps, and triangulation limits can affect it. The triangulation implementation uses [SciPy's Delaunay routine](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Delaunay.html).

### Reported values

All values use the selected cloud's configured distance unit. If **Maximum source points** is positive and smaller than the cloud, the error statistics use a reproducible random source sample; coverage still uses the full clouds.

| Result | Definition and interpretation |
| --- | --- |
| **P5 / P95** | 5th and 95th percentiles of valid deviations; together they describe the central 90% of evaluated points. |
| **P2.5 / P97.5** | Central 95% empirical interval, shown in the detailed results. |
| **Mean** | Arithmetic mean of the deviations. For unsigned error this is mean distance; for signed error positive and negative values can cancel. |
| **RMSE** | `sqrt(mean(eᵢ²))`. Keeps the sign-insensitive magnitude and gives larger deviations more weight. |
| **Sample standard deviation (SD)** | Spread around the arithmetic mean using denominator `N − 1`. It requires at least two valid points. |
| **Normalized SD (%)** | `100 × SD / axial measurement span`. Enter the full physical span in the same unit; this normalization does not change the deviations. |
| **Minimum / maximum** | Smallest and largest valid deviations. These are sensitive to isolated points and should be read alongside percentiles. |

Map controls change colours only. **Automatic** uses `0…P95` for unsigned distances and a symmetric range based on the 95th percentile of absolute signed deviations. **Symmetric +/- maximum** uses the chosen magnitude around zero; **Custom minimum / maximum** clips to the entered bounds. **Difference from mean deviation** subtracts the mean for display only; white/zero then means the mean deviation, not zero error. **Highlight above mean** adds a red overlay for source points above the reported mean. None of these visual choices changes the report statistics.

Percentile intervals describe the empirical point distribution; they are not confidence intervals or a complete measurement-uncertainty budget. A good registration fit does not prove accuracy, especially if the same points were used to align and evaluate. For an independent accuracy claim, align using separate landmarks/regions and evaluate on hold-out data.

## References

- Besl, P. J. & McKay, N. D. (1992). [A Method for Registration of 3-D Shapes](https://doi.org/10.1109/34.121791). *IEEE Transactions on Pattern Analysis and Machine Intelligence*.
- Chen, Y. & Medioni, G. (1992). [Object Modelling by Registration of Multiple Range Images](https://graphics.stanford.edu/~smr/ICP/comparison/chen-medioni-align-rob91.pdf). *Image and Vision Computing*.
- Fischler, M. A. & Bolles, R. C. (1981). [Random Sample Consensus](https://doi.org/10.1145/358669.358692). *Communications of the ACM*.
- Rusu, R. B., Blodow, N. & Beetz, M. (2009). [Fast Point Feature Histograms (FPFH) for 3D Registration](https://doi.org/10.1109/ROBOT.2009.5152473). *IEEE International Conference on Robotics and Automation*.
- Lague, D., Brodu, N. & Leroux, J. (2013). [Accurate 3D comparison of complex topography with terrestrial laser scanner](https://doi.org/10.1016/j.isprsjprs.2013.04.009). *ISPRS Journal of Photogrammetry and Remote Sensing*.
- [Open3D: Global registration](https://www.open3d.org/docs/latest/tutorial/pipelines/global_registration.html), [ICP registration](https://www.open3d.org/docs/latest/tutorial/pipelines/icp_registration.html), and [robust kernels](https://www.open3d.org/docs/latest/tutorial/pipelines/robust_kernels.html).
- [Point Cloud Library: Statistical Outlier Removal](https://pointclouds.org/documentation/tutorials/statistical_outlier.html).
