[CmdletBinding()]
param(
    [string]$JobId = "f898b5d3",
    [string]$OutputPath,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$datasetRelativePath = "backend/auto_train_output/$JobId/dataset"
$datasetPath = Join-Path $projectRoot $datasetRelativePath

if (-not (Test-Path -LiteralPath $datasetPath -PathType Container)) {
    throw "Dataset was not found: $datasetPath"
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path (Split-Path -Parent $projectRoot) "sawdhan-ai-training-data-$JobId.zip"
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

# Only the YOLO dataset is included: images, labels, and data.yaml. Model
# weights, failed-run inference output, and full project source stay out.
& tar.exe -a -c -f $archivePath -C $projectRoot $datasetRelativePath
if ($LASTEXITCODE -ne 0) {
    throw "Could not create training-data bundle. tar.exe exited with $LASTEXITCODE."
}

$sizeMb = [math]::Round((Get-Item -LiteralPath $archivePath).Length / 1MB, 2)
Write-Host "Training-data bundle created: $archivePath ($sizeMb MB)" -ForegroundColor Green
