import logging
import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *  # noqa: F403
from ttkbootstrap.widgets import ToolTip

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from app.engine import ODAEngine
from app.models import APP_TITLE, DEFAULT_THEME, DEFAULT_VERSION, VALID_EXTENSIONS, VERSION_MAP
from app.utils import parse_drop_data


class ConvertAppBase:
    def _init_common(self):
        self.files = []
        self.output_dir = ""
        self.engine = None
        self._results = {"success": 0, "failed": 0, "error": None}
        self._cancel_event = threading.Event()
        self._setup_oda()
        self._setup_ui()

    def _setup_oda(self):
        exe_dir = Path(__file__).parent.parent / "ODA"
        if exe_dir.exists():
            self.engine = ODAEngine(str(exe_dir))
        else:
            exe_dir = Path(__file__).parent.parent
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
        ToolTip(version_combo,
                text="Selecciona la versión de AutoCAD a la que quieres convertir los archivos")

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
        ToolTip(batch_radio,
                text="Convierte todos de una vez — más rápido, sin progreso individual")

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
        ToolTip(self.convert_btn,
                text="Selecciona archivos .dwg/.dxf o convierte los archivos arrastrados")

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
        paths = parse_drop_data(raw)
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

    def _refresh_file_list(self):
        self.file_list.delete(*self.file_list.get_children())
        for f in self.files:
            self.file_list.insert("", END, values=(os.path.basename(f), "Pendiente"), tags=(f,))
        count = len(self.files)
        s = 's' if count != 1 else ''
        badge = f"✓ {count} archivo{s} seleccionado{s}"
        self.badge_var.set(badge)
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
        def __init__(self):
            super().__init__()
            self.title(APP_TITLE)
            self.geometry("700x500")
            self.resizable(True, True)
            self._init_common()
else:
    class ConvertApp(ttk.Window, ConvertAppBase):  # type: ignore[no-redef]
        def __init__(self):
            super().__init__(title=APP_TITLE, themename=DEFAULT_THEME,
                             size=(700, 500), resizable=(True, True))
            self._init_common()


def run():
    from app.utils import setup_logging
    setup_logging()
    app = ConvertApp()
    app.mainloop()
