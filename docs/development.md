# Developer guide

End users should use the standalone Windows EXE linked from the [README](../README.md). Pixi is for contributors who want to run or package the app from source.

## Run from source

1. Install [Pixi](https://pixi.sh/latest/).
2. From the repository root, create the project environment:

   ```powershell
   pixi install
   ```

3. Start the app:

   ```powershell
   pixi run start
   ```

Pixi uses the Python version and application dependencies declared in `pixi.toml` and keeps the environment under `.pixi/`.

## Build the Windows executable

On Windows, with the Pixi environment installed, run:

```powershell
.\tools\build_windows_exe.ps1 -Version v0.1.1
```

The script creates `dist/PointCloudEvaluation-v0.1.1.exe`. Pass a different semantic version to change the output name. PyInstaller is installed into the local Pixi environment if it is missing. Generated executables and build intermediates are local artifacts, not source files.

For faster repeat launches, build a folder-based app with a splash screen:

```powershell
.\tools\build_windows_exe.ps1 -Version v0.1.1 -FastStart
```

This creates `dist/PointCloudEvaluation-v0.1.1/PointCloudEvaluation-v0.1.1.exe`. Keep the full folder together when moving or sharing the app. The normal one-file build remains available for single-file distribution.

To distribute one EXE while avoiding a full extraction on every launch, use the cached launcher:

```powershell
.\tools\build_windows_exe.ps1 -Version v0.1.1 -CachedOneFile
```

The first launch caches the app under the user's `%LOCALAPPDATA%`; subsequent launches reuse it. This is the recommended mode for a single-file release.

See the [Windows release process](windows-release.md) for building from a tag, validating the EXE, and preparing a release.

## Project layout

- `src/main.py` — application entry point.
- `src/ui/` — window, tools, plot, translations, icons, and theme.
- `src/data/` — point-cloud parsing, filtering, and exports.
- `src/utils/registration.py` — alignment, surface-error calculation, and coverage algorithms.
- `docs/` — user workflow and algorithm documentation.
