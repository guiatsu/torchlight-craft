param(
    [Parameter(Mandatory = $true)]
    [string]$Destination
)

$ErrorActionPreference = "Stop"
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$stagePath = [System.IO.Path]::GetFullPath($Destination)

if (Test-Path -LiteralPath $stagePath) {
    throw "Runtime staging destination already exists: $stagePath"
}

New-Item -ItemType Directory -Path $stagePath -Force | Out-Null

foreach ($file in @("main.py", "pyproject.toml", "pysidedeploy.spec")) {
    Copy-Item -LiteralPath (Join-Path $sourceRoot $file) -Destination $stagePath
}

foreach ($directory in @("app", "core", "services", "data", "ui")) {
    $sourceDirectory = Join-Path $sourceRoot $directory
    if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
        throw "Required runtime directory is missing: $directory"
    }
    Copy-Item -LiteralPath $sourceDirectory -Destination $stagePath -Recurse
}

$runtimeAssets = @(
    "check.svg",
    "close.svg",
    "down-chevron.svg",
    "library.svg",
    "new.svg",
    "planner-mark.ico",
    "planner-mark.svg",
    "save.svg",
    "weapon-sigil.svg"
)
$iconDirectory = Join-Path $stagePath "assets\icons"
New-Item -ItemType Directory -Path $iconDirectory -Force | Out-Null
foreach ($asset in $runtimeAssets) {
    Copy-Item -LiteralPath (Join-Path $sourceRoot "assets\icons\$asset") -Destination $iconDirectory
}

$cacheDirectories = Get-ChildItem -LiteralPath $stagePath -Directory -Recurse -Force |
    Where-Object { $_.Name -in @("__pycache__", ".pytest_cache") } |
    Sort-Object { $_.FullName.Length } -Descending
foreach ($directory in $cacheDirectories) {
    Remove-Item -LiteralPath $directory.FullName -Recurse -Force
}
Get-ChildItem -LiteralPath $stagePath -File -Filter "*.pyc" -Recurse -Force |
    Remove-Item -Force

$forbidden = @(".github", "tests", "torchlight_craft_planner.egg-info")
foreach ($name in $forbidden) {
    if (Test-Path -LiteralPath (Join-Path $stagePath $name)) {
        throw "Development-only content was copied into the runtime stage: $name"
    }
}

Write-Host "Runtime stage contains:"
Get-ChildItem -LiteralPath $stagePath -Force | Select-Object Mode, Name
