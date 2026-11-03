# 3D Point Cloud Data Viewer (spp2433_journal_evaluation)

A fast, local Python desktop application built with **PyQt6** and **matplotlib** to evaluate, filter, and visualize dense 3D surface scan data from CSV files.

## Features

- **Persistent workspace**: Keep projects and datasets in a left sidebar, the interactive 3-D view in the centre, and contextual Data, Prepare, Align, Evaluate, and Export tools on the right. Direct navigation does not enforce a fixed workflow.
- **Light and dark themes**: Start with the light theme or switch to dark from the toolbar. The choice is saved in the per-user application settings.
- **Standalone Windows release**: Build a versioned EXE with `tools/build_windows_exe.ps1`; publishing a GitHub Release triggers the Windows build and attaches the executable. See [Windows partner release](docs/windows-release.md) and the [feature navigation map](docs/feature-navigation.md).
- **Application Icon**: A blue-white-red point-cloud icon appears in the title bar and running application's Windows taskbar button. Restart the application after updating. Assets are in `src/assets/app_icon.{svg,png,ico}`; rebuild them with `pixi run python tools/generate_app_icon.py`. The ICO includes sizes from 16 to 256 pixels. Windows startup sets the dedicated identity `SPP2433.PointCloudEvaluation` before creating the UI.
- **Robust CSV Parsing**: Dynamically detects `X`, `Y`, and `Z` coordinates regardless of capitalization, and automatically ignores comment blocks like `//` in the headers. Retains extra columns (Intensity, Return Number, etc.) for visualization.
- **Smart Filtering & Downsampling**: Includes intuitive sliders to decimate the point cloud (e.g., keep 1 in every 10 points) or take a random percentage sample to keep the application responsive with massive datasets.
- **Caching Mechanism**: Save your filtered datasets locally. The app will automatically detect optimized datasets the next time you load the original file, saving significant loading time.
- **Project Toolbar & Safe Saving**: Icon actions provide Open, Open Project, Save, Save As, conversion, reference selection, and recent projects. Projects preserve cloud order and visibility; Save writes to the open project, while Save As creates a separate backup. Unsaved changes are flagged and confirmed on close.
- **Pixel Coordinate Conversion**: The top-bar **Convert pixel coordinates to mm** action creates a new CSV copy of the selected raw cloud. Enter pixels per millimetre (for example, `2.1`); X and Y are divided by that value. Z is unchanged by default and can be included only when it is also in pixels. The original cloud is hidden and the converted copy is loaded automatically.
- **3D Visualization**: Render points in an interactive 3D space. Apply dynamic color mapping using any of the additional columns in your dataset.
- **Stable Inspection View**: Keep the current 3-D camera orientation, zoom, and pan while applying manual transforms or refreshing the plot.
- **Camera Orientation Pad**: Jump to `±X`, `±Y`, or `±Z` views, return to isometric, or rotate the current view in 90° increments for axis-by-axis manual alignment.
- **List-ordered Overlay Display**: The first visible cloud in the loaded-cloud list is drawn above all others, then the second, and so on. Use **Move Up** / **Move Down** to set the display layer order; project saves retain this list order. It is display-only and never changes coordinates or error calculations.
- **Bounded Manual Fine Alignment**: Refine a rough manual pose with an iterative, robust closest-point optimizer. For materially partial scans, it first intersects the current X-Y footprints to exclude scan extensions with no counterpart, then freezes that 3-D overlap. Its correction rotates around the selected cloud's transformed centroid captured when the action starts, not around the raw-file origin. It provides independent `+/- X/Y/Z` and `+/- Rx/Ry/Rz` bounds and accepts a change only when the bidirectional anchored score measurably improves. It deliberately does not use ambiguous centre-of-gravity, PCA, or global feature initializers.
- **Previous Global Alignment (PCA / FPFH)**: Retains the broad automatic workflow: centre-of-gravity and PCA orientation candidates plus FPFH/RANSAC feature matching, each refined by robust coarse-to-fine ICP. It is useful when no good manual pose is available, but needs visual validation on small, smooth, or repetitive blade areas.
- **Surface-Error Report**: Calculate source-to-reference nearest-surface distances for only the overlapping area, with coverage, P5, median, mean, RMSE, P95, and maximum deviation. Save the project to keep the numeric report across sessions.
- **Pointwise Error Map**: After a surface-error calculation, colour every analysed project-cloud point from low to high nearest-surface error. The colour bar marks the mean; points outside the reference footprint or its edge band are grey and points above the mean can optionally be overlaid in red. Set **Heatmap maximum** under **Surface Error** before calculation to a fixed value, or use automatic P95 scaling. You can also adjust it afterward without recalculating. Export the current view as a report figure.
- **High-Quality Export**: Export your generated plots to static formats (PNG/JPEG) or vector graphics (SVG) for reports and presentations.
- **Export Font Sizes**: Under **Export Appearance**, set separate sizes in points for axis labels, axis numbers, colour-bar labels, and colour-bar numbers. These apply to previews and both display-resolution and full-resolution exports, and are saved with export settings. Older settings files default to 10 pt.
- **Z-axis Export Spacing**: The Z title follows the rendered tick-label position. **Z-axis title gap** sets the space between the title and tick numbers in points. **Z-axis tick label gap** sets the minimum empty space between adjacent numbers in points, expanding the displayed Z-axis height while retaining coordinates, limits, and tick values. Its **Default** leaves the axis proportions unchanged. **Z-axis tick interval** sets a step in axis units: `10` places ticks at multiples of 10 within the current limits, including negative values and zero. A positive interval overrides **Number of Z-axis ticks**, which remains available for an exact count. With no interval or count, **Auto** chooses ticks and reduces overlap. These settings are saved with export settings; older tick settings remain compatible. Label layout is measured with scatter points hidden, so dense clouds are rendered only during the actual export.

