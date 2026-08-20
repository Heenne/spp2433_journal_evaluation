# 3D Point Cloud Data Viewer (spp2433_journal_evaluation)

A fast, local Python desktop application built with **PyQt6** and **matplotlib** to evaluate, filter, and visualize dense 3D surface scan data from CSV files.

## Features

- **Robust CSV Parsing**: Dynamically detects `X`, `Y`, and `Z` coordinates regardless of capitalization, and automatically ignores comment blocks like `//` in the headers. Retains extra columns (Intensity, Return Number, etc.) for visualization.
- **Smart Filtering & Downsampling**: Includes intuitive sliders to decimate the point cloud (e.g., keep 1 in every 10 points) or take a random percentage sample to keep the application responsive with massive datasets.
- **Caching Mechanism**: Save your filtered datasets locally. The app will automatically detect optimized datasets the next time you load the original file, saving significant loading time.
- **Project Toolbar & Safe Saving**: Icon actions provide Open, Open Project, Save, Save As, conversion, reference selection, and recent projects. Projects preserve cloud order and visibility; Save writes to the open project, while Save As creates a separate backup. Unsaved changes are flagged and confirmed on close.
- **3D Visualization**: Render points in an interactive 3D space. Apply dynamic color mapping using any of the additional columns in your dataset.
- **Stable Inspection View**: Keep the current 3-D camera orientation, zoom, and pan while applying manual transforms or refreshing the plot.
- **Camera Orientation Pad**: Jump to `±X`, `±Y`, or `±Z` views, return to isometric, or rotate the current view in 90° increments for axis-by-axis manual alignment.
- **List-ordered Overlay Display**: The first visible cloud in the loaded-cloud list is drawn above all others, then the second, and so on. Use **Move Up** / **Move Down** to set the display layer order; project saves retain this list order. It is display-only and never changes coordinates or error calculations.
- **Bounded Manual Fine Alignment**: Refine a rough manual pose with an iterative, robust closest-point optimizer. It works around the initial overlap pivot, freezes the manually overlapping footprint, provides independent `+/- X/Y/Z` and `+/- Rx/Ry/Rz` bounds, and accepts a change only when the bidirectional anchored score measurably improves. It deliberately does not use ambiguous centre-of-gravity, PCA, or global feature initializers.
- **Previous Global Alignment (PCA / FPFH)**: Retains the broad automatic workflow: centre-of-gravity and PCA orientation candidates plus FPFH/RANSAC feature matching, each refined by robust coarse-to-fine ICP. It is useful when no good manual pose is available, but needs visual validation on small, smooth, or repetitive blade areas.
- **Surface-Error Report**: Calculate source-to-reference nearest-surface distances for only the overlapping area, with coverage, mean, median, RMSE, P95, and maximum deviation.
- **Pointwise Error Map**: After a surface-error calculation, colour every analysed project-cloud point from low to high nearest-surface error. The colour bar marks the mean; points outside the overlap cutoff are grey and points above the mean can optionally be overlaid in red. Export the current view as a report figure.
- **High-Quality Export**: Export your generated plots to static formats (PNG/JPEG) or vector graphics (SVG) for reports and presentations.

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
2. In **Manual Transform**, set **Uniform scale** if the files use different units. For example, use `1000` when the selected measurement is in metres and the reference is in millimetres. Scale is applied before rotation and translation.
3. If possible, use the manual transform controls to place the scans approximately together. This is especially useful for a small project scan against a much larger reference scan.
4. If you need the previous broad PCA/centre-of-gravity/FPFH method, open **Legacy Alignment** and use **Run Previous Global Auto Align**. It uses the current transformed cloud coordinates, including enabled axis inversions.
5. In **Fine Align & Error**, use **Bounded Manual Fine Alignment** to choose the reference and set independent `+/- X`, `+/- Y`, `+/- Z` translation limits plus `+/- Rx`, `+/- Ry`, `+/- Rz` Euler-angle limits. They are corrections relative to the current manual pose at the overlap pivot; set an axis to `0` to lock it. Use values that reflect your manual uncertainty (for example, a few centimetres and a few degrees), rather than the full scan size, then click **Optimise Manual Alignment**. The result is saved only if the frozen two-sided overlap improves measurably; otherwise the manual pose is retained unchanged.
6. In the same tab under **Surface Error**, choose the same reference, set an **Overlap / error cutoff**, and click **Calculate Surface Error**. Only selected-cloud points within this cutoff are included in the error statistics. Points outside it are reported as non-overlap, so regions measured by only one scan do not inflate the error.

The default registration limit is 30,000 adaptive voxel points per cloud. The default comparison limit is 250,000 selected-cloud points; a deterministic random sample is used for larger clouds. Set **Maximum source points** to `All source points` when a complete report is worth the extra processing time. The full reference is indexed with a KD-tree and source queries are processed in chunks.

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

After an accepted pose is saved, **Calculate Surface Error** computes the unsigned Euclidean nearest-neighbour distance for every analysed selected-cloud point to the full reference cloud:

`d_i = min_{q in reference} ||p_i - q||_2`

The reference is indexed in a KD-tree. The selected project cloud is queried in chunks of 100,000 points. By default, at most 250,000 selected-cloud points are sampled with a fixed random seed, so repeating the same comparison and settings gives the same sample. Choose **All source points** when the extra runtime is acceptable. Display-only decimation is not used for the calculation.

