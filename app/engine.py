import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class ODAEngine:
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
        results: dict = {"success": [], "failed": []}
        with tempfile.TemporaryDirectory() as tmp_input:
            tmp_output = tempfile.mkdtemp()
            try:
                for f in files:
                    shutil.copyfile(f, os.path.join(tmp_input, os.path.basename(f)))

                self._run_oda(tmp_input, tmp_output, version)

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
