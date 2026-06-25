import logging
import os
import sys
import threading
from pathlib import Path
from tkinter import Text, Toplevel, filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *  # noqa: F403
from ttkbootstrap.widgets import ToastNotification, ToolTip

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from app.engine import ODAEngine
from app.models import (
    APP_TITLE,
    DEFAULT_FORMAT,
    DEFAULT_THEME,
    DEFAULT_VERSION,
    FORMAT_EXT_MAP,
    OUTPUT_FORMATS,
    VALID_EXTENSIONS,
    VERSION_MAP,
    HistoryEntry,
)
from app.utils import (
    add_history,
    clear_history,
    load_history,
    parse_drop_data,
    scan_folder,
)


class ConvertAppBase:
    def _init_common(self):
        self.files = []
        self.output_dir = ""
        self.engine = None
        self._results = {"success": 0, "failed": 0, "error": None}
        self._history_entries: list = []
        self._cancel_event = threading.Event()
        self._setup_oda()
        self._setup_ui()

    def _setup_oda(self):
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent
        exe_dir = base_dir / "ODA"
        if exe_dir.exists():
            self.engine = ODAEngine(str(exe_dir))
        else:
            oda_installed = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
            oda_installed = oda_installed / "ODA"
            if oda_installed.exists():
                dirs = [d for d in oda_installed.iterdir() if d.is_dir()]
                if dirs:
                    self.engine = ODAEngine(str(sorted(dirs)[-1]))
                else:
                    self.engine = ODAEngine(str(oda_installed))
            else:
                self.engine = ODAEngine(str(base_dir))
        if not self.engine.oda_exe.exists():
            messagebox.showwarning(
                "ODA no encontrado",
                "No se encontró ODAFileConverter.exe.\n"
                "La conversión no funcionará correctamente.\n"
                "Ejecute setup.ps1 para instalar ODA File Converter."
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

        self.format_var = ttk.StringVar(value=DEFAULT_FORMAT)
        format_frame = ttk.Frame(main)
        format_frame.pack(anchor=W, pady=(0, 10))
        ttk.Label(format_frame, text="Formato de salida:",
                  font=("-size 10 -weight bold")).pack(side=LEFT)
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var,
                                     values=OUTPUT_FORMATS, state="readonly", width=8)
        format_combo.pack(side=LEFT, padx=(5, 0))
        ToolTip(format_combo, text="Selecciona el formato de salida: DWG o DXF")

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

        btn_row = ttk.Frame(main)
        btn_row.pack(fill=X, pady=5)

        self.cancel_btn = ttk.Button(
            btn_row, text="Cancelar",
            bootstyle="danger",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side=LEFT, fill=X, expand=True)
        self.cancel_btn.pack_forget()

        self.folder_btn = ttk.Button(
            btn_row, text="Carpeta",
            bootstyle="secondary-outline",
            command=self._on_select_folder
        )
        self.folder_btn.pack(side=RIGHT, padx=(5, 0))
        ToolTip(self.folder_btn,
                text="Seleccionar carpeta con planos DXF/DWG (busca recursivamente)")

        self.theme_btn = ttk.Button(
            btn_row, text="☀",
            bootstyle="secondary-outline", width=3,
            command=self._toggle_theme
        )
        self.theme_btn.pack(side=RIGHT, padx=(5, 0))
        ToolTip(self.theme_btn, text="Alternar modo oscuro/claro")

        self.hist_btn = ttk.Button(
            btn_row, text="Historial",
            bootstyle="secondary-outline",
            command=self._open_history
        )
        self.hist_btn.pack(side=RIGHT, padx=(5, 0))
        ToolTip(self.hist_btn, text="Ver historial de conversiones")

        ttk.Separator(main).pack(fill=X, pady=5)

        self.progress_var = ttk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(main, variable=self.progress_var,
                                         maximum=100, bootstyle="success-striped")
        self.progress.pack(fill=X, pady=(5, 2))

        self.status_var = ttk.StringVar(value="Listo")
        ttk.Label(main, textvariable=self.status_var,
                  font=("-size 9")).pack(anchor=W)

        log_toggle_frame = ttk.Frame(main)
        log_toggle_frame.pack(fill=X, pady=(5, 0))
        self._log_visible = False
        self.log_toggle_btn = ttk.Button(
            log_toggle_frame, text="Log ►",
            bootstyle="secondary-link", padding=(0, 0),
            command=self._toggle_log
        )
        self.log_toggle_btn.pack(side=LEFT)
        ttk.Button(log_toggle_frame, text="Copiar log", bootstyle="secondary-link",
                   padding=(0, 0), command=self._copy_log).pack(side=RIGHT)

        self.log_frame = ttk.Frame(main)
        self.log_text = Text(self.log_frame, height=6, font=("Consolas", 8),
                                wrap="word", state="normal")
        log_scroll = ttk.Scrollbar(self.log_frame, orient="vertical",
                                   command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll.pack(side=RIGHT, fill=Y)

    def _toggle_log(self):
        self._log_visible = not self._log_visible
        if self._log_visible:
            self.log_frame.pack(fill=BOTH, expand=False, pady=(2, 0))
            self.log_toggle_btn.configure(text="Log ▼")
        else:
            self.log_frame.pack_forget()
            self.log_toggle_btn.configure(text="Log ►")

    def _copy_log(self):
        content = self.log_text.get("1.0", "end-1c")
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)

    def _on_select_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta con planos CAD")
        if not folder:
            return
        found = scan_folder(folder)
        if not found:
            messagebox.showinfo("Sin planos",
                                f"No se encontraron archivos .dwg o .dxf en:\n{folder}")
            return
        added = 0
        for f in found:
            if f not in self.files:
                self.files.append(f)
                added += 1
        if added:
            self._refresh_file_list()
            logging.info("Carpeta escaneada: %d archivos agregados desde %s", added, folder)

    def _on_drop(self, event):
        raw = event.data
        paths = parse_drop_data(raw)
        added = 0
        invalid = []
        for p in paths:
            if os.path.isdir(p):
                found = scan_folder(p)
                for f in found:
                    if f not in self.files:
                        self.files.append(f)
                        added += 1
                continue
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
            self.convert_btn.configure(text="Convertir Planos")
        else:
            self.file_list.pack_forget()
            self.drop_area.pack(fill=BOTH, expand=True)
            self.convert_btn.configure(text="Buscar y Convertir Planos")

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
        output_format = self.format_var.get()
        output = self.output_dir or os.path.dirname(self._files_snapshot[0])
        self._last_output_dir = output

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

        self._results = {"success": 0, "failed": 0, "error": None}

        def worker():
            try:
                self._convert_unitario(version_code, output, output_format)
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

    def _resolve_output_path(self, source_file: str, base_output: str,
                              output_format: str = "DWG") -> str:
        ext = FORMAT_EXT_MAP.get(output_format, ".dwg")
        input_base = os.path.commonpath(self._files_snapshot) if len(self._files_snapshot) > 1 \
            else os.path.dirname(self._files_snapshot[0])
        rel = os.path.relpath(os.path.dirname(source_file), input_base)
        out_dir = os.path.join(base_output, rel) if rel != "." else base_output
        os.makedirs(out_dir, exist_ok=True)
        return os.path.join(out_dir, os.path.splitext(os.path.basename(source_file))[0] + ext)

    def _convert_unitario(self, version, output, output_format="DWG"):
        total = len(self._files_snapshot)
        import time as time_mod
        start_time = time_mod.time()
        for i, f in enumerate(self._files_snapshot, 1):
            if self._cancel_event.is_set():
                self._results["error"] = (
                    "Cancelado",
                    "La conversión fue cancelada por el usuario."
                )
                return
            t0 = time_mod.time()
            ok = self.engine.convert_single(f, version, output, output_format)
            elapsed = time_mod.time() - t0
            out_path = self._resolve_output_path(f, output, output_format)
            if ok:
                self._results["success"] += 1
            else:
                self._results["failed"] += 1
            status = "OK" if ok else "Error"
            self._history_entries.append((f, status, out_path if ok else ""))
            remaining = total - i
            if i > 1 and elapsed > 0 and total > 1:
                avg = (time_mod.time() - start_time) / i
                eta = int(avg * remaining)
                self.after(0, self._update_progress, i, total,
                           f"{os.path.basename(f)} — ETA: {eta}s")
            else:
                self.after(0, self._update_progress, i, total, os.path.basename(f))
            self.after(0, self._update_file_status, f, status)
            logging.info("%s → %s (%.1fs)", os.path.basename(f), status, elapsed)

    def _convert_batch(self, version, output, output_format="DWG"):
        self.after(0, self._update_progress, 0, len(self._files_snapshot), "Procesando lote...")
        results = self.engine.convert_batch(
            self._files_snapshot, version, output, output_format,
        )
        self._results["success"] = len(results["success"])
        self._results["failed"] = len(results["failed"])
        for f in results["success"]:
            out_path = self._resolve_output_path(f, output, output_format)
            self._history_entries.append((f, "OK", out_path))
            self.after(0, self._update_file_status, f, "OK")
        for f in results["failed"]:
            self._history_entries.append((f, "Error", ""))
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

    def _save_history(self):
        for f, status, out in self._history_entries:
            entry = HistoryEntry.now(
                source_file=f,
                target_version=self.version_var.get(),
                status=status,
                output_path=out,
            )
            add_history(entry)
        self._history_entries.clear()

    def _conversion_done(self):
        error = self._results.get("error")
        success = self._results.get("success", 0)
        failed = self._results.get("failed", 0)
        entries = list(self._history_entries)
        self._save_history()
        self.progress_var.set(100)
        self.status_var.set(f"Conversión completa — {success} OK, {failed} errores")
        self.convert_btn.configure(state=NORMAL)
        self.cancel_btn.pack_forget()
        if HAS_DND:
            self.drop_area.configure(
                text="Arrastra aquí tus planos .dwg/.dxf\no haz clic en 'Buscar y Convertir Planos'"
            )
        self._show_toast(success, failed, error)
        self._show_result_window(success, failed, error, entries)
        self.files.clear()
        self._refresh_file_list()
        self.output_dir = ""
        self.dest_var.set("Misma carpeta que los origen")
        self.progress_var.set(0)
        self.status_var.set("Listo")

    def _toggle_theme(self):
        style = ttk.Style()
        current = style.theme_use()
        new = "flatly" if current == "superhero" else "superhero"
        style.theme_use(new)
        self.theme_btn.configure(text="☾" if new == "superhero" else "☀")

    def _show_toast(self, success, failed, error):
        if error:
            msg = error[1] if len(error) > 1 else error[0]
            title = error[0]
            bootstyle = "danger"
        elif failed > 0 and success > 0:
            msg = f"{success} convertidos, {failed} errores"
            title = "Completado con errores"
            bootstyle = "warning"
        elif failed > 0:
            msg = f"Todos los {failed} archivo(s) fallaron"
            title = "Error"
            bootstyle = "danger"
        else:
            msg = f"{success} archivo(s) convertidos exitosamente"
            title = "Conversión completa"
            bootstyle = "success"
        toast = ToastNotification(
            title=title,
            message=msg,
            bootstyle=bootstyle,
            duration=5000,
        )
        toast.show_toast()

    def _show_result_window(self, success, failed, error, entries):
        total = len(entries)
        win = Toplevel(self)
        win.title("Resumen de conversión")
        win.geometry("700x400")
        win.transient(self)
        win.grab_set()

        if error:
            summary = f"Error: {error[1]}"
            bootstyle = "danger"
        elif failed > 0 and success > 0:
            summary = f"{total} archivos: {success} OK, {failed} errores"
            bootstyle = "warning"
        elif failed > 0:
            summary = f"Todos los {failed} archivo(s) fallaron"
            bootstyle = "danger"
        else:
            s = "s" if total != 1 else ""
            summary = f"{total} archivo{s} convertido{s} exitosamente"
            bootstyle = "success"

        ttk.Label(win, text=summary, font=("-size 12 -weight bold"),
                  bootstyle=bootstyle).pack(pady=(10, 5))

        version_name = self.version_var.get()
        tree = ttk.Treeview(win, columns=("file", "status", "version", "output"),
                            show="headings", height=12)
        tree.heading("file", text="Archivo")
        tree.heading("status", text="Estado")
        tree.heading("version", text="Versión")
        tree.heading("output", text="Destino")
        tree.column("file", width=200)
        tree.column("status", width=70)
        tree.column("version", width=150)
        tree.column("output", width=250)
        tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        for f, status, out_path in entries:
            tree.insert("", END, values=(
                os.path.basename(f), status, version_name, out_path or "—",
            ))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=X, padx=5, pady=(0, 5))

        def _export_csv():
            from datetime import datetime
            path = filedialog.asksaveasfilename(
                title="Guardar resumen CSV",
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            )
            if not path:
                return
            try:
                with open(path, "w", encoding="utf-8-sig") as f:
                    f.write("Archivo,Estado,Destino,Versión,Timestamp\n")
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for fp, st, out in entries:
                        out_esc = out.replace('"', '""') if out else ""
                        f.write(f'{os.path.basename(fp)},{st},"{out_esc}",{version_name},{ts}\n')
                logging.info("Resumen exportado a %s", path)
            except OSError as e:
                messagebox.showerror("Error al exportar", str(e))

        def _open_folder():
            out = self._last_output_dir if hasattr(self, "_last_output_dir") else ""
            if out and os.path.isdir(out):
                os.startfile(out)

        ttk.Button(btn_frame, text="Exportar CSV", bootstyle="success-outline",
                   command=_export_csv).pack(side=LEFT)
        ttk.Button(btn_frame, text="Abrir carpeta destino", bootstyle="info-outline",
                   command=_open_folder).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cerrar", bootstyle="secondary",
                   command=win.destroy).pack(side=RIGHT)

    def _open_history(self):
        entries = load_history()
        win = Toplevel(self)
        win.title("Historial de conversiones")
        win.geometry("750x400")
        win.transient(self)
        win.grab_set()

        tree = ttk.Treeview(win, columns=("date", "file", "version", "status", "output"),
                            show="headings", height=15)
        tree.heading("date", text="Fecha")
        tree.heading("file", text="Archivo")
        tree.heading("version", text="Versión")
        tree.heading("status", text="Estado")
        tree.heading("output", text="Destino")
        tree.column("date", width=140)
        tree.column("file", width=220)
        tree.column("version", width=120)
        tree.column("status", width=70)
        tree.column("output", width=180)
        tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        for e in reversed(entries):
            tree.insert("", END, values=(
                e.timestamp, os.path.basename(e.source_file),
                e.target_version, e.status, e.output_path,
            ))

        def on_double_click(event):
            sel = tree.selection()
            if not sel:
                return

        tree.bind("<Double-1>", on_double_click)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=X, padx=5, pady=(0, 5))

        ttk.Button(btn_frame, text="Limpiar historial", bootstyle="danger-outline",
                   command=lambda: self._clear_history(tree)).pack(side=RIGHT)
        ttk.Button(btn_frame, text="Cerrar", bootstyle="secondary",
                   command=win.destroy).pack(side=RIGHT, padx=(0, 5))

    def _clear_history(self, tree):
        if messagebox.askyesno("Limpiar historial",
                                "¿Eliminar todo el historial de conversiones?"):
            clear_history()
            for item in tree.get_children():
                tree.delete(item)


if HAS_DND:
    class ConvertApp(TkinterDnD.Tk, ConvertAppBase):
        def __init__(self):
            super().__init__()
            self.title(APP_TITLE)
            self.geometry("700x500")
            self.resizable(True, True)
            ttk.Style().theme_use(DEFAULT_THEME)
            self._init_common()
else:
    class ConvertApp(ttk.Window, ConvertAppBase):  # type: ignore[no-redef]
        def __init__(self):
            super().__init__(title=APP_TITLE, themename=DEFAULT_THEME,
                             size=(700, 500), resizable=(True, True))
            self._init_common()


def run():
    from app.utils import GUILogHandler, setup_logging
    setup_logging()
    app = ConvertApp()
    gui_handler = GUILogHandler()
    gui_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    gui_handler.set_widget(app.log_text)
    logging.getLogger().addHandler(gui_handler)
    app.mainloop()
