# Build script para IURISYNC
# Uso: .\build.ps1

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Compilando IURISYNC..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Verificar PyInstaller
$pipList = python -m pip show pyinstaller 2>$null
if (-not $pipList) {
    Write-Host "PyInstaller no encontrado. Instalando..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

# Limpiar builds anteriores
Write-Host "Limpiando builds anteriores..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "IURISYNC.spec") { Remove-Item -Force "IURISYNC.spec" }

# Compilar
Write-Host "Compilando ejecutable..." -ForegroundColor Yellow
$pyinstallerArgs = @(
    "--onedir",
    "--windowed",
    "--collect-data", "customtkinter",
    "--name", "IURISYNC",
    "--add-data", "scrappers;scrappers",
    "--add-data", "ui;ui",
    "--add-data", "models;models",
    "--add-data", "db;db",
    "--add-data", "analytics;analytics",
    "run_gui.py"
)
python -m PyInstaller @pyinstallerArgs

# Verificar resultado
if (Test-Path "dist\IURISYNC\IURISYNC.exe") {
    # Copiar credenciales a la carpeta de distribución
    New-Item -ItemType Directory -Force "dist\IURISYNC\config" | Out-Null
    Copy-Item "config\credentials.json" "dist\IURISYNC\config\" -ErrorAction SilentlyContinue
    Copy-Item "config\oauth_credentials.json" "dist\IURISYNC\config\" -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "Build exitoso!" -ForegroundColor Green
    Write-Host "Distribucion lista en: dist\IURISYNC\" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Build fallido." -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
