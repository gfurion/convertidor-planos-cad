# AGENTS.md

## Project Overview
Windows desktop app that converts AutoCAD DXF/DWG files to a user-selected target DWG version. Single-file Python app packaged with PyInstaller. UI in Spanish for non-technical users.

## Architecture
- **`app/models.py`** — data models (VERSION_MAP, constants)
- **`app/engine.py`** — ODA conversion logic (ODAEngine class)
- **`app/utils.py`** — helpers (parse_drop_data, setup_logging)
- **`app/gui.py`** — GUI classes (ConvertAppBase, ConvertApp) + run()
- **`app/__init__.py`** — package marker
- **`run.py`** — entry point (`python run.py` or `python -m app`)
- **`ODA/`** — ODA File Converter v27.1 (Qt6, VC16) bundled for DWG read/write (~70 MB, excluded via .gitignore)
- **`tests/`** — unit tests (pytest, 19 tests)
- **`convertidor.exe`** — PyInstaller `--onefile --windowed` build
- **`INSTRUCCIONES.txt`** — usage instructions for end users
- **`AGENTS.md`** — this file

### Tools de calidad
- **ruff** — linter configurado en `pyproject.toml`
- **mypy** — type checker (no-strict, con `ignore_missing_imports`)
- **pytest** — test runner
- **GitHub Actions** — CI en `.github/workflows/test.yml` (ruff + pytest en push/PR)

## Setup del proyecto
- Ejecutar `.\setup.ps1` después de clonar para descargar ODA File Converter
- El script intenta winget primero, luego descarga MSI directo, o copia desde instalación existente con `-FromInstalled`
- ODA/ está en .gitignore (~70 MB) — se descarga por separado

## Key Technical Decisions
- **ODA File Converter** handles ALL file reads/writes (both DXF and DWG)
- Output is always **`.dwg`** in the target version chosen by user
- **ttkbootstrap** (theme: "superhero") for modern dark UI
- **Not using ezdxf** anymore — ODA is the single engine
- Files from network paths (UNC) work via `shutil.copyfile()` (not `copy2`)

## Version Mappings (UI → ODA)
```
"AutoCAD 2018–2024" → "ACAD2018"
"AutoCAD 2013–2017" → "ACAD2013"
"AutoCAD 2010–2012" → "ACAD2010"
"AutoCAD 2007–2009" → "ACAD2007"
"AutoCAD 2004–2006" → "ACAD2004"
"AutoCAD 2000–2003" → "ACAD2000"
"AutoCAD R12–R14"   → "ACAD12"
```

## ODA CLI Syntax
```
ODAFileConverter <InputFolder> <OutputFolder> <OutputVersion> <OutputFormat> <Recurse> <Audit>
```
- Input/Output folders must be DIFFERENT
- OutputVersion: "ACAD2013", "ACAD2018", etc.
- OutputFormat: "DXF" or "DWG"
- Recurse: "0", Audit: "1"

## Building the .exe
```powershell
pip install ttkbootstrap pyinstaller
pyinstaller --onefile --windowed ^
  --hidden-import=ttkbootstrap ^
  --hidden-import=tkinterdnd2 ^
  --add-data "ODA;ODA" ^
  --add-data "app;app" ^
  run.py
```

## Qt Platform Plugin Fix
ODAFileConverter needs env vars to find Qt plugins at runtime:
```python
env["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(oda_dir / "platforms")
env["QT_PLUGIN_PATH"] = str(oda_dir)
```
And `cwd=oda_dir` in `subprocess.run()`.

## Temp Directory Gotcha
`TemporaryDirectory` cleans up on `with` block exit. Always copy the result TO the final destination INSIDE the `with` block.

## Distribution
- Only 2 files needed: `convertidor.exe` + `INSTRUCCIONES.txt`
- Windows 10+ only, no dependencies needed
- ~82 MB standalone .exe

## Source File Location
Source code is `convertidor.py` in the project root. It is deleted after building the .exe. To modify, recreate it from scratch or keep a backup.

---

## Session Log — Última Sesión (02-Jun-2026)

### Objetivo
Aplicar repositorio `nathankim0/clean-architecture-skills` al proyecto:
1. Instalar skills en OpenCode para Clean Architecture + Kent Beck
2. Recrear `convertidor.py` (eliminado tras build)
3. Refactorizar monolito en capas (domain, application, infrastructure, gui)
4. Compilar .exe

### Progreso
- [PENDIENTE] Clonar repo a `~/.opencode/skills/clean-architecture-skills`
- [PENDIENTE] Recrear `convertidor.py` desde especificación técnica
- [PENDIENTE] Refactorizar a Clean Architecture
- [PENDIENTE] Compilar y verificar

