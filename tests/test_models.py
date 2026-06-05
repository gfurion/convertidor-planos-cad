from app.models import (
    APP_TITLE,
    DEFAULT_FORMAT,
    DEFAULT_THEME,
    DEFAULT_VERSION,
    FORMAT_EXT_MAP,
    OUTPUT_FORMATS,
    VALID_EXTENSIONS,
    VERSION_MAP,
    Preset,
)


class TestVersionMap:
    def test_has_all_versions(self):
        assert len(VERSION_MAP) == 7

    def test_modern_default(self):
        assert DEFAULT_VERSION == "AutoCAD 2018–2024"
        assert VERSION_MAP[DEFAULT_VERSION] == "ACAD2018"

    def test_all_mappings(self):
        expected = {
            "AutoCAD 2018–2024": "ACAD2018",
            "AutoCAD 2013–2017": "ACAD2013",
            "AutoCAD 2010–2012": "ACAD2010",
            "AutoCAD 2007–2009": "ACAD2007",
            "AutoCAD 2004–2006": "ACAD2004",
            "AutoCAD 2000–2003": "ACAD2000",
            "AutoCAD R12–R14": "ACAD12",
        }
        assert VERSION_MAP == expected


class TestAppConstants:
    def test_valid_extensions(self):
        assert ".dwg" in VALID_EXTENSIONS
        assert ".dxf" in VALID_EXTENSIONS
        assert len(VALID_EXTENSIONS) == 2

    def test_app_title(self):
        assert APP_TITLE == "Convertidor de Planos CAD v2"

    def test_default_theme(self):
        assert DEFAULT_THEME == "superhero"

    def test_output_formats(self):
        assert OUTPUT_FORMATS == ["DWG", "DXF"]

    def test_format_ext_map(self):
        assert FORMAT_EXT_MAP == {"DWG": ".dwg", "DXF": ".dxf"}

    def test_default_format(self):
        assert DEFAULT_FORMAT == "DWG"


class TestPreset:
    def test_preset_dataclass(self):
        p = Preset(name="test", version="ACAD2018", output_format="DXF",
                    output_dir="C:\\out")
        assert p.name == "test"
        assert p.version == "ACAD2018"
        assert p.output_format == "DXF"
        assert p.output_dir == "C:\\out"

    def test_preset_default_output_dir(self):
        p = Preset(name="test", version="ACAD2018", output_format="DWG")
        assert p.output_dir == ""

    def test_preset_to_dict(self):
        p = Preset(name="t", version="v", output_format="DXF")
        d = p.to_dict()
        assert d == {"name": "t", "version": "v", "output_format": "DXF",
                      "output_dir": ""}
