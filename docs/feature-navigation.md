# Feature navigation parity

The workspace keeps the 3-D plot visible while the right-hand tool section changes. The project and dataset list remains visible on the left.

| Existing capability | Workspace location |
| --- | --- |
| Open a project, load CSV/PLY data, TXT conversion, pixel-to-mm conversion, quick reference, save/recent projects | Top toolbar and left project sidebar |
| Dataset selection, visibility, remove, and display order | Left **Project and datasets** panel |
| Base colour, column colour mapping, pointwise error-map display, camera views and angles | **Data** |
| Stride/random sampling, voxel, Z-score, SOR, bounding box, cache/save filtered data, centre copy | **Prepare** |
| Axis inversion, scale, translation, rotation, presets, ICP | **Align → Manual transform** |
| Previous centre-of-gravity/PCA/FPFH workflow | **Align → Global alignment** |
| Bounded fine alignment, source/reference selection, surface-error calculation, report, heatmap controls | **Evaluate** |
| Preview, appearance, display/full-resolution export, import/export settings | **Export** |
| Light/dark theme | Top toolbar **Theme** menu; saved in the per-user application settings |

## Compatibility checklist

- Existing JSON projects and saved camera/error-report state continue to use the existing project loader and saver.
- CSV and PLY input, TXT conversion, and pixel-coordinate conversion remain attached to the same actions.
- Transform presets, all manual/global alignment methods, filters, error reports/maps, and export settings remain in the existing `ControlPanel` handlers.
- The UI navigation only changes where these controls appear; it does not change point-cloud transformations, project schemas, or export formats.
