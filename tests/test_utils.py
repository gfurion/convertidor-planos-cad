import os
import tempfile
from pathlib import Path

from app.utils import parse_drop_data


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
