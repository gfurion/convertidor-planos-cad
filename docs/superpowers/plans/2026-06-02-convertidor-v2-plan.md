# Convertidor de Planos CAD v2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recreate `convertidor.py` from scratch with improved UX: multi-selection, drag & drop, progress bar, hidden ODA execution, and unit/batch modes.

**Architecture:** Single-file Python app using ttkbootstrap for dark UI, tkinterdnd2 for drag & drop, and ODA File Converter v27.1 as the conversion engine. All ODA calls run hidden (CREATE_NO_WINDOW).

**Tech Stack:** Python 3, ttkbootstrap, tkinterdnd2, ODA File Converter v27.1, PyInstaller

**Spec:** `docs/superpowers/specs/2026-06-02-convertidor-v2-design.md`

---

## File Structure

```
convertidor.py          — Main app (monolito)
requirements.txt        — Python dependencies
INSTRUCCIONES.txt       — End-user instructions (update)
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `convertidor.py` (skeleton)

- [ ] **Step 1: Create requirements.txt**

```
ttkbootstrap>=1.10
tkinterdnd2>=0.4
pyinstaller>=6.0
```

- [ ] **Step 2: Create convertidor.py skeleton**

```python
"""
Convertidor de Planos CAD v2
Convierte archivos DXF/DWG a versiones específicas de AutoCAD.
Motor: ODA File Converter v27.1
"""
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

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False


VERSION_MAP = {
    "AutoCAD 2018–2024": "ACAD2018",
    "AutoCAD 2013–2017": "ACAD2013",
    "AutoCAD 2010–2012": "ACAD2010",
    "AutoCAD 2007–2009": "ACAD2007",
    "AutoCAD 2004–2006": "ACAD2004",
    "AutoCAD 2000–2003": "ACAD2000",
    "AutoCAD R12–R14":   "ACAD12",
}

APP_TITLE = "Convertidor de Planos CAD v2"
DEFAULT_VERSION = "AutoCAD 2018–2024"
DEFAULT_THEME = "superhero"


class ODAEngine:
    """Maneja la conversión de archivos usando ODA File Converter."""

    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008

    def __init__(self, oda_dir: str):
        self.oda_dir = Path(oda_dir)
        self.oda_exe = self.oda_dir / "ODAFileConverter.exe"

    def _build_env(self) -> dict:
        env = os.environ.copy()
        env["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(self.oda_dir / "platforms")
        env["QT_PLUGIN_PATH"] = str(self.oda_dir)
        return env

    def _run_oda(self, input_dir: str, output_dir: str, version: str) -> bool:
        cmd = [
            str(self.oda_exe),
            input_dir,
            output_dir,
            version,
            "DWG",
            "0",
            "1",
        ]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.oda_dir),
                env=self._build_env(),
                startupinfo=startupinfo,
                creationflags=self.CREATE_NO_WINDOW | self.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=300,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logging.error("ODA timeout para carpeta: %s", input_dir)
            return False
        except Exception as e:
            logging.error("Error ejecutando ODA: %s", e)
            return False

    def convert_batch(self, files: list, version: str, output_dir: str,
                      progress_callback=None) -> dict:
        results = {"success": [], "failed": []}
        with tempfile.TemporaryDirectory() as tmp_input:
            tmp_output = tempfile.mkdtemp()
            try:
                for f in files:
                    shutil.copyfile(f, os.path.join(tmp_input, os.path.basename(f)))

                ok = self._run_oda(tmp_input, tmp_output, version)

                for f in files:
                    basename = os.path.splitext(os.path.basename(f))[0] + ".dwg"
                    src = os.path.join(tmp_output, basename)
                    dst = os.path.join(output_dir, basename)
                    if ok and os.path.exists(src):
                        shutil.copyfile(src, dst)
                        results["success"].append(f)
                    else:
                        results["failed"].append(f)
            finally:
                shutil.rmtree(tmp_output, ignore_errors=True)
        return results

    def convert_single(self, file: str, version: str, output_dir: str) -> bool:
        with tempfile.TemporaryDirectory() as tmp_input:
            tmp_output = tempfile.mkdtemp()
            try:
                shutil.copyfile(file, os.path.join(tmp_input, os.path.basename(file)))
                ok = self._run_oda(tmp_input, tmp_output, version)
                if ok:
                    basename = os.path.splitext(os.path.basename(file))[0] + ".dwg"
                    src = os.path.join(tmp_output, basename)
                    dst = os.path.join(output_dir, basename)
                    if os.path.exists(src):
                        shutil.copyfile(src, dst)
                        return True
                return False
            finally:
                shutil.rmtree(tmp_output, ignore_errors=True)


