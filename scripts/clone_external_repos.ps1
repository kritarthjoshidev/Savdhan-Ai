[CmdletBinding()]
param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"
$git = Get-Command git -ErrorAction Stop
if ([string]::IsNullOrWhiteSpace($Destination)) {
    $Destination = Join-Path (Split-Path -Parent $PSScriptRoot) "external"
}
$destinationPath = [System.IO.Path]::GetFullPath($Destination)
New-Item -ItemType Directory -Force -Path $destinationPath | Out-Null

$repositories = @(
    @{ Name = "my-projects"; Url = "https://github.com/sara22za/my-projects.git" },
    @{ Name = "deepcamera"; Url = "https://github.com/SharpAI/DeepCamera.git" },
    @{ Name = "motion-detection-alert-system"; Url = "https://github.com/whitehatboy005/Motion-Detection-Alert-System-for-CCTV.git" },
    @{ Name = "reidentification-fr"; Url = "https://github.com/Morteza-Asadi-Shalmaiy/Re-Identification-fr.git" },
    @{ Name = "a-ai"; Url = "https://github.com/rudra-sah00/A-AI.git" }
)

foreach ($repository in $repositories) {
    $target = Join-Path $destinationPath $repository.Name
    if (Test-Path $target) {
        Write-Host "Skipping $($repository.Name): already present" -ForegroundColor Yellow
        continue
    }
    Write-Host "Cloning $($repository.Name)..." -ForegroundColor Cyan
    & $git.Source clone --depth 1 --filter=blob:none $repository.Url $target
    if ($LASTEXITCODE -ne 0) {
        throw "Clone failed: $($repository.Name)"
    }
}

Write-Host "External repositories are ready in $destinationPath" -ForegroundColor Green
