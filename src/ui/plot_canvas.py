import pandas as pd
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.cm as cm

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111, projection='3d')
        
        super(PlotCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.colorbars = []
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()
        
    def plot_datasets(self, datasets: list):
        self.axes.cla() # Clear axes
        
        # Remove existing colorbars safely
        if hasattr(self, 'colorbars'):
            for cb in self.colorbars:
                cb.remove()
            self.colorbars.clear()
        else:
            self.colorbars = []
                
        visible_datasets = [d for d in datasets if d.get("visible", False) and "df_filtered" in d and not d["df_filtered"].empty]
        
        if not visible_datasets:
            self.draw()
            return
            
        x_min, x_max = float('inf'), float('-inf')
        y_min, y_max = float('inf'), float('-inf')
        z_min, z_max = float('inf'), float('-inf')
        
        colorbar_added = False
        
        for d in visible_datasets:
            df = d["df_filtered"]
            st = d["settings"]
            name = d["name"]
            
            x = df['X'].copy()
            y = df['Y'].copy()
            z = df['Z'].copy()
            
            if st.get("invert_x"):
                x = -x
            if st.get("invert_y"):
                y = -y
            if st.get("invert_z"):
                z = -z
            
            x_min, x_max = min(x_min, x.min()), max(x_max, x.max())
            y_min, y_max = min(y_min, y.min()), max(y_max, y.max())
            z_min, z_max = min(z_min, z.min()), max(z_max, z.max())
            
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
