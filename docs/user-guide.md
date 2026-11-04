# User guide

This guide takes a first-time user from point-cloud files to a saved comparison. Interface labels below use their English names; switch the app language with **EN / DE** if needed.

## 1. Prepare the files

The app reads comma-separated `.csv` files and binary `.ply` point clouds. Both need three numeric coordinates named `X`, `Y`, and `Z` (the names are case-insensitive). CSV files need a header row. Extra columns are retained and can be used for colour mapping. Make sure the coordinates are finite and understand each file's units before alignment.

The project file keeps settings and refers to source files by path. It does not copy the point data into the project. Keep the source files in place, or reopen the project on a computer where those paths resolve.

## 2. Create a project and add clouds

1. Start the EXE and select **Add point cloud** in the top toolbar. Select one or more CSV/PLY files. Repeat to add files later.
2. Add the reference cloud and the measurement cloud(s) to the same project. The reference is simply the cloud you choose as the fixed comparison target; it does not need a special file type.
3. Select a cloud in the left **Point Clouds** list to edit its settings. Use its checkbox to show or hide it in the plot. The checkbox does not remove it from the project.
4. The list order controls drawing order: clouds nearer the top are drawn on top of clouds below. Use the up/down controls to change only the display order; this does not move the clouds or alter the analysis.
5. Use **Save as** to create a project JSON. Later, use **Save** to update it. Save after alignment and again after calculating results.

If the same raw file is loaded twice, both entries refer to that file but have separate project settings. For large files, a prompt may offer an existing cached/filtered CSV; choose it only if that saved data is the version you intend to analyse.

## 3. Set coordinates and make a rough placement

Select the measurement cloud and open **Align → Manual transform**.

- Set **Distance unit** to the unit used by the transformed coordinates and reports. This label does not convert coordinates.
- Use **Uniform scale** when the files use different units. For example, multiply a cloud in metres by `1000` to match a reference in millimetres.
- Use **Invert X/Y/Z** only when the input coordinate convention requires an axis reversal.
- Adjust **Translate X/Y/Z** and **Rotate X/Y/Z**, then click **Apply**. Rotations are applied about the coordinate origin after scale; translations are applied last.
- Toggle visibility or use the camera controls to inspect the overlay from useful views. The reference should remain fixed while you adjust the measurement.

Manual placement is usually the safest first step for partial scans. Bring the clouds into the same region and orientation before running a local optimizer.

## 4. Choose an alignment method

Open **Align** and select a method from **Alignment method**.

- **Bounded fine alignment**: Recommended when the clouds already overlap approximately. Choose both the selected cloud and fixed reference. Set independent plus/minus translation and rotation limits to match your expected placement error. Enter `0` to lock an axis. Click **Optimise alignment**. The app keeps the starting pose if the bounded fit does not improve its overlap score enough.
- **Global PCA / FPFH**: Use when you do not have a close starting pose. Set the reference and registration-point limit, then run **Run global alignment**. It searches several broad starting poses and refines them. Check the result visually; smooth or repetitive surfaces may admit an incorrect pose.
- **Standard ICP**: A local point-to-point refinement. It needs a reasonable starting pose and a useful **Max distance** (correspondence radius).
- **Robust ICP (Partial Overlap)**: A point-to-plane ICP option with a Tukey robust loss. It can reduce the influence of mismatched points, but it is still a local optimizer and can settle on a nearby wrong surface.

All alignment methods move the chosen source relative to the reference. They estimate rigid rotation and translation; they do not estimate scale. Use **Uniform scale** first if units differ. More detail on assumptions and parameters is in [Algorithms and result metrics](algorithms.md).

## 5. Filter only what you intend to exclude

Open **Filter** to change filters for the selected cloud. Z-Bounds, Z-Score, and SOR are used by bounded/global alignment, comparison, and filtered-cloud export. Voxel downsampling changes the interactive display and filtered-cloud export; each registration method controls its own working resolution. The legacy Standard/Robust ICP choices use only the transformed coordinates. See the [algorithms guide](algorithms.md) for the exact behavior.

- **Voxel Grid Downsampling** reduces density by representing points in 3-D cells. It is useful for a faster interactive view. The global aligner also chooses its own voxel size; that setting is separate.
- **Z-Score** removes points far from the mean in any coordinate axis.
- **SOR** (statistical outlier removal) removes isolated points based on their mean distance to nearby points.
- **Z-Bounds** keeps points between the selected minimum and maximum Z values.

Start with filters off. Enable one at a time and inspect what disappears, especially near edges and small defects. The project saves the filter settings; it does not overwrite the original data.

## 6. Calculate and read the comparison

In **Evaluate → Surface Error**, choose the measurement **Source** and fixed **Reference**. Set **Reference edge margin**, choose an error method, and click **Calculate error**. For large files, **Maximum source points** can use a repeatable sample; `0` means use all source points. Coverage fractions are calculated from the full clouds regardless of that sampling limit.

Use the error map to inspect where deviations occur. Points outside the reference footprint and points within the excluded outer edge band are grey. Colour-scale limits affect display only, not reported statistics. For signed local-plane error, set the normal radius, neighbour limit, and orientation deliberately; see the [metric definitions](algorithms.md#surface-error-methods-and-statistics).

The results dialog reports coverage, percentile intervals, standard deviation, and other descriptive statistics. Set **Axial measurement range** to the full physical span in the same unit as the deviations if you need **Normalized SD (%)**. For example, a range from -100 mm to +100 mm is a span of 200 mm.

Save the project after calculation to retain the numeric report. The display colour map itself is temporary and must be recalculated after reopening if you want to show or export it again.

## 7. Save point clouds and figures

- Use **Export Point Cloud** in the top toolbar for **Export filtered** or **Export centered**. A selected cloud can also be right-clicked in the list for these actions.
- **Export filtered** writes a new CSV with the selected cloud's current transforms and enabled filters. The original file stays unchanged.
- **Export centered** creates a separate copy translated to its centroid; it does not alter the source cloud in the project.
- Open **Export** to configure plot appearance, profiles, preview settings, and plot export. Use the preview to check labels, axes, legend, and colour scale before saving a figure.
- Project export profiles and preview-plot settings are stored in the project. Use the profile import button to copy a profile from another project or import an older standalone export-settings JSON.

## Troubleshooting

- **Clouds do not overlap:** Check units, axis direction, and translation/rotation. Use global alignment only for a broad initial search; use bounded fine alignment after a plausible manual placement.
- **No valid comparison points:** Check that the selected source overlaps the reference in X/Y, reduce the edge margin if appropriate, and inspect normal settings when using signed error.
- **Project reports missing files:** Restore the source files at their saved paths, or load them again and save the project.
- **Plot is slow:** Hide clouds you do not need, enable voxel downsampling for display, or set a source-point cap for the error calculation. The point-cloud export uses the selected filter settings.
