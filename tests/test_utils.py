
import os

from app.utils import BUILTIN_PRESETS, PresetManager, parse_drop_data


class TestParseDropData:
    def test_empty_string(self):
        assert parse_drop_data("") == []

    def test_nonexistent_files_are_filtered(self):
        assert parse_drop_data("C:\\nonexistent\\file.dwg") == []

    def test_single_file(self, tmp_path):
        f = tmp_path / "test.dwg"
        f.write_text("")
        result = parse_drop_data(str(f))
        assert result == [str(f)]

    def test_multiple_files_space_separated(self, tmp_path):
        f1 = tmp_path / "a.dwg"
        f2 = tmp_path / "b.dxf"
        f1.write_text("")
        f2.write_text("")
        data = f"{f1} {f2}"
        result = parse_drop_data(data)
        assert str(f1) in result
        assert str(f2) in result

    def test_braced_path_with_spaces(self, tmp_path):
        sub = tmp_path / "sub dir"
        sub.mkdir()
        f = sub / "file.dwg"
        f.write_text("")
        data = "{" + str(f) + "}"
        result = parse_drop_data(data)
        assert result == [str(f)]

    def test_mixed_braced_and_plain(self, tmp_path):
        sub = tmp_path / "sub dir"
        sub.mkdir()
        f1 = sub / "a.dwg"
        f1.write_text("")
        f2 = tmp_path / "b.dxf"
        f2.write_text("")
        data = "{" + str(f1) + "} " + str(f2)
        result = parse_drop_data(data)
        assert str(f1) in result
        assert str(f2) in result

    def test_only_existing_files_returned(self, tmp_path):
        real = tmp_path / "real.dwg"
        real.write_text("")
        data = str(real) + " C:\\fake\\file.dwg"
        result = parse_drop_data(data)
        assert result == [str(real)]


class TestPresetManager:
    def test_builtin_presets(self):
        assert len(BUILTIN_PRESETS) == 3
        names = {p["name"] for p in BUILTIN_PRESETS}
        assert "DXF rápido (2018)" in names
        assert "DWG actual (2024)" in names
        assert "DWG legacy (2000)" in names

    def test_load_returns_builtins_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        presets = PresetManager.load_presets()
        assert len(presets) == 3

    def test_save_and_load_presets(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        custom = {"name": "Mi preset", "version": "ACAD2013",
                   "output_format": "DXF", "output_dir": "C:\\out"}
        PresetManager.add_preset(custom)
        loaded = PresetManager.load_presets()
        names = [p["name"] for p in loaded]
        assert "Mi preset" in names
        assert len(loaded) == 4

    def test_add_preset_returns_presets(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        custom = {"name": "Test", "version": "v", "output_format": "DWG",
                   "output_dir": ""}
        result = PresetManager.add_preset(custom)
        assert any(p["name"] == "Test" for p in result)

    def test_delete_preset(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        custom = {"name": "Test", "version": "v", "output_format": "DWG",
                   "output_dir": ""}
        PresetManager.add_preset(custom)
        result = PresetManager.delete_preset("Test")
        assert not any(p["name"] == "Test" for p in result)

    def test_cannot_delete_builtin(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = PresetManager.delete_preset("DXF rápido (2018)")
        names = [p["name"] for p in result]
        assert "DXF rápido (2018)" in names


class TestCsvExport:
    def test_csv_format(self, tmp_path):
        from datetime import datetime
        entries = [("C:\\in\\file1.dwg", "OK", "C:\\out\\file1.dwg"),
                   ("C:\\in\\file2.dxf", "Error", "")]
        path = tmp_path / "resumen.csv"
        version = "AutoCAD 2018–2024"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("Archivo,Estado,Destino,Versión,Timestamp\n")
            for fp, st, out in entries:
                out_esc = out.replace('"', '""') if out else ""
                f.write(f'{os.path.basename(fp)},{st},"{out_esc}",{version},{ts}\n')
        content = path.read_text(encoding="utf-8-sig")
        lines = content.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "Archivo,Estado,Destino,Versión,Timestamp"
        assert "file1.dwg,OK," in lines[1]
        assert "file2.dxf,Error," in lines[2]
        assert version in lines[1]

    def test_csv_bom_encoding(self, tmp_path):
        from datetime import datetime
        path = tmp_path / "test.csv"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("Archivo,Estado,Destino,Versión,Timestamp\n")
            f.write(f'a.dwg,OK,"C:\\out\\a.dwg",v,{ts}\n')
        content = path.read_bytes()
        assert content[:3] == b"\xef\xbb\xbf"  # BOM
