param(
    [string]$Version
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (& git -C $repoRoot describe --tags --exact-match 2>$null).Trim()
}
if ([string]::IsNullOrWhiteSpace($Version)) {
    throw "Pass -Version (for example v1.2.0) or run this script from a versioned Git tag."
}
if ($Version -notmatch '^v?\d+\.\d+\.\d+([.-][0-9A-Za-z.-]+)?$') {
    throw "Version must look like v1.2.0; received '$Version'."
}

Push-Location $repoRoot
try {
    $pythonPath = Join-Path $repoRoot ".pixi\envs\default\python.exe"
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        throw "Pixi's default environment is missing. Run 'pixi install' before building the Windows executable."
    }
    $pixiLibraryBin = Join-Path $repoRoot ".pixi\envs\default\Library\bin"
    $env:PATH = "$pixiLibraryBin;$env:PATH"

    & $pythonPath -c "import importlib.util, sys; sys.exit(importlib.util.find_spec('PyInstaller') is None)"
    if ($LASTEXITCODE -ne 0) {
        & $pythonPath -m ensurepip --upgrade
        if ($LASTEXITCODE -ne 0) { throw "Could not bootstrap pip in the Pixi environment." }
        & $pythonPath -m pip install "pyinstaller==6.11.1"
        if ($LASTEXITCODE -ne 0) { throw "Could not install the pinned PyInstaller build dependency." }
    }

    & $pythonPath -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name "PointCloudEvaluation-$Version" `
        --icon "src/assets/app_icon.ico" `
        --add-data "src/assets;src/assets" `
        --collect-binaries open3d `
        --hidden-import open3d `
        --hidden-import open3d.cpu.pybind `
        --hidden-import scipy.spatial.transform._rotation `
        "src/main.py"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }

    Write-Host "Built dist/PointCloudEvaluation-$Version.exe"
} finally {
    Pop-Location
}
