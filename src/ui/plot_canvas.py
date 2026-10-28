import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.cm as cm
from src.utils.error_mapping import error_map_colours

class PlotCanvas(FigureCanvas):
    # Show the full filtered clouds by default. A preview budget can still be
    # set explicitly, but must not silently reduce an unfiltered live view.
    MAX_PREVIEW_POINTS = None

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self._rendering_suspended = False
        self._draw_deferred = False
        self._deferred_datasets = None
        self.preview_point_counts = []
        self.fig = Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        self.axes = self.fig.add_subplot(111, projection='3d')
        # Matplotlib's 3-D axes normally reorder entire scatter collections by
        # depth. Keeping explicit z-orders lets the user deliberately overlay
        # a selected cloud while finding a rough manual pose.
        self.axes.computed_zorder = False
        
        super(PlotCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.colorbars = []
        self._preview_notice = self.fig.text(0.01, 0.01, "", fontsize=8, color="0.35")
        self._has_plotted_data = False
        self._visible_dataset_ids = ()
        self._fitted_limits = None
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()
        self.mpl_connect('scroll_event', self._on_scroll)
        
    def _on_scroll(self, event):
        if event.inaxes != self.axes:
            return
            
        base_scale = 1.1
        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            return
            
        cur_xlim = self.axes.get_xlim3d()
        cur_ylim = self.axes.get_ylim3d()
        cur_zlim = self.axes.get_zlim3d()

        xdata = event.xdata if event.xdata is not None else sum(cur_xlim)/2
        ydata = event.ydata if event.ydata is not None else sum(cur_ylim)/2
        zcenter = sum(cur_zlim)/2

        new_xlim = [xdata - (xdata - cur_xlim[0]) * scale_factor, xdata + (cur_xlim[1] - xdata) * scale_factor]
        new_ylim = [ydata - (ydata - cur_ylim[0]) * scale_factor, ydata + (cur_ylim[1] - ydata) * scale_factor]
        new_zlim = [zcenter - (zcenter - cur_zlim[0]) * scale_factor, zcenter + (cur_zlim[1] - zcenter) * scale_factor]

        self.axes.set_xlim3d(new_xlim)
        self.axes.set_ylim3d(new_ylim)
        self.axes.set_zlim3d(new_zlim)
        self.draw_idle()

    def set_standard_view(self, view_name: str):
        """Set a named orthographic-style inspection direction without redrawing data."""
        views = {
            "positive_x": (0.0, 0.0, 0.0),
            "negative_x": (0.0, 180.0, 0.0),
            "positive_y": (0.0, 90.0, 0.0),
            "negative_y": (0.0, -90.0, 0.0),
            "top": (90.0, -90.0, 0.0),
            "bottom": (-90.0, -90.0, 0.0),
            "isometric": (30.0, -60.0, 0.0),
            # User-selected diagonal inspection orientation.
            "diagonal_negative_x_positive_y_positive_z": (-30.0, -45.0, 180.0),
        }
        if view_name not in views:
            return
        elev, azim, roll = views[view_name]
        self.axes.view_init(elev=elev, azim=azim, roll=roll)
        self.draw_idle()

    def set_camera_angles(self, elevation: float, azimuth: float, roll: float = 0.0):
        """Set explicit Matplotlib camera orientation angles in degrees."""
        self.axes.view_init(elev=float(elevation), azim=float(azimuth), roll=float(roll))
        self.draw_idle()

    def camera_angles(self) -> tuple[float, float, float]:
        """Return the currently active elevation, azimuth, and roll in degrees."""
        return float(self.axes.elev), float(self.axes.azim), float(getattr(self.axes, "roll", 0.0))

    def rotate_camera_around_vertical(self, degrees: float):
        """Rotate the current inspection direction in 90-degree increments."""
        self.axes.view_init(elev=self.axes.elev, azim=self.axes.azim + degrees)
        self.draw_idle()

    def reset_view_to_data(self):
        """Fit the current axes to the last plotted visible point-cloud extent."""
        if self._fitted_limits is None:
            return

        xlim, ylim, zlim = self._fitted_limits
        self.axes.set_xlim3d(xlim)
        self.axes.set_ylim3d(ylim)
        self.axes.set_zlim3d(zlim)
        self.draw_idle()

        
    def plot_datasets(self, datasets: list):
        if self._rendering_suspended:
            self._deferred_datasets = datasets
            self._draw_deferred = True
            return
        # ``cla`` resets the 3-D camera. Preserve it after the first plot so a
        # manual transform updates the geometry without losing the user's
        # zoomed/panned inspection view.
        visible_dataset_ids = tuple(
            id(d) for d in datasets
            if d.get("visible", False) and "df_filtered" in d and not d["df_filtered"].empty
        )
        # Keep a user's inspection view while refreshing the same clouds (for
        # example after a small transform).  A different visible cloud needs a
        # fresh fitted extent; otherwise it may be completely outside the old
        # zoom window after being loaded.
        preserve_limits = self._has_plotted_data and visible_dataset_ids == self._visible_dataset_ids
        view_state = None
        if preserve_limits:
            view_state = {
                "elev": self.axes.elev,
                "azim": self.axes.azim,
                "roll": getattr(self.axes, "roll", None),
                "xlim": self.axes.get_xlim3d(),
                "ylim": self.axes.get_ylim3d(),
                "zlim": self.axes.get_zlim3d(),
            }

        # A colourbar changes the parent axes' layout. Remove it *before*
        # clearing those axes; doing this in the opposite order leaves some
        # Matplotlib versions with a detached colourbar axes and crashes on
        # the next redraw (for example when a cloud is hidden).
        if hasattr(self, 'colorbars'):
            previous_colorbars = self.colorbars
            self.colorbars = []
            for cb in previous_colorbars:
                try:
                    if getattr(cb, "ax", None) is not None:
                        cb.remove()
                except (AttributeError, KeyError, ValueError):
                    # Be defensive about colourbars created before this fix:
                    # their axes may already have been detached by ``cla``.
                    colorbar_axes = getattr(cb, "ax", None)
                    if colorbar_axes is not None:
                        try:
                            self.fig.delaxes(colorbar_axes)
                        except (KeyError, ValueError):
                            pass
        else:
            self.colorbars = []

        self.axes.cla() # Clear axes after restoring the original layout
                
        visible_datasets = [d for d in datasets if d.get("visible", False) and "df_filtered" in d and not d["df_filtered"].empty]
        self.preview_point_counts = []
        self._preview_notice.set_text("")
        per_cloud_limit = (
            max(1, self.MAX_PREVIEW_POINTS // max(1, len(visible_datasets)))
            if self.MAX_PREVIEW_POINTS is not None else None
        )
        
        if not visible_datasets:
            self._visible_dataset_ids = ()
            self._fitted_limits = None
            self.draw()
            return
            
        x_min, x_max = float('inf'), float('-inf')
        y_min, y_max = float('inf'), float('-inf')
        z_min, z_max = float('inf'), float('-inf')
        
        colorbar_added = False
        error_map_shown = False
        
        for layer_index, d in enumerate(visible_datasets):
            df = d["df_filtered"]
            st = d["settings"]
            name = d["name"]
            # The list is the layer stack: its first visible cloud is painted
            # last/highest, then each following one lies underneath it.
            zorder = len(visible_datasets) - layer_index + 1
            
            x = df['X'].to_numpy(dtype=float, copy=False)
            y = df['Y'].to_numpy(dtype=float, copy=False)
            z = df['Z'].to_numpy(dtype=float, copy=False)

            error_map = d.get("error_visualization") if d.get("show_error_visualization", False) else None
            if error_map is not None:
                points = np.asarray(error_map.get("points"), dtype=float)
                distances = np.asarray(error_map.get("distances"), dtype=float)
                valid = points.ndim == 2 and points.shape[1] == 3 and len(points) == len(distances)
                if valid and len(points):
                    x, y, z = points[:, 0], points[:, 1], points[:, 2]
                else:
                    error_map = None
            
            x_min, x_max = min(x_min, np.nanmin(x)), max(x_max, np.nanmax(x))
            y_min, y_max = min(y_min, np.nanmin(y)), max(y_max, np.nanmax(y))
            z_min, z_max = min(z_min, np.nanmin(z)), max(z_max, np.nanmax(z))
            full_count = len(x)
            indices = None
            if per_cloud_limit is not None and full_count > per_cloud_limit:
                # Regular row strides alias with raster/scan-line acquisition
                # order, turning smooth surfaces into artificial bands. A fixed
                # random sample avoids that pattern and stays stable on refresh.
                indices = np.sort(np.random.default_rng(0).choice(
                    full_count, size=per_cloud_limit, replace=False
                ))
            normalization_distances = None
            if error_map is not None and indices is not None:
                full_overlap = np.isfinite(distances)
                if np.any(full_overlap):
                    normalization_distances = distances[full_overlap]
                    indices[0] = np.argmax(full_overlap)
                if len(indices) > 1 and not np.all(full_overlap):
                    indices[1] = np.argmin(full_overlap)
            if indices is not None:
                x, y, z = x[indices], y[indices], z[indices]
                if error_map is not None:
                    distances = distances[indices]
            self.preview_point_counts.append((full_count, len(x)))
            
            if error_map is not None:
                distance_unit = error_map.get("unit", "mm")
                in_overlap = np.isfinite(distances)
                point_size = 8
                if np.any(in_overlap):
                    colour_values, colour_kwargs, colourbar_label, mean_marker = error_map_colours(
                        distances[in_overlap], error_map, normalization_distances=normalization_distances
                    )
                    scatter = self.axes.scatter(
                        x[in_overlap], y[in_overlap], z[in_overlap], c=colour_values,
                        marker='.', s=point_size, zorder=zorder, depthshade=False, **colour_kwargs,
                        label=f"{name} error", axlim_clip=True,
                    )
                    cb = self.fig.colorbar(
                        scatter, ax=self.axes, label=colourbar_label, pad=0.1
                    )
                    self.colorbars.append(cb)
                    if mean_marker is not None and np.isfinite(mean_marker):
                        cb.ax.axhline(float(mean_marker), color="white", linewidth=1.5)
                        cb.ax.axhline(float(mean_marker), color="black", linewidth=0.5, linestyle="--")
                    colorbar_added = True
                if np.any(~in_overlap):
                    self.axes.scatter(
                        x[~in_overlap], y[~in_overlap], z[~in_overlap], c="0.55", marker='.', s=point_size,
                        label=f"{name} excluded from error statistics", zorder=zorder, axlim_clip=True,
                    )
                if error_map.get("highlight_above_mean") and error_map.get("mean") is not None:
                    above_mean = in_overlap & (distances > float(error_map["mean"]))
                    if np.any(above_mean):
                        self.axes.scatter(
                            x[above_mean], y[above_mean], z[above_mean], c="red", marker='.', s=point_size,
                            label=f"{name} > mean error", zorder=zorder + 1, axlim_clip=True,
                        )
                error_map_shown = True
                continue

            color_col = st.get("color_col")
            base_color = st.get("base_color", "b")
            
            if color_col and color_col in df.columns:
                c = df[color_col].to_numpy()
                colour_min, colour_max = df[color_col].min(), df[color_col].max()
                if indices is not None:
                    c = c[indices]
                scatter = self.axes.scatter(
                    x, y, z, c=c, cmap=cm.viridis, vmin=colour_min, vmax=colour_max,
                    marker='.', s=10, label=name, zorder=zorder,
                    axlim_clip=True,
                )
                if not colorbar_added:
                    cb = self.fig.colorbar(scatter, ax=self.axes, label=color_col, pad=0.1)
                    self.colorbars.append(cb)
                    colorbar_added = True
            else:
                self.axes.scatter(
                    x, y, z, c=base_color, marker='.', s=10, label=name, zorder=zorder, axlim_clip=True
                )
            
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')
        self.axes.set_zlabel('Z')
        if error_map_shown:
            self.axes.set_title("Pointwise deviation from reference")
        preview_summary = self.preview_summary()
        self._preview_notice.set_text(preview_summary)
        if preview_summary:
            # Preserve the full cloud extent, even when an isolated extreme
            # point is absent from the interactive display sample.
            self.axes.auto_scale_xyz([x_min, x_max], [y_min, y_max], [z_min, z_max])
        
        if self.axes.collections:
            handles, labels = self.axes.get_legend_handles_labels()
            if labels:
                self.axes.legend(loc="upper right")
        
            # Lock the axis ratio to true data proportions
            x_range = x_max - x_min
            y_range = y_max - y_min
            z_range = z_max - z_min
            
            x_range = x_range if x_range > 0 else 1.0
            y_range = y_range if y_range > 0 else 1.0
            z_range = z_range if z_range > 0 else 1.0
            
            try:
                self.axes.set_box_aspect((x_range, y_range, z_range))
            except AttributeError:
                pass

            # Matplotlib has just auto-scaled the scatter collections.  Keep
            # that complete-data extent for the toolbar's Home action.
            self._fitted_limits = (
                self.axes.get_xlim3d(),
                self.axes.get_ylim3d(),
                self.axes.get_zlim3d(),
            )

        if view_state is not None:
            try:
                if view_state["roll"] is None:
                    self.axes.view_init(elev=view_state["elev"], azim=view_state["azim"])
                else:
                    self.axes.view_init(
                        elev=view_state["elev"], azim=view_state["azim"], roll=view_state["roll"]
                    )
            except TypeError:
                # Older Matplotlib releases do not accept the roll argument.
                self.axes.view_init(elev=view_state["elev"], azim=view_state["azim"])
            self.axes.set_xlim3d(view_state["xlim"])
            self.axes.set_ylim3d(view_state["ylim"])
            self.axes.set_zlim3d(view_state["zlim"])

        self._has_plotted_data = True
        self._visible_dataset_ids = visible_dataset_ids
            
        self.draw_idle()

    def preview_summary(self):
        total = sum(full for full, shown in self.preview_point_counts)
        shown = sum(shown for full, shown in self.preview_point_counts)
        return f"Interactive preview: {shown:,} of {total:,} points; statistics unchanged." if shown < total else ""

    def export_plot(self, filepath: str):
        """Exports the current plot to the given filepath (png, jpg, svg)."""
        self.fig.savefig(filepath, format=filepath.split('.')[-1], bbox_inches='tight')

    def finish_pending_draw(self):
        """Complete queued rendering before another window needs its first paint."""
        # Matplotlib's Qt backend consumes its pending flag here, so the
        # queued timer cannot start a second costly draw after a dialog opens.
        self._draw_idle()

    def draw(self):
        if self._rendering_suspended:
            self._draw_deferred = True
            return
        super().draw()

    def draw_idle(self):
        if self._rendering_suspended:
            self._draw_deferred = True
            return
        super().draw_idle()

    def pause_rendering(self):
        """Keep plot redraws from blocking an open results window."""
        if self._rendering_suspended:
            return
        self._rendering_suspended = True
        self._updates_before_pause = self.updatesEnabled()
        self.setUpdatesEnabled(False)

    def resume_rendering(self):
        if not self._rendering_suspended:
            return
        self._rendering_suspended = False
        datasets, self._deferred_datasets = self._deferred_datasets, None
        redraw, self._draw_deferred = self._draw_deferred, False
        if datasets is not None:
            self.plot_datasets(datasets)
        elif redraw:
            self.draw_idle()
        self.setUpdatesEnabled(self._updates_before_pause)