## Prerequisites

This project uses [Pixi](https://pixi.sh/) for dependency management to ensure a clean, reproducible environment without polluting your global Python installation.

1. **Install Pixi**: If you don't have it installed yet, follow the official instructions:
   - **Windows (PowerShell)**: 
     ```powershell
     iwr -useb https://pixi.sh/install.ps1 | iex
     ```
   - **macOS/Linux**:
     ```bash
     curl -fsSL https://pixi.sh/install.sh | bash
     ```

## How to Run

Running the application is simple. From the root of the repository, execute the following command. Pixi will automatically download Python and the required dependencies into an isolated environment before launching the app.

```bash
pixi run start
```

## Project Structure
- `src/main.py`: Entry point for the application.
- `src/ui/`: Contains the PyQt6 user interface components (`main_window.py`, `control_panel.py`, `plot_canvas.py`).
- `src/data/`: Contains the data ingestion and caching logic (`parser.py`, `filter.py`).
- `pixi.toml`: Dependency and environment configuration.

## Aligning and Comparing a Measurement

1. Load the reference cloud and one project cloud. Select the project cloud in the left-hand list.
   If the selected cloud stores X/Y in pixels, use the top-bar **Convert pixel coordinates to mm** action first. At `2.1 pixels/mm`, one pixel is `0.476190 mm`; leave **Z is also in pixels** unchecked when Z is already in millimetres. The new copy starts with its own manual transform settings.
2. In **Manual Transform**, set **Uniform scale** if the files use different units. For example, use `1000` when the selected measurement is in metres and the reference is in millimetres. Scale is applied before rotation and translation.
3. If possible, use the manual transform controls to place the scans approximately together. This is especially useful for a small project scan against a much larger reference scan.
4. If you need the previous broad PCA/centre-of-gravity/FPFH method, open **Legacy Alignment** and use **Run Previous Global Auto Align**. It uses the current transformed cloud coordinates, including enabled axis inversions.
5. In **Fine Align & Error**, use **Bounded Manual Fine Alignment** to choose the reference and set independent `+/- X`, `+/- Y`, `+/- Z` translation limits plus `+/- Rx`, `+/- Ry`, `+/- Rz` Euler-angle limits. They are corrections relative to the current manual pose at the selected cloud's transformed centroid captured when you click the button; set an axis to `0` to lock it. For partial scans, the optimizer automatically restricts matching to the current shared X-Y footprint before fitting in 3-D, so parts unique to either scan are ignored. Use limits that reflect your manual uncertainty (for example, a few centimetres and a few degrees), rather than the full scan size, then click **Optimise Manual Alignment**. The result is saved only if the frozen two-sided overlap improves measurably; otherwise the manual pose is retained unchanged.
6. In the same tab under **Surface Error**, choose the same reference, set a **Reference edge margin**, select the error-map colouring, and click **Calculate Surface Error**. **System points within reference area [%]** counts the fraction of measurement points inside the reference X-Y footprint. **Reference area covered [%]** measures how much of that footprint is covered by the measurement, using equal-area cells rather than point counts. Error statistics include all analysed points inside the reference area after excluding its outer edge band, even when their distance is large.

The default registration limit is 30,000 adaptive voxel points per cloud. Surface-error statistics use all selected-cloud points by default; an optional **Maximum source points** limit uses a deterministic random sample for larger clouds. Both coverage metrics use the full measurement independently of that limit. The full reference is indexed with a KD-tree and source queries are processed in chunks.

After calculating surface error, save the project to retain the numeric report and your manual heatmap maximum. Reopening the project restores the report when both input files and their cloud settings are unchanged. The pointwise colour map is held in memory and must be recalculated after reopening if you want to display or export it again.

Surface-error settings are saved per source cloud independently of the numeric report: reference selection, reference edge margin, maximum source points, colouring mode, heatmap maximum, and the show-map/highlight options. They survive reopening, edits that invalidate a report, and changes made before the first calculation. Reopening also restores the selected surface-error source.

Fine alignment estimates a rigid pose (rotation and translation), not a scale. The clouds must therefore be brought into compatible units with **Uniform scale** first. Smooth, repetitive blade regions and very small overlaps are inherently ambiguous, so overlap coverage and the visual overlay remain important validation checks. **Invert X/Y/Z** is applied before plotting, both alignment methods, surface-error calculation, and saved transformed data. If you have inverted the reference Z axis to put it in the correct visual direction, both aligners use that inverted reference rather than the original raw Z values.

## Previous Global Auto Alignment (PCA / FPFH)

Use **Legacy Alignment -> Run Previous Global Auto Align** when the two clouds do not yet have a sufficiently good manual relative pose. It is a *global*, coarse-registration procedure: it searches broadly for a rigid transform, then refines each plausible starting transform. It is intentionally separate from **Optimise Manual Alignment**, which only makes a bounded correction to a pose you have already placed manually.

The algorithm always uses the coordinates currently shown by the application. For each cloud this means that enabled axis inversions are applied first, then uniform scale, then the saved manual rotation and translation. Thus, if the reference `Z` axis was inverted to make its physical direction correct, PCA, FPFH, ICP, scoring, and the final result all use that inverted reference. The raw CSV is not changed unless **Save Filtered Data** is used; that export writes the transformed coordinates.

### Processing sequence

1. **Prepare a manageable common resolution.** Non-finite XYZ rows are ignored. To avoid constructing registration data structures for millions of points, each cloud is deterministically pre-sampled to at most `min(10 × requested registration points, 1,000,000)` points. A common voxel size `v` is selected from point spacing and cloud extent and is increased by a factor of `1.6` until both voxel-downsampled clouds contain no more than the requested number of registration points (default: 30,000 per cloud). The dialog reports the actual `v` and point counts; record them for reproducibility.
2. **Estimate local geometry.** Surface normals are estimated on both downsampled clouds using a radius `2.5v` and at most 40 neighbours. These normals are used by the point-to-plane ICP refinement. FPFH descriptors are calculated with a radius `6v` and at most 100 neighbours.
3. **Construct several global starting poses.** The current pose (identity correction) and a centre-of-gravity translation are always candidates. PCA is calculated from the covariance of each cloud. Because principal axes have an arbitrary sign and may be permuted, all 24 proper (non-reflecting, determinant `+1`) axis/sign mappings are considered; the three best candidates at an `8v` correspondence radius are retained. This step is why PCA can occasionally give a 180-degree-looking pose on a symmetric or partial blade scan: the geometry alone does not always distinguish the physically correct principal-axis direction.
4. **Add a feature-based candidate.** FPFH descriptors from the two clouds are matched and a RANSAC pose is estimated. RANSAC uses mutual feature matching, a correspondence distance of `2.5v`, three-point hypotheses, an edge-length consistency threshold of `0.9`, and up to 100,000 iterations with confidence `0.999`. If FPFH/RANSAC cannot be computed, that candidate is skipped; the centre-of-gravity and PCA candidates still run. FPFH is a local geometric descriptor designed to make feature matching much cheaper than the original PFH descriptor; RANSAC tests randomly sampled correspondence hypotheses while rejecting implausible ones. See [Rusu et al. (2009)](https://cir.nii.ac.jp/crid/1362825895092064896?lang=en) and the [Open3D global-registration description](https://www.open3d.org/docs/latest/tutorial/pipelines/global_registration.html).
5. **Refine every candidate with robust ICP.** Each starting pose is refined in three point-to-plane ICP passes. The correspondence radii are `8v`, `3v`, and `1.25v`, with at most 80 iterations per pass. A Tukey robust loss reduces the influence of outlier correspondences, such as points outside the common measurement area or defect/noise points. Point-to-plane ICP and robust kernels are documented by [Open3D](https://open3d.org/docs/latest/tutorial/pipelines/robust_kernels.html).
6. **Score and select the result.** At the final radius (`1.25v`), the code calculates nearest-neighbour distances in both directions: selected project cloud -> reference and reference -> selected project cloud. In each direction, only the closest 80% of accepted correspondences are used for the trimmed RMSE. The result is selected primarily by project-cloud coverage, then by this trimmed RMSE, then by symmetric overlap (the geometric mean of the two directional coverages). Preferring project-cloud coverage is deliberate: a project cloud can be much smaller than the reference and should not be penalised merely because it does not cover the whole reference.

The displayed **source overlap** is the fraction of the selected project cloud with a correspondence within the final radius. **Reference overlap** is the converse fraction and will naturally be small when the reference covers substantially more of the blade. **Symmetric overlap** is `sqrt(source overlap × reference overlap)`. The displayed **trimmed registration RMSE** is a registration-selection diagnostic on downsampled points, not a full-resolution surface-error result.

### When to use it

- First make the coordinate conventions physically consistent: especially units, handedness, and any required `Invert X/Y/Z` setting. A rigid registration cannot repair an unknown scale factor or an inconsistent reflection.
- Use global alignment when the rough pose is unknown. Inspect the overlay after it finishes, particularly around unique edges, root/tip features, damage, or other non-repetitive geometry.
- If the pose is already close, prefer **Optimise Manual Alignment** with tight component-wise bounds. It cannot perform the broad PCA flip that a global search can choose.
- Do not treat a low registration RMSE alone as proof of a correct pose. A large smooth surface can have a low closest-point residual at an incorrect tangential position. Require plausible overlay, sufficient project-cloud overlap, and—where available—independent landmarks or a hold-out region.

## Surface-error calculation

After an accepted pose is saved, **Calculate Surface Error** offers two **Error method** choices. The existing unsigned mode computes the Euclidean nearest-neighbour distance for every analysed selected-cloud point:

`d_i = min_{q in reference} ||p_i - q||_2`

**Signed local normal / plane distance** instead fits a local PCA plane around each reference point using the full quality-filtered reference cloud. The plane passes through the neighbourhood centroid `c`; its unit normal `n` is the covariance eigenvector with the smallest eigenvalue. Each system point is associated with its nearest eligible reference point and evaluated as `e = (p - c) dot n`. This is a signed local plane approximation, not a signed nearest-point magnitude or exact distance to a reconstructed curved surface. It follows local surface slope but can be biased by curvature when the neighbourhood is too large.

Set **Normal radius** in the configured distance unit (zero selects three times the median positive nearest-neighbour reference spacing), **Maximum normal neighbours** (default 30), and **Normal orientation** (+/- X, Y, or Z in the transformed reference coordinates). Normals point towards the selected direction, which defines positive error; it does not automatically identify the specimen exterior. Choose an appropriate direction for each surface side. Neighbourhoods with fewer than three points, effectively collinear points (second/largest covariance eigenvalue ratio <= 1e-8), insufficient planarity (smallest/second eigenvalue ratio > 0.25), or near-perpendicular orientation (`abs(n dot direction) <= 1e-6`) are excluded and shown grey. Their source-point count is reported separately. The projected coverage metrics are independent of these normal exclusions.

**Heatmap scale** supports automatic bounds, a symmetric `[-maximum, +maximum]` range, or a custom **Heatmap minimum / maximum**. Automatic signed maps use the 95th percentile of absolute deviations symmetrically; a positive maximum overrides that magnitude. In symmetric mode zero also selects automatic magnitude. In custom mode both limits are literal and minimum must be smaller than maximum. Clipping changes colours only, never the statistics. Signed maps default to blue for negative values, white at zero, and red for positive values. Under **Export Appearance -> Heatmap colours**, select **Blue / white at zero / red** to use this palette explicitly, including with asymmetric limits; **Automatic (by error method)** chooses it for signed maps and `turbo` for unsigned maps. Preview, current-display export, and full-resolution export share the same error method and normalization. Existing saved export settings that explicitly select `turbo` retain that selection.

All normal and scale settings are saved per source cloud in the project. Changing the error method or normal parameters requires **Calculate Surface Error** again; valid colour-scale changes update an existing map immediately. The report includes the selected metric, P5/P95, mean, RMSE, signed minimum/maximum, and sample standard deviation (`ddof=1`, unavailable for fewer than two valid points). Normal parameters and orientation remain attached to the calculated map so export cannot silently switch methods when controls are edited.

#### Journal statistics and result overview

In **Fine Align & Error → Surface Error**, enter each source system's **Axial measurement range** from Table 3 in the same unit as the errors. Enter the full span: a range from −100 to +100 mm means **200 mm**. This input is saved per source cloud; changing it updates the normalized statistic without recalculating point deviations.

The compact result table and **View Surface Error Results…** dialog show the system-point fraction, reference-area coverage, **[P5; P95]** (central 90% empirical interval), **sample standard deviation**, and **normalized standard deviation (%) = 100 × SD / axial measurement span**. These are computed from the valid deviations of the selected error method, including negative deviations in signed mode. The dialog provides an overview across loaded clouds, detailed results for the selected row, an additional **[P2.5; P97.5]** interval, and **Copy table (TSV)** for transfer to a spreadsheet. Median remains in saved reports for compatibility but is no longer a headline statistic.

The status below the calculation controls indicates missing results, available results, missing axial range, or calculation settings changed since the last report. Changes to the error method, reference, edge margin, analysis-point cap or signed-normal parameters require recalculation. Missing statistics are displayed as **—**, including SD for fewer than two valid points; a genuinely zero SD is displayed as zero. Older reports with missing statistics need recalculation. Display clipping does not change the statistics.

The report is prepared before its window opens. Opening it returns immediately from the comparison worker's completion callback; the main window remains modal while the report is visible. Plot redraws and incoming plot refreshes are deferred until the report closes, so resizing/layout events cannot make the results window wait for a dense point-cloud redraw.

**Error statistics ready** means the numerical calculation has finished; **Preparing interactive point-cloud preview** identifies the subsequent rendering phase. The progress indicator is cleared only when both are ready. The interactive canvas displays **all points remaining after the enabled filters**, with no additional automatic preview reduction. Disable the voxel filter to retain the full point density, or enable it explicitly to improve responsiveness for large scans. The **full-resolution export** uses the full quality-filtered clouds without the display voxel filter; a direct export of the interactive canvas captures the displayed points.

The normalized SD is the percentage requested for the reviewer's “dynamic range” column; **Normalized SD / axial range (%)** is a precise column label. The sample SD is calculated about the arithmetic mean with denominator N−1. The percentile intervals describe the empirical distribution of point deviations, not a complete GUM measurement-uncertainty evaluation.

The reference is indexed in a KD-tree. The selected project cloud is queried in chunks of 100,000 points. By default, all selected-cloud points are analysed. You can set **Maximum source points** to a limit to use a reproducible random sample for faster analysis. Display-only decimation is not used for the calculation.

The **Reference edge margin** excludes a narrow outer band of the reference footprint to avoid boundary artifacts. Its effective width is capped at 2% of the shorter reference span and is shown in the report. System points within reference area counts all measurement points inside the projected reference coverage, regardless of Z error or this edge band. Every analysed point inside the remaining reference area contributes its full unsigned nearest-reference distance to the statistics; there is no 3-D error cutoff. Enclosed gaps in the reference coverage are also evaluated. Only points outside the reference footprint or its edge band are grey in the map. By default the application replaces the selected project cloud in the plot with a pointwise error map. **Closest-reference distance** uses the `turbo` colour scale, capped visually at P95 so isolated large errors do not compress the useful colour range; those errors still count in all statistics. The mean is marked on the colour bar. The optional **Difference from mean distance** mode instead colours `d_i - mean(d)` with a blue-white-red scale centred at zero. This changes only the colours; the report always uses `d_i`. Enable **Highlight errors above the mean in red** if a binary high-error accent is helpful. The report contains the total and analysed source points, reference points indexed, effective edge margin, both explicitly named coverage fractions, the number of points used for error statistics, and, for those points only:

- mean unsigned distance (often described as MAE here);
- 5th percentile (P5), a robust lower-end value that one unusually close point cannot determine;
- median unsigned distance;
- RMSE, `sqrt(mean(d_i^2))`;
- 95th percentile (P95); and
- maximum distance.

All values are displayed in the configured distance unit (default: millimetres) after scaling. Unsigned mode reports nonnegative nearest-point magnitudes; signed mode reports local normal deviations. Neither method alone supplies measurement uncertainty bounds or establishes material loss, deflection, or independent ground-truth accuracy. For normal-direction change analysis with local roughness/registration uncertainty, M3C2 is an established alternative; see [Lague, Brodu & Leroux (2013)](https://doi.org/10.1016/j.isprsjprs.2013.04.009). The existing unsigned-map description above applies to unsigned mode; signed maps use the selected signed deviations and the bounds described above. **Difference from mean deviation** subtracts the mean for colours only: white then denotes the mean deviation, not the reference surface.

### Exact X-Y coverage calculation

Coverage uses the transformed, quality-filtered clouds with finite XYZ coordinates, before the optional error-analysis sample. Z distances and the reference edge exclusion do not affect either coverage value.

- **System points within reference area [%]** is `100 * N_inside / N_system`, where every system point is tested against the existing reference comparison mask. This is the previous surface-error `overlap_fraction`, now explicitly named `system_points_within_reference_area_fraction`. The old report keys remain as compatibility aliases for saved projects; they are not additional metrics.
- **Reference area covered [%]** is `100 * A_covered / A_reference`. The denominator is the area of the existing reference mask, including its enclosed filled gaps and excluding no edge band. Each occupied reference-mask cell contributes the same area `h_reference²`. A cell contributes to the numerator if its centre lies in the locally supported system footprint, with a one-cell boundary tolerance described below. No reference-point or system-point count weights this area ratio.

For the reference, retain the existing comparison grid exactly. Its cell width is `h = max(0.5 * s95, longest_XY_span / 1500, sqrt(XY_bounding_box_area / 2_000_000), 0.05)` in the configured coordinate unit. `s95` is the 95th percentile of positive nearest-neighbour X-Y spacings, queried against the full reference cloud at up to 20,000 evenly indexed samples. The grid origin is `min(XY) - 2h`, its shape is `ceil(XY_span / h) + 5`, and point positions map to cells by flooring `(XY - origin) / h`. The reference occupancy undergoes a 3-by-3 binary closing followed by filling enclosed holes, as already used for error selection.

The system footprint connects samples using a **local Delaunay triangulation**, rather than counting occupied system grid cells. Duplicate X-Y positions are removed and sorted. At each remaining system position, local spacing is the median distance to its nearest six other positions (or all others if fewer exist). A triangle is accepted only if **every** edge has length at most `4 * min(local_spacing_at_endpoint_1, local_spacing_at_endpoint_2)`. The system footprint is the union of accepted triangles: this interpolates the normal gaps between sparse, irregular samples and adapts to local density, while rejecting long connections across missing patches or disconnected scans. It does not simply fill the entire convex hull or every enclosed hole.

To bound triangulation memory, system clouds with more than 200,000 distinct X-Y positions are simplified by retaining the first actual sample in each fine grid cell. The simplification cell width starts at `max(longest_XY_span / 1500, sqrt(XY_bounding_box_area / 100_000))` and is multiplied by 1.5 until at most 200,000 cells are occupied. Local spacing and triangulation are calculated from these retained positions. This simplification affects only the coverage footprint; all full-cloud system points still contribute to the point fraction and the existing error calculation.

Reference-cell centres are tested against accepted triangles in chunks, also evaluating the one-cell neighbourhood of the reference mask. The resulting support raster receives a single 3-by-3 binary dilation before intersecting it with the reference mask. This one-cell tolerance compensates for the reference occupancy boundary extending beyond the outermost reference samples; it can also bridge gaps narrower than two reference cells. The covered-cell count times `h_reference²` gives the numerator area. A sparse system can cover the same area as a dense system; adding duplicate system points cannot change its area coverage. A system extending far beyond the reference can have a low point fraction and still cover nearly 100% of the reference area.

This is an estimate of projected area, not 3-D surface area. Its interpolation assumes that gaps within the local spacing threshold represent continuous measured coverage. Larger gaps remain uncovered; sampling alone cannot distinguish a small real hole from an ordinary inter-sample gap. The numeric report stores `reference_area`, `reference_area_covered`, `area_unit`, reference grid cell width, system support-point count, simplification cell width, edge factor, and method identifier `xy_local_delaunay_cell_centres_v2` for reproducibility. Reference clouds with fewer than three points or an effectively zero X or Y span have no usable 2-D mask: area coverage is reported as unavailable, while their existing point-fraction and error behavior is preserved. A system with fewer than three distinct X-Y positions or collinear positions contributes zero area. Older saved reports show “not saved; recalculate” when the area metric is absent. Saved v1 area values are retained until the comparison is recalculated.

## Reporting the results in a paper

### Methods text you can adapt

> Each project point cloud was converted to the reference coordinate convention by applying the recorded axis inversions, uniform scale factor, and rigid pose. Coarse registration used voxel-downsampled point clouds and competing centre-of-gravity, PCA-orientation, and FPFH-feature/RANSAC initialisations. Each candidate was refined by three-scale robust point-to-plane ICP with Tukey loss. The candidate with the largest selected-cloud overlap, followed by the smallest bidirectional 80%-trimmed nearest-neighbour RMSE, was retained. Surface comparison was then performed from the registered project cloud to the full reference cloud as unsigned nearest-surface Euclidean distance. Only points inside the measured reference footprint, excluding its outer boundary band, were included with their full distances; points outside the footprint or edge band were excluded from error statistics.

Replace the generic statements with the values actually shown in the result dialog/log for each run. State explicitly that the reference `Z` axis was inverted if that was part of the coordinate convention. This is a coordinate correction, not an algorithmic reflection applied after registration.

### Minimum reproducibility information

Report the following once in the Methods section and, where it varies, per dataset in supplementary material:

| Item | What to report |
| --- | --- |
| Coordinate convention | Units, uniform scale factor, which axes were inverted, and the order of transformations. |
| Input and registration density | Original point counts; actual registration point counts and voxel size `v`. |
| Coarse registration | That the previous global PCA/centre-of-gravity/FPFH-RANSAC workflow was used; the selected initialisation for each cloud. |
| FPFH/RANSAC settings | Normal radius `2.5v`, FPFH radius `6v`, RANSAC distance `2.5v`, three-point hypotheses, edge check `0.9`, 100,000 maximum iterations, confidence `0.999`. |
| ICP settings | Point-to-plane ICP, Tukey loss, radii `8v`, `3v`, `1.25v`, and 80 iterations per scale. |
| Registration acceptance | Source/reference/symmetric overlap and 80%-trimmed bidirectional registration RMSE; visual or landmark quality-control rule. |
| Comparison rule | Direction (project -> reference), unsigned Euclidean nearest-surface distance, reference edge margin, analysed-point cap or `All source points`, and whether sampling was used. |
| Regions | The physical overlap or ROI used for each comparison, and how defect regions were defined independently of the error result. |

For every project cloud, a compact results table should include at least:

| Cloud | Error method | Analysed / evaluated points | System points within reference area [%] | Reference area covered [%] | [P5; P95] | Sample SD | Normalized SD / axial range [%] |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| Project A | e.g. signed local normal | ... | ... | ... | ... | ... | ... |

Use one distance unit consistently in the table (for example, mm). Report the empirical **[P5; P95]** interval alongside **sample SD**; the percentile interval describes the central 90% of the deviation distribution, while SD also reflects the tails. Normalize SD by the system's axial measurement span for the requested percentage column. The maximum and RMSE remain useful diagnostics of larger deviations.

Keep two quantities distinct in the text and table:

1. **Registration trimmed RMSE** evaluates the downsampled correspondences used to choose a transform. It is useful for registration quality control.
2. **Surface-comparison distance statistics** evaluate the final project-to-reference distances at the chosen sampling density and reference edge margin. These are the values to use for measured geometric deviation.

Because the same data help estimate the transformation and then are compared, the comparison is potentially optimistic. For a claim of independent measurement accuracy, estimate the pose on a registration ROI/landmarks and evaluate distances on a spatially separate hold-out ROI or independent check targets. When comparing several systems, summarise each scan/ROI first and then compare the per-scan summaries (for example median and interquartile range); pooling all points would let the densest scan dominate the result.

### Recommended figures

| Figure | What it shows | Good practice |
| --- | --- | --- |
| Before/after overlay | Whether the rigid pose is physically credible. | Use the same camera, axis limits, equal aspect where possible, colours, and crop in both panels. Include at least one close-up of a distinctive region. The current **Export Plot** can export this overlay. |
| Colour-coded distance cloud | Where the unsigned project-to-reference deviation occurs. | Use one fixed colour scale and the same display clipping threshold for every system; show the colour bar and units. Clip only for display and disclose the clipping threshold. |
| ECDF or histogram of distances | The full distribution, including tails. | An ECDF is often clearer than bins. Mark the acceptance tolerance; use identical axes across systems. |
| Box/violin plot per project or system | Comparable central tendency and spread over scans/ROIs. | Plot one summary per independent scan/ROI, not millions of individual points as independent observations. Show sample size and overlap fraction. |
| Spanwise/chordwise error profile | Localised defects and systematic drift along the blade. | Bin points along a physically defined blade coordinate; plot median and P95 per bin, plus the number of overlap points in each bin. |
| Cross-sections at defects | Whether a local apparent deviation is geometric rather than an overlap artefact. | Use the same section planes for reference and all projects, show the reference and measured profiles together, and annotate the local distance scale. |
| Coverage/overlap footprint | Which part of the blade actually contributed to each statistic. | Plot the evaluated overlap points separately from non-overlap areas, so absence of data is never read as zero error. |

The application can export both the normal overlay and the current pointwise error map through **Export Plot**. Use **Data & Display -> Analysis Display -> Show latest pointwise error map** to switch the calculated map on or off without recalculating it. Histograms/ECDFs, profile plots, and cross-sections remain recommended analysis outputs; preserve the fixed scale, display clipping threshold, ROI, and axis convention in their figure captions. A strong paper figure set is usually: one before/after overlay, one fixed-scale distance map with defect close-ups, one distribution plot, and one spatial profile or cross-section.