### Issues Detectados
1. **`convertidor.py` no existe** — AGENTS.md confirma que se elimina tras compilar.
   Solución: Recrear desde cero usando la especificación técnica de este archivo.

2. **Bucle de permisos en OpenCode** — Al hacer clic en "Permitir siempre", vuelve a preguntar.
   Posible causa: Archivo de configuración global en `~/.config/opencode/opencode.json`
   puede tener reglas de permiso conflictivas u otro problema (permisos de escritura,
   formato inválido, etc.). Está pendiente de diagnosticar.

3. **No hay `.opencode/` directory en `~/.opencode/`** — Se debe crear para instalar skills.

### Recursos
- Repo skills: https://github.com/nathankim0/clean-architecture-skills
- Docs OpenCode: https://opencode.ai/config.json
- ODA File Converter v27.1: descargar con `.\setup.ps1` o desde https://www.opendesign.com/guestfiles/oda_file_converter

---

## Session Log — 02-Jun-2026 (Sesión 2)

### Objetivo
Recrear `convertidor.py` desde cero con UX mejorada usando metodología Superpowers.

### Progreso
- [x] Instalar plugin Superpowers en OpenCode
- [x] Crear design spec (`docs/superpowers/specs/2026-06-02-convertidor-v2-design.md`)
- [x] Crear implementation plan (`docs/superpowers/plans/2026-06-02-convertidor-v2-plan.md`)
- [x] Task 1: Project setup + skeleton
- [x] Task 2: Drag & drop + file management
- [x] Task 3: Conversion engine — hidden ODA
- [x] Task 4: Error handling + edge cases
- [x] Task 5: UI polish + final testing
- [x] Task 6: Build .exe (~32MB)
- [x] Copiar ODA a carpeta del proyecto (`ODA/`)
- [x] Probar interfaz — funciona correctamente
- [x] Compilar .exe con ODA dentro (78.5 MB)
- [x] Instalar Inno Setup 6.7.3 via winget
- [x] Crear script `instalador.iss`
- [x] Generar instalador `Setup_Convertidor_CAD_v2.exe` (59.4 MB)

### Archivos creados/modificados
- `convertidor.py` — App completa (~480 líneas)
- `requirements.txt` — Dependencias
- `INSTRUCCIONES.txt` — Instrucciones v2
- `dist\convertidor.exe` — Ejecutable con ODA dentro (78.5 MB)
- `installer\Setup_Convertidor_CAD_v2.exe` — Instalador profesional (59.4 MB)
- `instalador.iss` — Script Inno Setup
- `icono.ico` — Icono personalizado (CCAD)
- `generar_icono.py` — Script para recrear icono
- `ODA/` — ODA File Converter v27.1
- `docs/superpowers/specs/2026-06-02-convertidor-v2-design.md` — Design spec
- `docs/superpowers/plans/2026-06-02-convertidor-v2-plan.md` — Implementation plan

### Notas técnicas
- tkinterdnd2 requiere `TkinterDnD.Tk()` como base, no `ttk.Window`
- Usar `pythonw` en vez de `python` para evitar ventana de consola negra
- ODA ejecutado con `CREATE_NO_WINDOW | DETACHED_PROCESS` — nunca se ve la ventana
- Botón "Buscar y Convertir Planos" abre file dialog cuando no hay archivos, convierte cuando ya hay
- PyInstaller con `--add-data "ODA;ODA"` incluye ODA dentro del .exe
- Inno Setup 6.7.3 instalado en `C:\Users\gvalbuena\AppData\Local\Programs\Inno Setup 6`
- ISCC.exe para compilación silenciosa: `& "ISCC.exe" "instalador.iss"`

### Pendiente
- Probar conversión con archivos reales
- Probar instalador en máquina limpia

### GitHub
- Repositorio privado creado: `https://github.com/gfurion/convertidor-planos-cad`
- Commits: `d651cb8`, `4d80d32`
- Rama: `master`

---

## Session Log — 04-Jun-2026 (Sesión 3)

### Objetivo
Ejecutar Fase 1: Refactorizar monolito en módulos, agregar tests y CI/CD.

