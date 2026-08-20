import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.cm as cm

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        self.axes = self.fig.add_subplot(111, projection='3d')
        
        super(PlotCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.colorbars = []
        
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

        
    def plot_datasets(self, datasets: list):
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
        
        if not visible_datasets:
            self.draw()
            return
            
        x_min, x_max = float('inf'), float('-inf')
        y_min, y_max = float('inf'), float('-inf')
        z_min, z_max = float('inf'), float('-inf')
        
        colorbar_added = False
        error_map_shown = False
        
        for d in visible_datasets:
            df = d["df_filtered"]
            st = d["settings"]
            name = d["name"]
            
            x = df['X'].copy()
            y = df['Y'].copy()
            z = df['Z'].copy()

            error_map = d.get("error_visualization") if d.get("show_error_visualization", False) else None
            if error_map is not None:
                points = np.asarray(error_map.get("points"), dtype=float)
                distances = np.asarray(error_map.get("distances"), dtype=float)
                valid = points.ndim == 2 and points.shape[1] == 3 and len(points) == len(distances)
                if valid and len(points):
                    x, y, z = points[:, 0], points[:, 1], points[:, 2]
                else:
                    error_map = None
            
            x_min, x_max = min(x_min, x.min()), max(x_max, x.max())
            y_min, y_max = min(y_min, y.min()), max(y_max, y.max())
            z_min, z_max = min(z_min, z.min()), max(z_max, z.max())
            
            if error_map is not None:
                cutoff = float(error_map["cutoff"])
                in_overlap = np.isfinite(distances)
                point_size = 8
                if np.any(in_overlap):
                    scatter = self.axes.scatter(
                        x[in_overlap], y[in_overlap], z[in_overlap], c=distances[in_overlap],
                        cmap="turbo", vmin=0.0, vmax=cutoff, marker='.', s=point_size,
                        label=f"{name} error",
                    )
                    cb = self.fig.colorbar(
                        scatter, ax=self.axes, label="Unsigned distance to reference (data units)", pad=0.1
                    )
                    self.colorbars.append(cb)
                    mean = error_map.get("mean")
                    if mean is not None and np.isfinite(mean):
                        cb.ax.axhline(float(mean), color="white", linewidth=1.5)
                        cb.ax.axhline(float(mean), color="black", linewidth=0.5, linestyle="--")
                    colorbar_added = True
                if np.any(~in_overlap):
                    self.axes.scatter(
                        x[~in_overlap], y[~in_overlap], z[~in_overlap], c="0.55", marker='.', s=point_size,
                        label=f"{name} outside cutoff",
                    )
                if error_map.get("highlight_above_mean") and error_map.get("mean") is not None:
                    above_mean = in_overlap & (distances > float(error_map["mean"]))
                    if np.any(above_mean):
                        self.axes.scatter(
                            x[above_mean], y[above_mean], z[above_mean], c="red", marker='.', s=point_size,
                            label=f"{name} > mean error",
                        )
                error_map_shown = True
                continue

            color_col = st.get("color_col")
            base_color = st.get("base_color", "b")
            
            if color_col and color_col in df.columns:
                c = df[color_col]
                scatter = self.axes.scatter(x, y, z, c=c, cmap=cm.viridis, marker='.', s=10, label=name)
                if not colorbar_added:
                    cb = self.fig.colorbar(scatter, ax=self.axes, label=color_col, pad=0.1)
                    self.colorbars.append(cb)
                    colorbar_added = True
            else:
                self.axes.scatter(x, y, z, c=base_color, marker='.', s=10, label=name)
            
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')
        self.axes.set_zlabel('Z')
        if error_map_shown:
            self.axes.set_title("Pointwise unsigned distance to reference")
        
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
            
        self.draw_idle()

    def export_plot(self, filepath: str):
        """Exports the current plot to the given filepath (png, jpg, svg)."""
        self.fig.savefig(filepath, format=filepath.split('.')[-1], bbox_inches='tight')