The **Overlap / error cutoff** is essential for partial scans. Only points with `d_i` at or below that cutoff enter the error statistics; more distant points are reported as *non-overlap*, not assigned a very large error. By default the application also replaces the selected project cloud in the plot with a pointwise error map for exactly the analysed points. **Closest-reference distance** is the default: low-to-high `d_i` values use the `turbo` colour scale, the mean is marked on the colour bar, and non-overlap points are grey. The optional **Difference from mean distance** mode instead colours `d_i - mean(d)` with a blue-white-red scale centred at zero. Enable **Highlight errors above the mean in red** if a binary high-error accent is helpful. The report contains the total and analysed source points, reference points indexed, cutoff, overlap count/fraction, non-overlap count, and, for overlap points only:

- mean unsigned distance (often described as MAE here);
- median unsigned distance;
- RMSE, `sqrt(mean(d_i^2))`;
- 95th percentile (P95); and
- maximum distance.

All values are in the data-coordinate unit after scaling—usually millimetres if the reference is in millimetres. The present calculation is **unsigned nearest-surface Euclidean distance**. It does not determine whether a point is above/below the reference surface, does not measure distance along a surface normal, and does not itself provide uncertainty bounds. Therefore it is appropriate to describe it exactly as an unsigned closest-surface deviation, not as signed thickness loss, signed blade deflection, or absolute ground-truth accuracy. For a future signed, normal-direction change analysis with local roughness/registration uncertainty, M3C2 is a relevant established approach; see [Lague, Brodu & Leroux (2013)](https://doi.org/10.1016/j.isprsjprs.2013.04.009).

## Reporting the results in a paper

### Methods text you can adapt

> Each project point cloud was converted to the reference coordinate convention by applying the recorded axis inversions, uniform scale factor, and rigid pose. Coarse registration used voxel-downsampled point clouds and competing centre-of-gravity, PCA-orientation, and FPFH-feature/RANSAC initialisations. Each candidate was refined by three-scale robust point-to-plane ICP with Tukey loss. The candidate with the largest selected-cloud overlap, followed by the smallest bidirectional 80%-trimmed nearest-neighbour RMSE, was retained. Surface comparison was then performed from the registered project cloud to the full reference cloud as unsigned nearest-surface Euclidean distance. Only points within the pre-specified overlap cutoff were included; excluded points were reported as non-overlap.

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
| Comparison rule | Direction (project -> reference), unsigned Euclidean nearest-surface distance, error cutoff, analysed-point cap or `All source points`, and whether sampling was used. |
| Regions | The physical overlap or ROI used for each comparison, and how defect regions were defined independently of the error result. |

For every project cloud, a compact results table should include at least:

| Cloud | Selected initialisation | Source overlap | Registration trimmed RMSE | Analysed / overlap points | Comparison overlap | Mean | Median | RMSE | P95 | Maximum |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Project A | e.g. global FPFH/RANSAC | ... | ... | ... | ... | ... | ... | ... | ... | ... |

Use one unit consistently in the table (for example, mm). The **median** and **P95** are usually the most informative headline values for a heavy-tailed error distribution; the **RMSE** shows the effect of larger deviations. Give the **mean** as well if desired, but do not report only a mean. The maximum is useful as a diagnostic, but is highly sensitive to isolated noise, edge effects, and a few bad correspondences.

Keep two quantities distinct in the text and table:

1. **Registration trimmed RMSE** evaluates the downsampled correspondences used to choose a transform. It is useful for registration quality control.
2. **Surface-comparison distance statistics** evaluate the final project-to-reference distances at the chosen sampling density and cutoff. These are the values to use for measured geometric deviation.

Because the same data help estimate the transformation and then are compared, the comparison is potentially optimistic. For a claim of independent measurement accuracy, estimate the pose on a registration ROI/landmarks and evaluate distances on a spatially separate hold-out ROI or independent check targets. When comparing several systems, summarise each scan/ROI first and then compare the per-scan summaries (for example median and interquartile range); pooling all points would let the densest scan dominate the result.

### Recommended figures

| Figure | What it shows | Good practice |
| --- | --- | --- |
| Before/after overlay | Whether the rigid pose is physically credible. | Use the same camera, axis limits, equal aspect where possible, colours, and crop in both panels. Include at least one close-up of a distinctive region. The current **Export Plot** can export this overlay. |
| Colour-coded distance cloud | Where the unsigned project-to-reference deviation occurs. | Use one fixed colour scale and the same cutoff for every system; show the colour bar and units. Clip only for display and disclose the clipping threshold. |
| ECDF or histogram of distances | The full distribution, including tails. | An ECDF is often clearer than bins. Mark the acceptance tolerance and the overlap cutoff; use identical axes across systems. |
| Box/violin plot per project or system | Comparable central tendency and spread over scans/ROIs. | Plot one summary per independent scan/ROI, not millions of individual points as independent observations. Show sample size and overlap fraction. |
| Spanwise/chordwise error profile | Localised defects and systematic drift along the blade. | Bin points along a physically defined blade coordinate; plot median and P95 per bin, plus the number of overlap points in each bin. |
| Cross-sections at defects | Whether a local apparent deviation is geometric rather than an overlap artefact. | Use the same section planes for reference and all projects, show the reference and measured profiles together, and annotate the local distance scale. |
| Coverage/overlap footprint | Which part of the blade actually contributed to each statistic. | Plot the evaluated overlap points separately from non-overlap areas, so absence of data is never read as zero error. |

The application can export both the normal overlay and the current pointwise error map through **Export Plot**. Use **Data & Display -> Analysis Display -> Show latest pointwise error map** to switch the calculated map on or off without recalculating it. Histograms/ECDFs, profile plots, and cross-sections remain recommended analysis outputs; preserve the fixed scale, cutoff, ROI, and axis convention in their figure captions. A strong paper figure set is usually: one before/after overlay, one fixed-scale distance map with defect close-ups, one distribution plot, and one spatial profile or cross-section.
