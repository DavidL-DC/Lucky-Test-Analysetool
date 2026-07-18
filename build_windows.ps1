$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$DistRoot = Join-Path $ProjectRoot "dist"
$AppName = "Lucky Test Analysetool"
$AppDirectory = Join-Path $DistRoot $AppName

if (-not (Test-Path $Python)) {
    throw "Virtuelle Umgebung fehlt. Bitte zuerst python -m venv .venv ausführen."
}

& $Python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller fehlt. Bitte .\.venv\Scripts\python.exe -m pip install -r requirements-build.txt ausführen."
}

Push-Location $ProjectRoot
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onedir `
        --name $AppName `
        --icon "assets\icon.ico" `
        --add-data "assets;assets" `
        --collect-all customtkinter `
        --additional-hooks-dir "pyinstaller_hooks" `
        --runtime-hook "pyinstaller_hooks\runtime_tkinter.py" `
        --paths "src" `
        "windows_launcher.py"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller-Build fehlgeschlagen."
    }

    Copy-Item ".local.env.example" (Join-Path $AppDirectory ".local.env.example") -Force
    New-Item -ItemType Directory -Path (Join-Path $AppDirectory ".secrets") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $AppDirectory "data") -Force | Out-Null
}
finally {
    Pop-Location
}

Write-Host "Build fertig: $AppDirectory"
Write-Host "Vor dem ersten Start .local.env und .secrets in diesen Ordner kopieren."
