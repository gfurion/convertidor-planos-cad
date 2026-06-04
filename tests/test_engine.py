from unittest.mock import patch, MagicMock

from app.engine import ODAEngine


class TestODAEngine:
    def test_init_finds_exe(self, tmp_path):
        oda_dir = tmp_path / "ODA"
        oda_dir.mkdir()
        exe = oda_dir / "ODAFileConverter.exe"
        exe.write_text("")
        engine = ODAEngine(str(oda_dir))
        assert engine.oda_exe == exe
        assert engine.oda_exe.exists()

    def test_build_env_sets_qt_paths(self, tmp_path):
        oda_dir = tmp_path / "ODA"
        oda_dir.mkdir()
        (oda_dir / "platforms").mkdir()
        engine = ODAEngine(str(oda_dir))
        env = engine._build_env()
        assert "QT_PLUGIN_PATH" in env
        assert "QT_QPA_PLATFORM_PLUGIN_PATH" in env

    @patch("app.engine.subprocess.run")
    def test_run_oda_success(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        oda_dir = tmp_path / "ODA"
        oda_dir.mkdir()
        (oda_dir / "ODAFileConverter.exe").write_text("")
        engine = ODAEngine(str(oda_dir))
        result = engine._run_oda("input", "output", "ACAD2018")
        assert result is True

    @patch("app.engine.subprocess.run")
    def test_run_oda_failure(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1)
        oda_dir = tmp_path / "ODA"
        oda_dir.mkdir()
        (oda_dir / "ODAFileConverter.exe").write_text("")
        engine = ODAEngine(str(oda_dir))
        result = engine._run_oda("input", "output", "ACAD2018")
        assert result is False

    @patch("app.engine.subprocess.run")
    def test_run_oda_timeout(self, mock_run, tmp_path):
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("cmd", 300)
        oda_dir = tmp_path / "ODA"
        oda_dir.mkdir()
        (oda_dir / "ODAFileConverter.exe").write_text("")
        engine = ODAEngine(str(oda_dir))
        result = engine._run_oda("input", "output", "ACAD2018")
        assert result is False

    @patch("app.engine.ODAEngine.convert_single")
    def test_convert_single_delegates(self, mock_convert):
        mock_convert.return_value = True
        engine = ODAEngine(".")
        result = engine.convert_single("file.dwg", "ACAD2018", "out")
        assert result is True
        mock_convert.assert_called_once_with("file.dwg", "ACAD2018", "out")
