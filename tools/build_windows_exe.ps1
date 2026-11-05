param(
    [string]$Version,
    [switch]$FastStart,
    [switch]$CachedOneFile
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
if ($FastStart -and $CachedOneFile) {
    throw "Choose either -FastStart or -CachedOneFile."
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

    $payloadName = "PointCloudEvaluation-$Version-runtime"
    $payloadDistPath = "build\cached-payload"
    $appName = if ($CachedOneFile) { $payloadName } else { "PointCloudEvaluation-$Version" }
    $pyInstallerArgs = @("--noconfirm", "--clean")
    if ($FastStart -or $CachedOneFile) {
        $pyInstallerArgs += "--onedir"
    } else {
        $pyInstallerArgs += "--onefile"
    }
    $pyInstallerArgs += @(
        "--windowed",
        "--name", $appName,
        "--distpath", $(if ($CachedOneFile) { $payloadDistPath } else { "dist" }),
        "--icon", "src/assets/app_icon.ico",
        "--add-data", "src/assets;src/assets",
        "--collect-binaries", "open3d",
        "--hidden-import", "numpy._core._exceptions",
        "--hidden-import", "scipy._cyutility",
        "--hidden-import", "open3d",
        "--hidden-import", "open3d.cpu.pybind",
        "--hidden-import", "scipy.spatial.transform._rotation",
        "src/main.py"
    )
    & $pythonPath -m PyInstaller @pyInstallerArgs
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }

    if ($CachedOneFile) {
        $payloadDirectory = Join-Path $repoRoot "$payloadDistPath\$payloadName"
        $payloadArchive = Join-Path $repoRoot "build\PointCloudEvaluation-$Version-payload.zip"
        if (Test-Path -LiteralPath $payloadArchive) {
            Remove-Item -LiteralPath $payloadArchive -Force
        }
        Compress-Archive -Path $payloadDirectory -DestinationPath $payloadArchive -CompressionLevel Optimal

        $payloadHash = (Get-FileHash -LiteralPath $payloadArchive -Algorithm SHA256).Hash.ToLowerInvariant()
        $cacheKey = "$Version-$payloadHash"
        $buildInfoPath = Join-Path $repoRoot "build\CachedLauncherBuildInfo.cs"
        $buildInfoSource = @"
namespace SPP2433
{
    internal static class BuildInfo
    {
        internal const string CacheKey = "$cacheKey";
        internal const string CacheDirectoryName = "$Version-$($payloadHash.Substring(0, 16))";
        internal const string PayloadRoot = "$payloadName";
        internal const string ApplicationExecutable = "$payloadName.exe";
    }
}
"@
        Set-Content -LiteralPath $buildInfoPath -Value $buildInfoSource -Encoding ASCII

        $compilerPath = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
        if (-not (Test-Path -LiteralPath $compilerPath)) {
            $compilerPath = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe"
        }
        if (-not (Test-Path -LiteralPath $compilerPath)) {
            throw "The .NET Framework C# compiler was not found; cannot build the cached single-file launcher."
        }

        $launcherPath = Join-Path $repoRoot "dist\PointCloudEvaluation-$Version.exe"
        $launcherSourcePath = Join-Path $repoRoot "tools\CachedLauncher.cs"
        & $compilerPath `
            /nologo `
            /target:winexe `
            /platform:x64 `
            /optimize+ `
            /win32icon:src/assets/app_icon.ico `
            "/out:$launcherPath" `
            /reference:System.Core.dll `
            /reference:System.Drawing.dll `
            /reference:System.Windows.Forms.dll `
            /reference:System.IO.Compression.dll `
            /reference:System.IO.Compression.FileSystem.dll `
            "/resource:$payloadArchive,SPP2433.Payload.zip" `
            "/resource:src/assets/app_icon.ico,SPP2433.AppIcon.ico" `
            "/resource:src/assets/app_icon.png,SPP2433.AppLogo.png" `
            $launcherSourcePath `
            $buildInfoPath
        if ($LASTEXITCODE -ne 0) { throw "Could not compile the cached single-file launcher." }

        Write-Host "Built dist/PointCloudEvaluation-$Version.exe (single-file launcher; first start caches under %LOCALAPPDATA%)"
    } elseif ($FastStart) {
        Write-Host "Built dist/PointCloudEvaluation-$Version/PointCloudEvaluation-$Version.exe (fast-start folder build)"
    } else {
        Write-Host "Built dist/PointCloudEvaluation-$Version.exe"
    }
} finally {
    Pop-Location
}
