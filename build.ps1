# Build script for WebScrapping Fuentes
# Usage: .\build.ps1

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Building WebScrapping Fuentes..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
try {
    pyinstaller --version | Out-Null
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Build executable
Write-Host "Building executable..." -ForegroundColor Yellow
$pyinstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name", "WebScrapping",
    "--add-data", "config;config",
    "--add-data", "scrappers;scrappers",
    "--add-data", "ui;ui",
    "--add-data", "models;models",
    "--add-data", "db;db",
    "run_gui.py"
)
pyinstaller @pyinstallerArgs

# Check if build was successful
if (Test-Path "dist\WebScrapping.exe") {
    Write-Host "" 
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable location: dist\WebScrapping.exe" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Build failed!" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