### Progreso
- [x] Clonar repo desde GitHub a PC nueva (`C:\Users\giova\Desktop\Convertidor de Planos CAD\`)
- [x] Instalar ODA File Converter v27.1 via winget y copiar a `ODA/` (69.3 MB)
- [x] Corregir `setup.ps1` para detectar subcarpetas versionadas (`ODAFileConverter 27.1.0`)
- [x] Crear estructura `app/` con 4 módulos: models, engine, utils, gui
- [x] Crear `run.py` como entry point
- [x] Crear `pyproject.toml` (ruff + mypy) + `requirements-dev.txt`
- [x] Crear 19 tests unitarios (pytest) — todos pasando
- [x] Ruff: 0 errores. Mypy: 0 errores.
- [x] Verificar que la app se abre y destruye correctamente
- [x] Crear `CHANGELOG.md`
- [x] Crear CI/CD (`./github/workflows/test.yml`)
- [x] Actualizar `AGENTS.md`

### Archivos creados
- `app/__init__.py`, `app/models.py`, `app/engine.py`, `app/utils.py`, `app/gui.py`
- `run.py`
- `tests/__init__.py`, `tests/test_models.py`, `tests/test_engine.py`, `tests/test_utils.py`
- `pyproject.toml`, `requirements-dev.txt`
- `CHANGELOG.md`
- `.github/workflows/test.yml`
- `ODA/` (69.3 MB, .gitignored)

### Archivos modificados
- `setup.ps1` — detecta subcarpetas versionadas de ODA
- `Contexto/AGENTS.md` — sesión log, arquitectura actualizada, plan de mejora marcado
- `README.md` — setup simplificado
- `.gitignore` — verificado (ODA/ excluido)

### Notas técnicas
- module `app/` funciona con `python run.py` o `python -m app`
- tkinterdnd2 con `TkinterDnD.Tk` en `app/gui.py` — import condicional (HAS_DND)
- `ruff` con per-file-ignores para F405 en gui.py (star import de ttkbootstrap.constants)
- PyInstaller build actualizado: `--add-data "app;app" --hidden-import=tkinterdnd2`
- Mypy `ignore_missing_imports = true` para ttkbootstrap/tkinterdnd2

### Pendiente
- Compilar .exe con PyInstaller
- Probar conversión con archivos reales
- Pasar a Fase 2: UX v2

---

# PLAN DE MEJORA — Próximas Versiones

## 1. Arquitectura y Código ✅ COMPLETADO
- [x] Refactorizar monolito `convertidor.py` en módulos: `app/models.py`, `app/engine.py`, `app/utils.py`, `app/gui.py`
- [x] Tests unitarios (19 tests con pytest) + CI/CD (GitHub Actions)
- [x] Linting con ruff + type checking con mypy
- [x] Control de versiones semántico (CHANGELOG.md, pyproject.toml v2.1.0)
- [ ] Detección/actualización automática del engine ODA — pendiente

## 2. UX/UI
- Vista previa de planos (miniaturas DWG/DXF)
- Barra de progreso granular por archivo individual
- Drag & drop de archivos/carpetas
- Modo carpeta completa (convertir recursivamente)
- Indicación visual de selección múltiple: texto informativo, badge de archivos seleccionados, tooltip, placeholder y título de filedialog personalizado
- Historial de conversiones (fecha, archivo, versión, resultado)
- Modo oscuro/claro seleccionable
- Notificaciones toast al completar
- Panel expandible de log detallado

## 3. Funcionalidades Nuevas
- Conversión inversa DWG → DXF
- Procesamiento paralelo con `concurrent.futures`
- Presets de conversión guardables
- Exportar resumen CSV/TXT
- Opción de purgar capas y bloques no usados (vía ODA)
- Sobrescritura inteligente con recordatorio

## 4. Distribución
- [x] Instalador Inno Setup con asociación de archivos .dwg/.dxf
- [ ] Auto-actualizador vía GitHub Releases
- [ ] Firma digital Authenticode
- [x] Versión portable (dist\convertidor.exe) + versión instalable (Setup_Convertidor_CAD_v2.exe)

## 5. Multi-idioma (i18n)
- Archivos JSON de traducción
- ES / EN / PT
- Detección automática del idioma del sistema + selector manual

## 6. Calidad y Soporte
- Logging estructurado a archivo rotativo
- Modo CLI para integración: `convertidor.exe --input ./planos --version ACAD2018 --output ./convertidos`
- Reporte anónimo de errores (opt-in)
- Botón de Ayuda → web FAQ

## 7. Roadmap (12 semanas)
```
Fase 1 (Sem 1-3): Refactor + tests + logging
Fase 2 (Sem 4-6): UX v2 (drag & drop, miniaturas, progreso, historial, i18n)
Fase 3 (Sem 7-9): Nuevas features (DXF←→DWG, carpeta recursiva, CLI, presets)
Fase 4 (Sem 10-12): Instalador, auto-updater, firma digital, documentación
```
