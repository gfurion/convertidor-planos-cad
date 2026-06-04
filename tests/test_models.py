from app.models import VERSION_MAP, VALID_EXTENSIONS, APP_TITLE, DEFAULT_VERSION, DEFAULT_THEME


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
