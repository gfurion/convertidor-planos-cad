# Changelog

## [Unreleased]

## [2.3.1] — 2026-06-04

### Fixed
- Tema oscuro (`superhero`) no se aplicaba en modo Drag & Drop
- Checkbox "Optimizar archivo" eliminado (causaba error en ODA v27.1)

### Removed
- Presets de conversión en GUI (simplifica interfaz para usuarios no técnicos)

## [2.3.0] — 2026-06-04

### Added
- Fase 2: UX/UI v2
  - Historial de conversiones (JSON persistente, ventana Toplevel)
  - Panel de log expandible con toggle y copiar al portapapeles
  - Notificaciones toast al completar
  - Modo carpeta completa con escaneo recursivo y preservación de subcarpetas
  - Tiempo estimado restante (ETA) en barra de progreso
  - Alternar modo oscuro/claro (superhero ↔ flatly)
- Fase 3: Nuevas capacidades
  - Conversión bidireccional DWG ↔ DXF (selector de formato de salida)
  - Presets de conversión guardables (3 built-in + personalizados)
  - Exportar resumen CSV con BOM (compatible Excel)
  - Botón "Abrir carpeta destino" al finalizar
  - Checkbox "Optimizar archivo (eliminar datos no usados)" — purge flag de ODA
- Tests: 19 → 35 tests unitarios
- Detección automática de ODA instalado en `%ProgramFiles%\ODA\`

## [2.1.0] — 2026-06-04

### Added
- Refactor monolito a módulos: `app/models`, `app/engine`, `app/utils`, `app/gui`
- Entry point `run.py` (`python run.py` o `python -m app`)
- Tests unitarios con pytest (19 tests)
- `pyproject.toml` con ruff + mypy
- `requirements-dev.txt`
- `CHANGELOG.md`
- CI/CD con GitHub Actions (ruff + pytest)

### Changed
- `Contexto/AGENTS.md` — actualizado con nuevo proceso de setup
- `README.md` — instrucciones de setup simplificadas
- `setup.ps1` — detecta subcarpetas versionadas de ODA

### Fixed
- Ruff linting: imports ordenados, líneas largas corregidas, variable no usada eliminada

## [2.0.0] — 2026-06-02

### Added
- App completa convertidor.py (~520 líneas)
- Drag & drop de archivos DXF/DWG
- Modo Unitario (progreso por archivo) y Lote
- ODA File Converter v27.1 oculto (sin ventana)
- Logging rotativo
- Botón Cancelar
- Icono personalizado CCAD
- Instalador Inno Setup con asociación de archivos .dwg/.dxf
- Script `setup.ps1` para descarga automática de ODA
