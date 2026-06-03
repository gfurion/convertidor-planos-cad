# AGENTS.md

## Project Overview
Windows desktop app that converts AutoCAD DXF/DWG files to a user-selected target DWG version. Single-file Python app packaged with PyInstaller. UI in Spanish for non-technical users.

## Architecture
- **`convertidor.py`** — single source file with GUI + conversion logic
- **`ODA/`** — ODA File Converter v27.1 (Qt6, VC16) bundled for DWG read/write
- **`convertidor.exe`** — PyInstaller `--onefile --windowed` build
- **`INSTRUCCIONES.txt`** — usage instructions for end users
- **`AGENTS.md`** — this file

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
pip install ttkbootstrap
pip install pyinstaller
pyinstaller --onefile --windowed --hidden-import=ttkbootstrap --add-data "ODA;ODA" convertidor.py
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
- ODA File Converter v27.1 en `%TEMP%\ODAExtract\`

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

# PLAN DE MEJORA — Próximas Versiones

## 1. Arquitectura y Código
- Refactorizar monolito `convertidor.py` en módulos: `gui/`, `engine/`, `models/`, `utils/`
- Agregar tests unitarios + CI/CD (GitHub Actions)
- Control de versiones semántico
- Detección/actualización automática del engine ODA

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
