"""Position export labels using their rendered extents, including 3-D axes."""
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.ticker import FixedLocator, MaxNLocator
from matplotlib.transforms import Bbox


def z_tick_boxes(axes, renderer):
    lower, upper = sorted(axes.get_zlim3d())
    return [tick.label1.get_window_extent(renderer) for tick in axes.zaxis.get_major_ticks()
            if lower <= tick.get_loc() <= upper and tick.label1.get_visible() and tick.label1.get_text()]


def z_tick_label_separation(axes, boxes):
    """Return the smallest text gap and center separation along the Z axis."""
    if len(boxes) < 2:
        return float("inf"), float("inf")
    endpoints = axes.zaxis.line.get_transform().transform(axes.zaxis.line.get_xydata())
    direction = endpoints[-1] - endpoints[0]
    length = np.linalg.norm(direction)
    direction = direction / length if length else np.array([0., 1.])
    projected = sorted((
        np.dot([(box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2], direction),
        (abs(direction[0]) * box.width + abs(direction[1]) * box.height) / 2,
    ) for box in boxes)
    gaps = [right[0] - left[0] - left[1] - right[1] for left, right in zip(projected, projected[1:])]
    centers = [right[0] - left[0] for left, right in zip(projected, projected[1:])]
    return min(gaps), min(centers)


def layout_export_z_axis(figure, axes, label, font_size, spacing=0.0, tick_count=0, tick_interval=0.0,
                         tick_label_gap=0.0):
    """Separate the Z title from numbers, honoring a tick interval or count.

    A positive interval takes precedence and places ticks at multiples of that
    interval within the existing limits. Otherwise a zero count selects Auto,
    which reduces colliding tick labels. A positive tick-label gap expands the
    displayed Z box aspect until the numbers have that much space between them.

    Measure the layout without rendering the potentially millions of scatter
    points. The normal export pass subsequently renders the full data once.
    """
    axes.set_zlabel("")
    title = figure.text(0.1, 0.5, label, rotation=90, va="center", ha="center", fontsize=font_size)
    title.set_gid("export_z_axis_label")
    canvas = FigureCanvasAgg(figure)
    collections = [(artist, artist.get_visible()) for artist in axes.collections]
    try:
        for artist, _ in collections:
            artist.set_visible(False)
        requested_count = int(tick_count)
        interval = float(tick_interval)
        lower, upper = sorted(axes.get_zlim3d())
        interval_positions = None
        if interval > 0:
            first = int(np.ceil(lower / interval - 1e-10))
            last = int(np.floor(upper / interval + 1e-10))
            if last - first + 1 > 1000:
                raise ValueError("Z-axis tick interval would create more than 1000 ticks; choose a larger interval.")
            interval_positions = np.clip(np.arange(first, last + 1, dtype=float) * interval, lower, upper)
        # Savefig must not move the axes after positioning a figure-level
        # title, so finish and freeze constrained layout before measuring.
        canvas.draw()
        canvas.draw()
        figure.set_layout_engine("none")
        manual = interval_positions is not None or requested_count > 0
        counts = [requested_count] if manual else range(6, 0, -1)
        for count in counts:
            if interval_positions is not None:
                locator = FixedLocator(interval_positions)
            elif requested_count > 0:
                positions = np.linspace(lower, upper, count) if count > 1 else [(lower + upper) / 2]
                locator = FixedLocator(positions)
            else:
                locator = (MaxNLocator(nbins=count - 1, min_n_ticks=2) if count > 1
                           else FixedLocator([(lower + upper) / 2]))
            axes.zaxis.set_major_locator(locator)
            canvas.draw()
            renderer = canvas.get_renderer()
            boxes = z_tick_boxes(axes, renderer)
            if manual or (len(boxes) <= count and (tick_label_gap > 0 or not any(
                    first.expanded(1.05, 1.15).overlaps(second)
                    for index, first in enumerate(boxes) for second in boxes[index + 1:]))):
                break
        if tick_label_gap > 0 and len(boxes) > 1:
            target_gap = float(tick_label_gap) * figure.dpi / 72
            for _ in range(24):
                actual_gap, center_spacing = z_tick_label_separation(axes, boxes)
                if actual_gap >= target_gap - 0.25:
                    break
                aspect = axes.get_box_aspect().copy()
                aspect[2] *= min(2.0, max(1.05, 1 + (target_gap - actual_gap) / max(center_spacing, 1)))
                axes.set_box_aspect(aspect)
                canvas.draw()
                renderer = canvas.get_renderer()
                boxes = z_tick_boxes(axes, renderer)
            else:
                raise ValueError("The Z tick-label gap cannot fit in the export. Choose a smaller gap or a larger tick interval.")
        offset = axes.zaxis.get_offset_text()
        if offset.get_visible() and offset.get_text():
            boxes.append(offset.get_window_extent(renderer))
        extent = Bbox.union(boxes) if boxes else axes.zaxis.line.get_window_extent(renderer)
        title_width = title.get_window_extent(renderer).width
        gap = (float(spacing) or max(8.0, float(font_size) / 2)) * figure.dpi / 72
        # Follow the actual Z-axis side of the current camera view.
        side = -1 if extent.x0 + extent.x1 < 2 * axes.bbox.x0 + axes.bbox.width else 1
        x = extent.x0 - gap - title_width / 2 if side < 0 else extent.x1 + gap + title_width / 2
        title.set_position(figure.transFigure.inverted().transform((x, (extent.y0 + extent.y1) / 2)))
    finally:
        for artist, visible in collections:
            artist.set_visible(visible)
    return title
