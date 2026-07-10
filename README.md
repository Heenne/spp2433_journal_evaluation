# 3D Point Cloud Data Viewer (spp2433_journal_evaluation)

A fast, local Python desktop application built with **PyQt6** and **matplotlib** to evaluate, filter, and visualize dense 3D surface scan data from CSV files.

## Features

- **Robust CSV Parsing**: Dynamically detects `X`, `Y`, and `Z` coordinates regardless of capitalization, and automatically ignores comment blocks like `//` in the headers. Retains extra columns (Intensity, Return Number, etc.) for visualization.
- **Smart Filtering & Downsampling**: Includes intuitive sliders to decimate the point cloud (e.g., keep 1 in every 10 points) or take a random percentage sample to keep the application responsive with massive datasets.
- **Caching Mechanism**: Save your filtered datasets locally. The app will automatically detect optimized datasets the next time you load the original file, saving significant loading time.
- **3D Visualization**: Render points in an interactive 3D space. Apply dynamic color mapping using any of the additional columns in your dataset.
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