class ConvertApp(ttk.Window):
    """Ventana principal del convertidor."""

    def __init__(self):
        super().__init__(title=APP_TITLE, themename=DEFAULT_THEME,
                         size=(700, 500), resizable=(True, True))
        self.files = []
        self.output_dir = ""
        self.engine = None
        self._setup_ui()
        self._setup_oda()

    def _setup_oda(self):
        exe_dir = Path(__file__).parent / "ODA"
        if exe_dir.exists():
            self.engine = ODAEngine(str(exe_dir))
        else:
            exe_dir = Path(__file__).parent
            self.engine = ODAEngine(str(exe_dir))

    def _setup_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=BOTH, expand=True)

        ttk.Label(main, text="Versión de AutoCAD destino:",
                  font=("-size 10 -weight bold")).pack(anchor=W)
        self.version_var = ttk.StringVar(value=DEFAULT_VERSION)
        version_combo = ttk.Combobox(
            main, textvariable=self.version_var,
            values=list(VERSION_MAP.keys()),
            state="readonly", width=30
        )
        version_combo.pack(anchor=W, pady=(0, 10))

        ttk.Label(main, text="Modo de conversión:",
                  font=("-size 10 -weight bold")).pack(anchor=W)
        self.mode_var = ttk.StringVar(value="unit")
        mode_frame = ttk.Frame(main)
        mode_frame.pack(anchor=W, pady=(0, 10))
        ttk.Radiobutton(mode_frame, text="Unitario — progreso por archivo",
                        variable=self.mode_var, value="unit").pack(side=LEFT)
        ttk.Radiobutton(mode_frame, text="Lote — más rápido",
                        variable=self.mode_var, value="batch").pack(side=LEFT, padx=10)

        ttk.Separator(main).pack(fill=X, pady=5)

        drop_frame = ttk.Labelframe(main, text="Archivos", padding=5)
        drop_frame.pack(fill=BOTH, expand=True, pady=5)

        self.drop_area = ttk.Label(
            drop_frame,
            text="Arrastra aquí tus planos .dwg/.dxf\no haz clic en 'Buscar y Convertir Planos'",
            bootstyle="info", font=("-size 11"),
            anchor=CENTER, justify=CENTER
        )
        self.drop_area.pack(fill=BOTH, expand=True)

        if HAS_DND:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind("<<Drop>>", self._on_drop)

        self.file_list = ttk.Treeview(drop_frame, columns=("name", "status"),
                                       show="headings", height=6)
        self.file_list.heading("name", text="Archivo")
        self.file_list.heading("status", text="Estado")
        self.file_list.column("name", width=400)
        self.file_list.column("status", width=150)
        self.file_list.pack(fill=BOTH, expand=True, pady=(5, 0))
        self.file_list.pack_forget()

        self.badge_var = ttk.StringVar(value="")
        ttk.Label(main, textvariable=self.badge_var,
                  bootstyle="success", font=("-size 10 -weight bold")).pack(anchor=W)

        ttk.Separator(main).pack(fill=X, pady=5)

        dest_frame = ttk.Frame(main)
        dest_frame.pack(fill=X, pady=2)
        self.dest_var = ttk.StringVar(value="Misma carpeta que los origen")
        ttk.Label(dest_frame, text="Destino:").pack(side=LEFT)
        ttk.Label(dest_frame, textvariable=self.dest_var,
                  bootstyle="info").pack(side=LEFT, padx=5)
        ttk.Button(dest_frame, text="Cambiar carpeta",
                   bootstyle="outline",
                   command=self._change_output).pack(side=RIGHT)

        self.convert_btn = ttk.Button(
            main, text="Buscar y Convertir Planos",
            bootstyle="success",
            command=self._on_convert
        )
        self.convert_btn.pack(fill=X, pady=5)

        ttk.Separator(main).pack(fill=X, pady=5)

        self.progress_var = ttk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(main, variable=self.progress_var,
                                         maximum=100, bootstyle="success-striped")
        self.progress.pack(fill=X, pady=(5, 2))

        self.status_var = ttk.StringVar(value="Listo")
        ttk.Label(main, textvariable=self.status_var,
                  font=("-size 9")).pack(anchor=W)

    def _on_drop(self, event):
        raw = event.data
        paths = self._parse_drop_data(raw)
        added = 0
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            if ext in (".dwg", ".dxf") and p not in self.files:
                self.files.append(p)
                added += 1
        if added:
            self._refresh_file_list()

    def _parse_drop_data(self, data: str) -> list:
        paths = []
        if "{" in data:
            import re
            paths = re.findall(r"\{([^}]+)\}", data)
            rest = re.sub(r"\{[^}]+\}", "", data).strip()
            if rest:
                paths.extend(rest.split())
        else:
            paths = data.split()
        return [p for p in paths if os.path.exists(p)]

    def _refresh_file_list(self):
        self.file_list.delete(*self.file_list.get_children())
        for f in self.files:
            self.file_list.insert("", END, values=(os.path.basename(f), "Pendiente"))
        count = len(self.files)
        self.badge_var.set(f"✓ {count} archivo{'s' if count != 1 else ''} seleccionado{'s' if count != 1 else ''}")
        if count > 0:
            self.file_list.pack(fill=BOTH, expand=True, pady=(5, 0))
            self.drop_area.pack_forget()
        else:
            self.file_list.pack_forget()
            self.drop_area.pack(fill=BOTH, expand=True)

    def _change_output(self):
        d = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if d:
            self.output_dir = d
            self.dest_var.set(d)

    def _on_convert(self):
        if not self.files:
            messagebox.showwarning("Sin archivos",
                                   "Selecciona al menos un archivo DXF o DWG.")
            return

        version_code = VERSION_MAP.get(self.version_var.get())
        output = self.output_dir or os.path.dirname(self.files[0])
        os.makedirs(output, exist_ok=True)

        self.convert_btn.configure(state=DISABLED)
        self.progress_var.set(0)
        self.status_var.set("Convirtiendo...")

        mode = self.mode_var.get()

        def worker():
            if mode == "unit":
                self._convert_unitario(version_code, output)
            else:
                self._convert_batch(version_code, output)
            self.after(0, self._conversion_done)

        threading.Thread(target=worker, daemon=True).start()

    def _convert_unitario(self, version, output):
        total = len(self.files)
        for i, f in enumerate(self.files, 1):
            self.after(0, self._update_progress, i, total, os.path.basename(f))
            self.after(0, self._update_file_status, f, "Convirtiendo...")
            ok = self.engine.convert_single(f, version, output)
            status = "OK" if ok else "Error"
            self.after(0, self._update_file_status, f, status)
            logging.info("%s → %s", os.path.basename(f), status)

    def _convert_batch(self, version, output):
        self.after(0, self._update_progress, 0, len(self.files), "Procesando lote...")
        results = self.engine.convert_batch(self.files, version, output)
        for f in results["success"]:
            self.after(0, self._update_file_status, f, "OK")
        for f in results["failed"]:
            self.after(0, self._update_file_status, f, "Error")

    def _update_progress(self, current, total, name):
        pct = (current / total) * 100 if total > 0 else 0
        self.progress_var.set(pct)
        self.status_var.set(f"Archivo {current} de {total}: {name}")

    def _update_file_status(self, filepath, status):
        for item in self.file_list.get_children():
            vals = self.file_list.item(item, "values")
            if vals[0] == os.path.basename(filepath):
                self.file_list.item(item, values=(vals[0], status))
                break

    def _conversion_done(self):
        total = len(self.files)
        self.progress_var.set(100)
        self.status_var.set(f"Conversión completa — {total} archivo{'s' if total != 1 else ''}")
        self.convert_btn.configure(state=NORMAL)
        messagebox.showinfo("Completado",
                            f"Se convirtieron {total} archivo{'s' if total != 1 else ''} exitosamente.")


