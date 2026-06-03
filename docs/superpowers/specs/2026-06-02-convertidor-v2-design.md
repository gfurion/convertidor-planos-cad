# Design Spec — Convertidor de Planos CAD v2

> Recreación de `convertidor.py` desde cero con UX mejorada
> Fecha: 2026-06-02
> Estado: Aprobado

---

## 1. Resumen

Recrear `convertidor.py` (eliminado tras compilar el .exe v1) desde cero, incorporando mejoras UX:
- Indicación clara de selección múltiple
- Drag & drop de archivos
- Progreso granular por archivo
- Procesamiento unitario o por lotes
- Ventana de ODA completamente oculta

**Tecnología**: Python + ttkbootstrap (tema "superhero") + tkinterdnd2 + ODA File Converter v27.1
**Empaquetado**: PyInstaller `--onefile --windowed`

---

## 2. Arquitectura

```
convertidor.py (monolito ~500-700 líneas)
├── Config
│   ├── VERSION_MAP (UI labels → ODA version codes)
│   ├── DEFAULT_OUTPUT_FOLDER
│   └── APP_TITLE, THEME
├── GUI (ttkbootstrap)
│   ├── Ventana principal (700x500, resizable)
│   ├── Selector de versión (Combobox)
│   ├── Zona drag & drop (tkinterdnd2)
│   ├── Lista de archivos seleccionados
│   ├── Badge de selección múltiple
│   ├── Selector de modo: Unitario / Lote
│   ├── Selector de carpeta destino
│   ├── Barra de progreso + label de estado
│   └── Botones: Buscar, Cambiar destino, Convertir
├── Engine
│   ├── convert_files(file_list, version, output_dir, mode)
│   ├── convert_single(file, version, output_dir)
│   ├── convert_batch(file_list, version, output_dir)
│   └── run_oda_hidden(cmd, cwd, env)
└── Utils
    ├── setup_logging()
    └── copy_to_temp(file) → temp_path
```

---

## 3. Versiones Soportadas

```python
VERSION_MAP = {
    "AutoCAD 2018–2024": "ACAD2018",
    "AutoCAD 2013–2017": "ACAD2013",
    "AutoCAD 2010–2012": "ACAD2010",
    "AutoCAD 2007–2009": "ACAD2007",
    "AutoCAD 2004–2006": "ACAD2004",
    "AutoCAD 2000–2003": "ACAD2000",
    "AutoCAD R12–R14":   "ACAD12",
}
```

Default: "AutoCAD 2018–2024"

---

## 4. Diseño de la Interfaz

```
┌─────────────────────────────────────────────────────────────┐
│  Convertidor de Planos CAD v2                            [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Versión de AutoCAD destino:                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ AutoCAD 2018–2024                                 ▼ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Modo de conversión:                                        │
│  (●) Unitario — progreso por archivo                        │
│  ( ) Lote — más rápido, una sola operación                  │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │        Arrastra aquí tus planos .dwg/.dxf          │    │
│  │        o haz clic en "Buscar y Convertir Planos"    │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ✓ 4 archivos seleccionados                                 │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Carpeta destino: C:\Users\...\Convertidos                 │
│  [Cambiar carpeta]                                          │
│                                                             │
│  [Buscar y Convertir Planos]                                │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░  3 de 15: planta.dwg  │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente | Tipo | Detalle |
|---|---|---|
| Versión destino | `ttk.Combobox` | 7 opciones, default "AutoCAD 2018–2024" |
| Modo conversión | `ttk.Radiobutton` | Unitario / Lote, default Unitario |
| Zona drag & drop | `tkinterdnd2.DND_Target` | Acepta .dwg, .dxf, y carpetas |
| Lista archivos | `tkinter.Treeview` o `Text` | Muestra nombres de archivos seleccionados |
| Badge selección | `ttk.Label` | "N archivos seleccionados", actualiza en tiempo real |
| Carpeta destino | `ttk.Label` + `Button` | Ruta editable, default: misma carpeta que origen |
| Barra progreso | `ttk.Progressbar` | Modo determinado, se actualiza por archivo |
| Label estado | `ttk.Label` | "Archivo 3 de 15: planta.dwg" |
| Botón principal | `ttk.Button` | "Buscar y Convertir Planos" |
| Botón destino | `ttk.Button` | "Cambiar carpeta de destino" |

---

## 5. Motor de Conversión

### Ejecución oculta de ODA

```python
CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE

