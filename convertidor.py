"""
Convertidor de Planos CAD v2
Convierte archivos DXF/DWG a versiones específicas de AutoCAD.
Motor: ODA File Converter v27.1
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import ToolTip
import threading
import subprocess
import shutil
import tempfile
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re

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

VALID_EXTENSIONS = (".dwg", ".dxf")

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

    def convert_batch(self, files: list, version: str, output_dir: str) -> dict:
        results = {"success": [], "failed": []}
        with tempfile.TemporaryDirectory() as tmp_input:
            tmp_output = tempfile.mkdtemp()
            try:
                for f in files:
                    shutil.copyfile(f, os.path.join(tmp_input, os.path.basename(f)))

                ok = self._run_oda(tmp_input, tmp_output, version)

                for f in files:
                    base_name = os.path.splitext(os.path.basename(f))[0]
                    input_ext = os.path.splitext(f)[1].lower()
                    expected = [input_ext, ".dwg", ".dxf"]
                    found = False
                    for ext in expected:
                        candidate = os.path.join(tmp_output, base_name + ext)
                        if os.path.exists(candidate):
                            dst = os.path.join(output_dir, base_name + ext)
                            shutil.copyfile(candidate, dst)
                            results["success"].append(f)
                            found = True
                            break
                    if not found:
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
                    base_name = os.path.splitext(os.path.basename(file))[0]
                    input_ext = os.path.splitext(file)[1].lower()
                    for ext in [input_ext, ".dwg", ".dxf"]:
                        src = os.path.join(tmp_output, base_name + ext)
                        if os.path.exists(src):
                            dst = os.path.join(output_dir, base_name + ext)
                            shutil.copyfile(src, dst)
                            return True
                return False
            finally:
                shutil.rmtree(tmp_output, ignore_errors=True)


class ConvertAppBase:
    """Clase base con lógica común del convertidor."""

    def _init_common(self):
        self.files = []
        self.output_dir = ""
        self.engine = None
        self._results = {"success": 0, "failed": 0, "error": None}
        self._cancel_event = threading.Event()
        self._setup_oda()
        self._setup_ui()

    def _setup_oda(self):
        exe_dir = Path(__file__).parent / "ODA"
        if exe_dir.exists():
            self.engine = ODAEngine(str(exe_dir))
        else:
            exe_dir = Path(__file__).parent
            self.engine = ODAEngine(str(exe_dir))
        if not self.engine.oda_exe.exists():
            messagebox.showwarning(
                "ODA no encontrado",
                "No se encontró ODAFileConverter.exe.\n"
                "La conversión no funcionará correctamente.\n"
                "Instale ODA File Converter en la carpeta 'ODA' junto al script."
            )

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
        ToolTip(version_combo, text="Selecciona la versión de AutoCAD a la que quieres convertir los archivos")

        ttk.Label(main, text="Modo de conversión:",
                  font=("-size 10 -weight bold")).pack(anchor=W)
        self.mode_var = ttk.StringVar(value="unit")
        mode_frame = ttk.Frame(main)
        mode_frame.pack(anchor=W, pady=(0, 10))
        unit_radio = ttk.Radiobutton(mode_frame, text="Unitario — progreso por archivo",
                        variable=self.mode_var, value="unit")
        unit_radio.pack(side=LEFT)
        ToolTip(unit_radio, text="Convierte archivo por archivo con barra de progreso individual")

        batch_radio = ttk.Radiobutton(mode_frame, text="Lote — más rápido",
                        variable=self.mode_var, value="batch")
        batch_radio.pack(side=LEFT, padx=10)
        ToolTip(batch_radio, text="Convierte todos los archivos de una vez, más rápido pero sin progreso individual")

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
        ToolTip(self.convert_btn, text="Selecciona archivos .dwg/.dxf o convierte los archivos arrastrados")

        self.cancel_btn = ttk.Button(
            main, text="Cancelar",
            bootstyle="danger",
            command=self._on_cancel
        )
        self.cancel_btn.pack(fill=X, pady=5)
        self.cancel_btn.pack_forget()
        ToolTip(self.cancel_btn, text="Detiene la conversión en curso")

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
        invalid = []
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            if ext in VALID_EXTENSIONS:
                if p not in self.files:
                    self.files.append(p)
                    added += 1
            else:
                invalid.append(os.path.basename(p))
        if invalid:
            messagebox.showwarning(
                "Archivos no válidos",
                f"Se omitieron {len(invalid)} archivo(s) con extensión no soportada:\n"
                + "\n".join(invalid[:10])
                + ("\n..." if len(invalid) > 10 else "")
                + "\n\nSolo se permiten archivos .dwg y .dxf."
            )
        if added:
            self._refresh_file_list()

    def _parse_drop_data(self, data: str) -> list:
        paths = []
        if "{" in data:
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
            self.file_list.insert("", END, values=(os.path.basename(f), "Pendiente"), tags=(f,))
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
            paths = filedialog.askopenfilenames(
                title="Seleccionar planos CAD",
                filetypes=[
                    ("Planos CAD", "*.dwg *.dxf"),
                    ("AutoCAD Drawing", "*.dwg"),
                    ("AutoCAD DXF", "*.dxf"),
                    ("Todos los archivos", "*.*"),
                ],
            )
            for p in paths:
                ext = os.path.splitext(p)[1].lower()
                if ext in VALID_EXTENSIONS and p not in self.files:
                    self.files.append(p)
            self._refresh_file_list()
            if not self.files:
                messagebox.showwarning(
                    "Sin archivos",
                    "No se seleccionó ningún archivo .dwg o .dxf.\n"
                    "Arrastra archivos al panel o usa 'Buscar y Convertir Planos'."
                )
                return

        self._files_snapshot = list(self.files)
        version_code = VERSION_MAP.get(self.version_var.get())
        output = self.output_dir or os.path.dirname(self._files_snapshot[0])

        try:
            os.makedirs(output, exist_ok=True)
        except PermissionError:
            messagebox.showerror(
                "Error de permisos",
                f"No se tiene permiso de escritura en:\n{output}\n\n"
                "Seleccione otra carpeta de destino."
            )
            return
        except OSError as e:
            messagebox.showerror(
                "Error de carpeta",
                f"No se pudo crear o acceder a la carpeta de destino:\n{output}\n\n{e}"
            )
            return

        if not os.access(output, os.W_OK):
            logging.warning("os.access check failed for %s (may be unreliable on Windows)", output)

        self.convert_btn.configure(state=DISABLED)
        self.cancel_btn.pack(fill=X, pady=5)
        self.cancel_btn.configure(state=NORMAL)
        self._cancel_event.clear()
        self.progress_var.set(0)
        self.status_var.set("Convirtiendo...")

        if HAS_DND:
            self.drop_area.configure(text="Convirtiendo...")

        mode = self.mode_var.get()
        self._results = {"success": 0, "failed": 0, "error": None}

        def worker():
            try:
                if mode == "unit":
                    self._convert_unitario(version_code, output)
                else:
                    self._convert_batch(version_code, output)
            except PermissionError:
                self._results["error"] = (
                    "Error de permisos",
                    "No se tiene permiso para escribir en la carpeta de destino."
                )
            except Exception as e:
                logging.error("Error inesperado durante conversión: %s", e)
                self._results["error"] = (
                    "Error inesperado",
                    f"Ocurrió un error durante la conversión:\n{e}"
                )
            finally:
                self.after(0, self._conversion_done)

        threading.Thread(target=worker, daemon=True).start()

    def _on_cancel(self):
        self._cancel_event.set()
        self.status_var.set("Cancelando...")
        self.cancel_btn.configure(state=DISABLED)

    def _convert_unitario(self, version, output):
        total = len(self._files_snapshot)
        for i, f in enumerate(self._files_snapshot, 1):
            if self._cancel_event.is_set():
                self._results["error"] = (
                    "Cancelado",
                    "La conversión fue cancelada por el usuario."
                )
                return
            self.after(0, self._update_progress, i, total, os.path.basename(f))
            self.after(0, self._update_file_status, f, "Convirtiendo...")
            ok = self.engine.convert_single(f, version, output)
            if ok:
                self._results["success"] += 1
            else:
                self._results["failed"] += 1
            status = "OK" if ok else "Error"
            self.after(0, self._update_file_status, f, status)
            logging.info("%s → %s", os.path.basename(f), status)

    def _convert_batch(self, version, output):
        self.after(0, self._update_progress, 0, len(self._files_snapshot), "Procesando lote...")
        results = self.engine.convert_batch(self._files_snapshot, version, output)
        self._results["success"] = len(results["success"])
        self._results["failed"] = len(results["failed"])
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
            tags = self.file_list.item(item, "tags")
            if tags and tags[0] == filepath:
                vals = self.file_list.item(item, "values")
                self.file_list.item(item, values=(vals[0], status))
                break

    def _conversion_done(self):
        error = self._results.get("error")
        total = len(self._files_snapshot)
        success = self._results.get("success", 0)
        failed = self._results.get("failed", 0)
        self.progress_var.set(100)
        self.status_var.set(f"Conversión completa — {success} OK, {failed} errores")
        self.convert_btn.configure(state=NORMAL)
        self.cancel_btn.pack_forget()
        if HAS_DND:
            self.drop_area.configure(
                text="Arrastra aquí tus planos .dwg/.dxf\no haz clic en 'Buscar y Convertir Planos'"
            )
        if error:
            messagebox.showerror(error[0], error[1])
        elif failed > 0 and success > 0:
            messagebox.showwarning(
                "Completado con errores",
                f"Se convirtieron {success} de {total} archivos.\n{failed} archivo(s) fallaron."
            )
        elif failed > 0:
            messagebox.showerror(
                "Error",
                f"Todos los {failed} archivo(s) fallaron al convertir."
            )
        else:
            messagebox.showinfo(
                "Completado",
                f"Se convirtieron {total} archivo{'s' if total != 1 else ''} exitosamente."
            )


if HAS_DND:
    class ConvertApp(TkinterDnD.Tk, ConvertAppBase):
        """Ventana principal del convertidor con drag & drop."""
        def __init__(self):
            super().__init__()
            self.title(APP_TITLE)
            self.geometry("700x500")
            self.resizable(True, True)
            self._init_common()
else:
    class ConvertApp(ttk.Window, ConvertAppBase):
        """Ventana principal del convertidor sin drag & drop."""
        def __init__(self):
            super().__init__(title=APP_TITLE, themename=DEFAULT_THEME,
                             size=(700, 500), resizable=(True, True))
            self._init_common()


if __name__ == "__main__":
    log_handler = RotatingFileHandler(
        "convertidor.log",
        maxBytes=1 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    log_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logging.basicConfig(
        level=logging.INFO,
        handlers=[log_handler],
    )
    app = ConvertApp()
    app.mainloop()