if __name__ == "__main__":
    logging.basicConfig(
        filename="convertidor.log",
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app = ConvertApp()
    app.mainloop()
```

- [ ] **Step 3: Verify it runs**

Run: `python convertidor.py`
Expected: Window opens with dark theme, version selector, mode selector, drop area

- [ ] **Step 4: Commit**

```bash
git init
git add convertidor.py requirements.txt
git commit -m "feat: skeleton with config, engine, and basic GUI"
```

---

## Task 2: Drag & Drop + File Management

**Files:**
- Modify: `convertidor.py`

- [ ] **Step 1: Test drag & drop with sample files**

Drag a .dwg or .dxf file onto the window. Verify:
- File appears in treeview
- Badge updates to "1 archivo seleccionado"
- Drop area hides, treeview shows

- [ ] **Step 2: Test multiple file selection via button**

Click "Buscar y Convertir Planos" → select multiple files → verify all appear in list

- [ ] **Step 3: Commit**

```bash
git add convertidor.py
git commit -m "feat: drag & drop and multi-file selection working"
```

---

## Task 3: Conversion Engine — Hidden ODA

**Files:**
- Modify: `convertidor.py`

- [ ] **Step 1: Create test DXF files**

```python
# create_test_files.py (temporary)
import ezdxf
for i in range(3):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((0, 0), (10, 10))
    doc.saveas(f"test_{i+1}.dxf")
```

- [ ] **Step 2: Test single file conversion**

Select 1 file, click Convert, verify:
- No ODA window appears
- Output file created in destination
- Progress shows "Archivo 1 de 1"
- Log entry created

- [ ] **Step 3: Test batch conversion**

Select 3 files, choose "Lote" mode, convert:
- No ODA window appears
- All 3 files converted
- Progress bar fills
- Log has 3 entries

- [ ] **Step 4: Commit**

```bash
git add convertidor.py
git commit -m "feat: hidden ODA execution with unit and batch modes"
```

---

## Task 4: Error Handling + Edge Cases

**Files:**
- Modify: `convertidor.py`

- [ ] **Step 1: Test with no files selected**

Click Convert without files → verify warning dialog appears

- [ ] **Step 2: Test with invalid file**

Add a .txt file to the list → verify it's skipped or shows error

- [ ] **Step 3: Test with UNC path**

Test file from `\\server\share\file.dwg` → verify it works via `shutil.copyfile`

- [ ] **Step 4: Commit**

```bash
git add convertidor.py
git commit -m "feat: error handling for edge cases"
```

---

## Task 5: UI Polish + Final Testing

**Files:**
- Modify: `convertidor.py`
- Modify: `INSTRUCCIONES.txt`

- [ ] **Step 1: Add tooltips**

Add tooltip to version selector and mode radio buttons

- [ ] **Step 2: Update INSTRUCCIONES.txt**

```
INSTRUCCIONES DE USO — v2
==========================

1. Haz doble clic en "convertidor.exe"
2. Escoge la versión de tu AutoCAD en el menú
3. Selecciona modo: Unitario (progreso individual) o Lote (más rápido)
4. Arrastra archivos .dwg/.dxf a la ventana O haz clic en "Buscar y Convertir Planos"
5. Puedes seleccionar uno o varios archivos a la vez
6. Espera a que termine la conversión
7. No es necesario tener AutoCAD ni nada instalado
```

- [ ] **Step 3: Final manual test**

- Open app
- Drag 3+ files
- Convert in unit mode → verify progress per file
- Convert in batch mode → verify all converted
- Verify no ODA window ever appears
- Check convertidor.log has entries

- [ ] **Step 4: Commit**

```bash
git add convertidor.py INSTRUCCIONES.txt
git commit -m "feat: UI polish, tooltips, updated instructions"
```

---

## Task 6: Build .exe

**Files:**
- Modify: `convertidor.py` (if needed for PyInstaller)

- [ ] **Step 1: Install PyInstaller**

```powershell
pip install pyinstaller
```

- [ ] **Step 2: Build executable**

```powershell
pyinstaller --onefile --windowed `
  --hidden-import=ttkbootstrap `
  --hidden-import=tkinterdnd2 `
  --add-data "ODA;ODA" `
  convertidor.py
```

- [ ] **Step 3: Test .exe**

Run `dist\convertidor.exe`:
- Window opens
- Drag & drop works
- Conversion works
- No ODA window visible

- [ ] **Step 4: Commit**

```bash
git add convertidor.py
git commit -m "build: PyInstaller configuration for v2"
```

---

## Summary

| Task | What | Est. Time |
|---|---|---|
| 1 | Project setup + skeleton | 10 min |
| 2 | Drag & drop + file management | 5 min |
| 3 | Conversion engine — hidden ODA | 10 min |
| 4 | Error handling | 5 min |
| 5 | UI polish + final testing | 10 min |
| 6 | Build .exe | 5 min |
| **Total** | | **~45 min** |