proc = subprocess.Popen(
    cmd,
    creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
    cwd=oda_directory,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    env=oda_environment
)
```

### Modo Unitario

Por cada archivo:
1. Copiar archivo a carpeta temporal individual (con `shutil.copyfile` para rutas UNC)
2. Ejecutar `ODAFileConverter` con ventana oculta sobre esa carpeta
3. Leer el resultado de la carpeta de salida temporal
4. Mover/copiar resultado a la carpeta destino final
5. Actualizar barra de progreso: `X de N: nombre.dwg`
6. Registrar en log: archivo, versión, resultado, tiempo

### Modo Lote

1. Copiar todos los archivos a carpeta temporal
2. Ejecutar `ODAFileConverter` una vez sobre toda la carpeta (con ventana oculta)
3. Mover/copiar todos los resultados a la carpeta destino
4. Actualizar barra: "Convirtiendo... (N archivos)"
5. Al terminar: "N archivos convertidos"

### Parámetros ODA

```
ODAFileConverter <InputFolder> <OutputFolder> <OutputVersion> DWG 0 1
```

- InputFolder / OutputFolder: siempre diferentes
- OutputVersion: "ACAD2018", "ACAD2013", etc.
- OutputFormat: "DWG"
- Recurse: "0"
- Audit: "1"

---

## 6. Selección Múltiple

### Feedback visual
- **Texto informativo**: "Puedes seleccionar uno o varios archivos DXF/DWG" junto al botón
- **Placeholder**: "Arrastra aquí tus planos o haz clic en 'Buscar y Convertir Planos'"
- **Badge dinámico**: "N archivos seleccionados" se actualiza al agregar/quitar
- **Título filedialog**: "Selecciona uno o varios archivos DXF/DWG"
- **Tooltip**: "Selecciona uno o varios archivos DXF o DWG"

### Fuentes de archivos
- Botón "Buscar y Convertir Planos" → `filedialog.askopenfilenames()`
- Drag & drop desde explorador de Windows
- Ambas fuentes agregan a la misma lista interna
- Eliminar duplicados automáticamente

---

## 7. Manejo de Errores

| Error | Acción |
|---|---|
| Archivo no encontrado | Saltar archivo, continuar, registrar en log |
| ODA falla en archivo | Marcar como error en la lista, continuar |
| Todos los archivos fallan | Mostrar toast "0 archivos convertidos" + log |
| Carpeta destino sin permisos | Mostrar error dialog, pedir otra ruta |
| Archivo corrupto | ODA lo reporta en stderr, registrar y saltar |
| Red/UNC inaccesible | Mostrar error con la ruta que falló |

---

## 8. Logging

- Archivo: `convertidor.log` en la misma carpeta del .exe
- Rotación: máximo 1 MB, 3 archivos de respaldo
- Formato: `[FECHA HORA] [NIVEL] [ARCHIVO] Mensaje`
- Ejemplo: `[2026-06-02 14:30:15] [INFO] [planta.dwg] Convertido a ACAD2018 en 2.3s`

---

## 9. Estructura del Archivo

```python
# convertidor.py

# === IMPORTS ===
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import subprocess
import shutil
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime

# Try drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# === CONFIG ===
VERSION_MAP = { ... }
APP_TITLE = "Convertidor de Planos CAD v2"
DEFAULT_THEME = "superhero"
DEFAULT_VERSION = "AutoCAD 2018–2024"

# === ENGINE ===
class ODAEngine:
    def __init__(self): ...
    def run_oda_hidden(self, cmd, cwd, env): ...
    def convert_single(self, file, version, output_dir): ...
    def convert_batch(self, files, version, output_dir): ...

# === GUI ===
class ConvertApp(ttk.Window):
    def __init__(self): ...
    def setup_ui(self): ...
    def setup_drag_drop(self): ...
    def on_files_selected(self, files): ...
    def on_convert(self): ...
    def update_progress(self, current, total, filename): ...
    def show_toast(self, message): ...

# === MAIN ===
if __name__ == "__main__":
    app = ConvertApp()
    app.mainloop()
```

---

## 10. Dependencias

```
ttkbootstrap>=1.10
tkinterdnd2>=0.4
pyinstaller>=6.0
```

---

## 11. Empaquetado

```powershell
pip install ttkbootstrap tkinterdnd2 pyinstaller
pyinstaller --onefile --windowed ^
  --hidden-import=ttkbootstrap ^
  --hidden-import=tkinterdnd2 ^
  --add-data "ODA;ODA" ^
  convertidor.py
```

---

## 12. Criterios de Aceptación

- [ ] El .py se ejecuta sin errores
- [ ] El tema "superhero" se carga correctamente
- [ ] Se puede seleccionar archivos vía botón (múltiples)
- [ ] Se puede arrastrar archivos desde el explorador
- [ ] El badge muestra el número de archivos seleccionados
- [ ] El selector de modo Unitario/Lote funciona
- [ ] La conversión unitaria muestra progreso por archivo
- [ ] La conversión por lote procesa todos de una vez
- [ ] La ventana de ODA **nunca** es visible
- [ ] El .exe se compila y ejecuta correctamente
- [ ] El log registra cada conversión
- [ ] Errores se manejan sin crashear la app
