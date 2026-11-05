# Windows partner release

Build a standalone executable from a version tag on Windows with Pixi installed:

```powershell
git checkout v1.2.0
.\tools\build_windows_exe.ps1
```

Or supply the version directly while building a checked-out commit:

```powershell
.\tools\build_windows_exe.ps1 -Version v1.2.0
```

The script builds `dist/PointCloudEvaluation-v1.2.0.exe`. It pins PyInstaller, bundles the application icon and Open3D runtime files, and does not commit generated binaries.

When publishing a rebuilt runtime that users need to copy again, increment the patch version (for example, `v0.2.0` to `v0.2.1`). The version is part of both the release filename and the per-user cache identity.

The GitHub Actions workflow builds the cached single-file EXE on a Windows runner when a GitHub Release is published, then attaches it to that release. Once this workflow change is pushed to the repository's default branch, no local EXE build is needed for releases. Wait for the **Build Windows release** workflow to finish before sharing the release download.

For a single-file download with faster repeat launches, build the cached launcher:

```powershell
.\tools\build_windows_exe.ps1 -Version v1.2.0 -CachedOneFile
```

This still creates one distributable `dist/PointCloudEvaluation-v1.2.0.exe`. On first launch it shows a full-window splash with extraction progress and caches the app under the current user's `%LOCALAPPDATA%`. Later launches reuse that cached copy. A new build uses a content-specific cache, so it does not start an older cached app.

For a folder-based build, add `-FastStart` instead:

```powershell
.\tools\build_windows_exe.ps1 -Version v1.2.0 -FastStart
```

This creates `dist/PointCloudEvaluation-v1.2.0/`, with the runnable EXE beside its `_internal` dependency folder. Zip the complete `PointCloudEvaluation-v1.2.0` folder and attach that ZIP to the GitHub Release. Do not upload only the EXE from a folder build.

## Release checklist

1. Run the repository test suite and build the executable from the release tag.
2. Launch the EXE on a clean Windows account that has no Python or Pixi installed.
3. Open a representative legacy JSON project, CSV and PLY data; verify visibility, filtering, alignment, evaluation, and export.
4. Confirm that changing the theme survives restarting the EXE.
5. Create a GitHub Release for the version tag and attach the cached single-file `dist/PointCloudEvaluation-<version>.exe`. For a folder-based build, attach a ZIP of the complete folder instead.
6. In the release notes, include the version, supported Windows requirement, first-run usage (open a project or load CSV/PLY data), project/data compatibility, and any known limitations.

The repository task does not publish a release. A release is created only when a maintainer performs the checklist after validating the packaged EXE.
