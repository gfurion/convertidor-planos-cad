# Changelog

## [Unreleased] — v2.1.0

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
