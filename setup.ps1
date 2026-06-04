<#
.SYNOPSIS
  Configura el motor ODA File Converter para el proyecto Convertidor de Planos CAD.
.DESCRIPTION
  Descarga e instala ODA File Converter v27.1 y copia los archivos necesarios
  a la carpeta ODA/ del proyecto.
.PARAMETER Force
  Re-descarga e instala aunque ODA/ ya exista.
.PARAMETER FromInstalled
  Copia desde una instalación existente de ODA en el sistema (sin descargar).
.EXAMPLE
  .\setup.ps1
.EXAMPLE
  .\setup.ps1 -FromInstalled
#>

param(
    [switch]$Force,
    [switch]$FromInstalled
)

$ProjectRoot = $PSScriptRoot
$OdaDir = Join-Path $ProjectRoot "ODA"
$OdaExe = Join-Path $OdaDir "ODAFileConverter.exe"

function Write-Step {
    param([string]$Message, [string]$Color = "Yellow")
    Write-Host ">>> $Message" -ForegroundColor $Color
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  OK $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "  X  $Message" -ForegroundColor Red
}

# ─── Already set up? ─────────────────────────────────────────
if ((Test-Path $OdaExe) -and -not $Force) {
    Write-Ok "ODA ya está configurado en $OdaDir"
    exit 0
}

$KnownPaths = @(
    "$env:ProgramFiles\ODA\ODAFileConverter",
    "${env:ProgramFiles(x86)}\ODA\ODAFileConverter",
    "$env:LOCALAPPDATA\ODA",
    "$env:ProgramData\ODA",
    "C:\Program Files\ODA\ODAFileConverter"
)

# Add any subfolder under Program Files\ODA (e.g. "ODAFileConverter 27.1.0")
$odaDirs = Get-ChildItem "$env:ProgramFiles\ODA" -Directory -ErrorAction SilentlyContinue
foreach ($d in $odaDirs) {
    if (Test-Path (Join-Path $d.FullName "ODAFileConverter.exe")) {
        $KnownPaths = @($d.FullName) + $KnownPaths
    }
}

# ─── -FromInstalled flag ─────────────────────────────────────
if ($FromInstalled) {
    Write-Step "Buscando instalación existente de ODA en el sistema..."
    foreach ($p in $KnownPaths) {
        $candidate = Join-Path $p "ODAFileConverter.exe"
        if (Test-Path $candidate) {
            Write-Ok "Encontrado en: $p"
            New-Item -ItemType Directory -Path $OdaDir -Force | Out-Null
            Copy-Item -Path "$p\*" -Destination $OdaDir -Recurse -Force
            Write-Ok "Archivos copiados a $OdaDir"
            exit 0
        }
    }
    Write-Error "No se encontró ODA instalado en el sistema."
    Write-Host "`nDescárgalo desde: https://www.opendesign.com/guestfiles/oda_file_converter"
    exit 1
}

# ─── Step 1: Try winget ──────────────────────────────────────
$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($winget) {
    Write-Step "Instalando ODA File Converter via winget..."
    $result = & winget install --id ODA.ODAFileConverter --silent --accept-package-agreements --accept-source-agreements 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Instalación completada"
        foreach ($p in $KnownPaths) {
            $candidate = Join-Path $p "ODAFileConverter.exe"
            if (Test-Path $candidate) {
                New-Item -ItemType Directory -Path $OdaDir -Force | Out-Null
                Copy-Item -Path "$p\*" -Destination $OdaDir -Recurse -Force
                Write-Ok "Archivos copiados a $OdaDir"
                exit 0
            }
        }
        Write-Error "No se pudo localizar la carpeta de instalación tras winget."
        exit 1
    }
    Write-Error "winget falló (código: $LASTEXITCODE). Probando método alternativo..."
}

# ─── Step 2: Download MSI directly ───────────────────────────
Write-Step "Descargando ODA File Converter MSI..."
$msiUrl = "https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll_27.1.msi"
$msiPath = Join-Path $env:TEMP "ODAFileConverter_27.1.msi"

try {
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($msiUrl, $msiPath)
    Write-Ok "Descargado a $msiPath"
}
catch {
    Write-Error "Error de descarga: $($_.Exception.Message)"
    Write-Host "`n  1. Descarga manual: https://www.opendesign.com/guestfiles/oda_file_converter"
    Write-Host "  2. Instala ODA File Converter"
    Write-Host "  3. Ejecuta: .\setup.ps1 -FromInstalled"
    exit 1
}

# ─── Step 3: Install MSI ─────────────────────────────────────
Write-Step "Instalando ODA (solicitará permisos de administrador)..."
$installDir = Join-Path $env:TEMP "ODAExtract_$(Get-Random)"
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

# Try admin install (msiexec /a) to extract without full system install
$args = @(
    "/a", "`"$msiPath`"",
    "TARGETDIR=`"$installDir`"",
    "/qn"
)
$proc = Start-Process -FilePath "msiexec.exe" -ArgumentList $args -Wait -PassThru -NoNewWindow

if ($proc.ExitCode -eq 0 -and (Test-Path (Join-Path $installDir "ODAFileConverter.exe"))) {
    Write-Ok "Extracción completada"
    New-Item -ItemType Directory -Path $OdaDir -Force | Out-Null
    Copy-Item -Path "$installDir\*" -Destination $OdaDir -Recurse -Force
    Remove-Item -Path $installDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Ok "ODA configurado en $OdaDir"
    exit 0
}

# If admin install fails, try regular install
$args2 = @(
    "/i", "`"$msiPath`"",
    "/qn",
    "/norestart"
)
$proc2 = Start-Process -FilePath "msiexec.exe" -ArgumentList $args2 -Wait -PassThru -NoNewWindow

if ($proc2.ExitCode -eq 0) {
    Write-Ok "Instalación completada. Buscando archivos..."
    Start-Sleep -Seconds 3
    foreach ($p in $KnownPaths) {
        $candidate = Join-Path $p "ODAFileConverter.exe"
        if (Test-Path $candidate) {
            New-Item -ItemType Directory -Path $OdaDir -Force | Out-Null
            Copy-Item -Path "$p\*" -Destination $OdaDir -Recurse -Force
            Write-Ok "Archivos copiados a $OdaDir"
            exit 0
        }
    }
    Write-Error "Instalado pero no encontrado en rutas conocidas."
    Write-Host "  Busca ODAFileConverter.exe en el sistema y ejecuta:"
    Write-Host "  .\setup.ps1 -FromInstalled"
    exit 1
}

Write-Error "Error de instalación (código: $($proc2.ExitCode))."
Write-Host "`nPrueba ejecutar como Administrador o instala manualmente desde:"
Write-Host "  https://www.opendesign.com/guestfiles/oda_file_converter"
Write-Host "Luego ejecuta: .\setup.ps1 -FromInstalled"
exit 1
