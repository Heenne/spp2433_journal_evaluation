import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import LinearLocator, MultipleLocator
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
        self._last_datasets = []
        self.preview_options = {
            "use_heatmap": True, "use_heightmap": False, "heatmap_colormap": "auto",
            "heightmap_colormap": "viridis", "colourbar_height": 1.0, "colourbar_decimals": 2,
            "colourbar_label": "", "colourbar_label_font_size": 10.0,
            "colourbar_tick_font_size": 10.0, "point_size": 10.0,
            "x_label": "X", "y_label": "Y", "z_label": "Z",
            "axis_label_font_size": 10.0, "axis_tick_font_size": 10.0,
            "z_axis_label_spacing": 0.0, "z_axis_tick_label_gap": 0.0,
            "z_axis_ticks": 0, "z_axis_tick_interval": 0.0,
            "show_legend": True, "legend_point_size": 16.0,
            "legend_placement": "inside", "legend_position": "upper right",
            "legend_title": "", "legend_labels": {}, "legend_label_lines": [],
        }
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
        self.theme = "light"
        
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

    def set_preview_options(self, options: dict):
        """Apply saved appearance settings and redraw the current point clouds."""
        self.preview_options.update(options or {})
        if self._last_datasets:
            self.plot_datasets(self._last_datasets)
        else:
            self.draw_idle()

        
    def plot_datasets(self, datasets: list):
        self._last_datasets = datasets
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
        options = self.preview_options
        point_size = float(options.get("point_size", 2.0))
        axis_label_font_size = float(options.get("axis_label_font_size", 10.0))
        axis_tick_font_size = float(options.get("axis_tick_font_size", 10.0))
        heightmap_enabled = bool(options.get("use_heightmap", False))
        use_heatmap = bool(options.get("use_heatmap", True)) and not heightmap_enabled
        colourbar_added = False
        height_mappable = None
        height_min = min(float(d["df_filtered"]["Z"].min()) for d in visible_datasets)
        height_max = max(float(d["df_filtered"]["Z"].max()) for d in visible_datasets)
        if height_max <= height_min:
            height_max = height_min + np.finfo(float).eps
        height_cmap_name = options.get("heightmap_colormap", "viridis")
        if height_cmap_name == "height_blue_rose":
            height_cmap = LinearSegmentedColormap.from_list(
                "preview_height_blue_rose",
                ["#304D8B", "#5C80B7", "#93A8CC", "#CCB6C7", "#E9BAB1"], N=256,
            )
        else:
            height_cmap = cm.get_cmap(height_cmap_name)

        colorbar_format = f"%.{int(options.get('colourbar_decimals', 2))}f"

        def add_colorbar(mappable, label):
            colorbar = self.fig.colorbar(
                mappable, ax=self.axes, pad=0.1,
                shrink=float(options.get("colourbar_height", 1.0)), format=colorbar_format,
            )
            colorbar.set_label(
                options.get("colourbar_label") or label,
                fontsize=float(options.get("colourbar_label_font_size", 10.0)),
            )
            tick_size = float(options.get("colourbar_tick_font_size", 10.0))
            colorbar.ax.tick_params(labelsize=tick_size)
            colorbar.ax.yaxis.get_offset_text().set_fontsize(tick_size)
            self.colorbars.append(colorbar)
            return colorbar

        legend_labels = options.get("legend_labels", {})
        legend_label_lines = options.get("legend_label_lines", [])
        if not isinstance(legend_labels, dict):
            legend_labels = {}
        if not isinstance(legend_label_lines, list):
            legend_label_lines = []
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

            error_map = d.get("error_visualization") if (
                use_heatmap and d.get("show_error_visualization", False)
            ) else None
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
            display_name = legend_labels.get(name, name) if isinstance(legend_labels, dict) else name
            if layer_index < len(legend_label_lines) and name not in legend_labels:
                display_name = legend_label_lines[layer_index]
            
            if error_map is not None:
                distance_unit = error_map.get("unit", "mm")
                in_overlap = np.isfinite(distances)
                if np.any(in_overlap):
                    colour_values, colour_kwargs, colourbar_label, mean_marker = error_map_colours(
                        distances[in_overlap], error_map, options.get("heatmap_colormap", "auto"),
                        normalization_distances=normalization_distances,
                    )
                    scatter = self.axes.scatter(
                        x[in_overlap], y[in_overlap], z[in_overlap], c=colour_values,
                        marker='.', s=point_size, zorder=zorder, depthshade=False, **colour_kwargs,
                        label=display_name, axlim_clip=True,
                    )
                    cb = add_colorbar(scatter, colourbar_label)
                    if mean_marker is not None and np.isfinite(mean_marker):
                        cb.ax.axhline(float(mean_marker), color="white", linewidth=1.5)
                        cb.ax.axhline(float(mean_marker), color="black", linewidth=0.5, linestyle="--")
                    colorbar_added = True
                if np.any(~in_overlap):
                    self.axes.scatter(
                        x[~in_overlap], y[~in_overlap], z[~in_overlap], c="0.55", marker='.', s=point_size,
                        label=f"{display_name} excluded from error statistics", zorder=zorder, axlim_clip=True,
                    )
                if error_map.get("highlight_above_mean") and error_map.get("mean") is not None:
                    above_mean = in_overlap & (distances > float(error_map["mean"]))
                    if np.any(above_mean):
                        self.axes.scatter(
                            x[above_mean], y[above_mean], z[above_mean], c="red", marker='.', s=point_size,
                            label=f"{display_name} > mean error", zorder=zorder + 1, axlim_clip=True,
                        )
                error_map_shown = True
                continue

            color_col = st.get("color_col")
            base_color = st.get("base_color", "b")

            if heightmap_enabled:
                scatter = self.axes.scatter(
                    x, y, z, c=z, cmap=height_cmap, vmin=height_min, vmax=height_max,
                    marker='.', s=point_size, label=display_name, zorder=zorder,
                    axlim_clip=True, depthshade=False,
                )
                if height_mappable is None:
                    height_mappable = scatter
                continue
            
            if color_col and color_col in df.columns:
                c = df[color_col].to_numpy()
                colour_min, colour_max = df[color_col].min(), df[color_col].max()
                if indices is not None:
                    c = c[indices]
                scatter = self.axes.scatter(
                    x, y, z, c=c, cmap=cm.viridis, vmin=colour_min, vmax=colour_max,
                    marker='.', s=point_size, label=display_name, zorder=zorder,
                    axlim_clip=True,
                )
                if not colorbar_added:
                    add_colorbar(scatter, color_col)
                    colorbar_added = True
            else:
                self.axes.scatter(
                    x, y, z, c=base_color, marker='.', s=point_size, label=display_name, zorder=zorder, axlim_clip=True
                )
        if height_mappable is not None:
            unit = visible_datasets[0].get("settings", {}).get("distance_unit", "mm")
            add_colorbar(height_mappable, f"Height / Z coordinate ({unit})")
            colorbar_added = True
            
        label_padding = 4.0 + 0.75 * max(0.0, axis_label_font_size - 10.0)
        self.axes.set_xlabel(options.get("x_label", "X"), fontsize=axis_label_font_size, labelpad=label_padding)
        self.axes.set_ylabel(options.get("y_label", "Y"), fontsize=axis_label_font_size, labelpad=label_padding)
        z_label_spacing = float(options.get("z_axis_label_spacing", 0.0))
        if z_label_spacing <= 0:
            z_label_spacing = label_padding
        self.axes.set_zlabel(options.get("z_label", "Z"), fontsize=axis_label_font_size,
                             labelpad=z_label_spacing)
        self.axes.tick_params(axis="both", labelsize=axis_tick_font_size)
        self.axes.tick_params(axis="z", labelsize=axis_tick_font_size)
        z_interval = float(options.get("z_axis_tick_interval", 0.0))
        z_tick_count = int(options.get("z_axis_ticks", 0))
        if z_interval > 0:
            self.axes.zaxis.set_major_locator(MultipleLocator(z_interval))
        elif z_tick_count > 0:
            self.axes.zaxis.set_major_locator(LinearLocator(z_tick_count))
        z_tick_gap = float(options.get("z_axis_tick_label_gap", 0.0))
        if z_tick_gap > 0:
            self.axes.tick_params(axis="z", pad=z_tick_gap)
        if error_map_shown:
            self.axes.set_title("Pointwise deviation from reference")
        preview_summary = self.preview_summary()
        self._preview_notice.set_text(preview_summary)
        if preview_summary:
            # Preserve the full cloud extent, even when an isolated extreme
            # point is absent from the interactive display sample.
            self.axes.auto_scale_xyz([x_min, x_max], [y_min, y_max], [z_min, z_max])
        
        if self.axes.collections:
            if options.get("show_legend", True):
                handles, labels = self.axes.get_legend_handles_labels()
                if labels:
                    placement = options.get("legend_placement", "inside")
                    position = options.get("legend_position", "upper right")
                    legend_kwargs = {
                        "loc": "best" if placement == "best" else position,
                        "title": options.get("legend_title", ""),
                        "markerscale": np.sqrt(
                            float(options.get("legend_point_size", 16.0)) / max(point_size, 0.1)
                        ),
                    }
                    if placement == "outside":
                        anchor = {
                            "upper right": (1.02, 1.0), "upper left": (-0.02, 1.0),
                            "lower right": (1.02, 0.0), "lower left": (-0.02, 0.0),
                        }.get(position, (1.02, 1.0))
                        legend_kwargs["bbox_to_anchor"] = anchor
                        legend_kwargs["loc"] = {
                            "upper right": "upper left", "upper left": "upper right",
                            "lower right": "lower left", "lower left": "lower right",
                        }.get(position, "upper left")
                    legend = self.axes.legend(handles, labels, **legend_kwargs)
                    for text in legend.get_texts():
                        text.set_fontsize(axis_tick_font_size)

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
        self._apply_theme_colors()
        self.draw_idle()

    def set_theme(self, theme: str):
        """Set plot colors to match the surrounding application theme."""
        self.theme = "dark" if theme == "dark" else "light"
        self._apply_theme_colors()
        self.draw_idle()

    def _apply_theme_colors(self):
        dark = self.theme == "dark"
        background = "#171d27" if dark else "#ffffff"
        axes_background = "#1e2633" if dark else "#ffffff"
        foreground = "#e6edf7" if dark else "#263244"
        grid = "#526176" if dark else "#d8dee8"
        self.fig.patch.set_facecolor(background)
        self.axes.set_facecolor(axes_background)
        self.axes.tick_params(colors=foreground)
        self.axes.xaxis.label.set_color(foreground)
        self.axes.yaxis.label.set_color(foreground)
        self.axes.zaxis.label.set_color(foreground)
        self.axes.title.set_color(foreground)
        self.axes.grid(color=grid, alpha=0.55)
        for axis in (self.axes.xaxis, self.axes.yaxis, self.axes.zaxis):
            axis.pane.set_facecolor(axes_background)
            axis.pane.set_edgecolor(grid)
        if self.axes.legend_ is not None:
            self.axes.legend_.get_frame().set_facecolor(axes_background)
            self.axes.legend_.get_frame().set_edgecolor(grid)
            self.axes.legend_.get_title().set_color(foreground)
            for text in self.axes.legend_.get_texts():
                text.set_color(foreground)
        self._preview_notice.set_color(foreground)
        for colorbar in self.colorbars:
            colorbar.ax.tick_params(colors=foreground)
            colorbar.ax.yaxis.label.set_color(foreground)

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
