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

## Release checklist

1. Run the repository test suite and build the executable from the release tag.
2. Launch the EXE on a clean Windows account that has no Python or Pixi installed.
3. Open a representative legacy JSON project, CSV and PLY data; verify visibility, filtering, alignment, evaluation, and export.
4. Confirm that changing the theme survives restarting the EXE.
5. Create a GitHub Release for the version tag and attach `dist/PointCloudEvaluation-<version>.exe`.
6. In the release notes, include the version, supported Windows requirement, first-run usage (open a project or load CSV/PLY data), project/data compatibility, and any known limitations.

The repository task does not publish a release. A release is created only when a maintainer performs the checklist after validating the packaged EXE.
