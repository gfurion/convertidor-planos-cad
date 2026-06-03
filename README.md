# Convertidor de Planos CAD v2.0

Convierte archivos DXF/DWG a versiones específicas de AutoCAD. Desarrollado con Python + ODA File Converter.

## Requisitos

- Windows 10+
- [OpenCode](https://opencode.ai) — para continuar el desarrollo con asistentes IA
- [Python 3.14+](https://python.org) — `winget install Python.Python.3.14`
- [Git](https://git-scm.com) — `winget install Git.Git`
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (opcional, para compilar instalador) — `winget install JRSoftware.InnoSetup`

## Setup para desarrollo

```powershell
# 1. Clonar el repo
git clone https://github.com/gfurion/convertidor-planos-cad.git
cd convertidor-planos-cad

# 2. Instalar dependencias Python
pip install ttkbootstrap tkinterdnd2 pyinstaller pillow

# 3. Copiar el motor ODA (no está en el repo por ser ~70 MB)
#    Desde la máquina original, copiar la carpeta ODA\ completa aquí
#    O descargar ODA File Converter v27.1 desde developer.opendesign.com
```

## Ejecutar la app

```powershell
pythonw convertidor.py
```

## Build del .exe

```powershell
pyinstaller --onefile --windowed --hidden-import=ttkbootstrap --add-data "ODA;ODA" --icon=icono.ico convertidor.py
```

> Resultado: `dist\convertidor.exe`

## Build del instalador

```powershell
& "C:\Program Files\Inno Setup 6\ISCC.exe" instalador.iss
```

> Resultado: `installer\Setup_Convertidor_CAD_v2.exe`

## Continuar con OpenCode

Abrir el proyecto en OpenCode:

```powershell
opencode "C:\ruta\convertidor-planos-cad"
```

OpenCode cargará automáticamente el contexto desde `Contexto/AGENTS.md` y los skills de Superpowers.

## Estructura del proyecto

```
convertidor-planos-cad/
├── convertidor.py              # Código fuente
├── icono.ico                   # Icono personalizado
├── instalador.iss              # Script Inno Setup
├── requirements.txt            # Dependencias Python
├── INSTRUCCIONES.txt           # Instrucciones de usuario
├── generar_icono.py            # Script para recrear icono
├── Contexto/
│   ├── AGENTS.md               # Contexto para OpenCode
│   ├── PLAN_MEJORA.md          # Plan de mejoras
│   └── PLAN_GITHUB.txt         # Notas de distribución
├── docs/superpowers/
│   ├── specs/                  # Design spec
│   └── plans/                  # Implementation plan
├── ODA/                        # Motor ODA (no subido al repo)
├── dist/                       # .exe compilado (no subido al repo)
└── installer/                  # Instalador (no subido al repo)
```
