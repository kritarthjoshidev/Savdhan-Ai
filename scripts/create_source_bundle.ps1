[CmdletBinding()]
param(
    [string]$OutputPath,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path (Split-Path -Parent $projectRoot) "sawdhan-ai-source.zip"
}
$archivePath = [System.IO.Path]::GetFullPath($OutputPath)

if (Test-Path -LiteralPath $archivePath) {
    if (-not $Force) {
        throw "Archive already exists: $archivePath. Re-run with -Force to replace it."
    }
    Remove-Item -LiteralPath $archivePath -Force
}

$archiveDirectory = Split-Path -Parent $archivePath
if (-not (Test-Path -LiteralPath $archiveDirectory)) {
    New-Item -ItemType Directory -Force -Path $archiveDirectory | Out-Null
}

# These are reproducible/local files, not source code. The recipient restores
# them through npm/pip, model downloads, the clone script, or their own dataset.
$excludedPaths = @(
    ".venv",
    "frontend/node_modules",
    "frontend/dist",
    "external",
    "weights",
    "backend/weights",
    "backend/auto_train_output",
    "backend/runs",
    "backend/data",
    "backend/training_jobs",
    "training_jobs",
    "surveillance.db",
    "backend/surveillance.db",
    "yolov8n.pt",
    "yolov8s-world.pt",
    "backend/yolov8n.pt",
    "backend/yolov8s-world.pt",
    ".env",
    ".env.local",
    "backend/.env"
)

$tarArguments = @("-a", "-c", "-f", $archivePath)
foreach ($excludedPath in $excludedPaths) {
    $tarArguments += "--exclude=$excludedPath"
}
$tarArguments += @("-C", $projectRoot, ".")

& tar.exe @tarArguments
if ($LASTEXITCODE -ne 0) {
    throw "Could not create source bundle. tar.exe exited with $LASTEXITCODE."
}

$sizeMb = [math]::Round((Get-Item -LiteralPath $archivePath).Length / 1MB, 2)
Write-Host "Source bundle created: $archivePath ($sizeMb MB)" -ForegroundColor Green
