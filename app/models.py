from dataclasses import asdict, dataclass
from datetime import datetime

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

OUTPUT_FORMATS = ["DWG", "DXF"]
FORMAT_EXT_MAP = {"DWG": ".dwg", "DXF": ".dxf"}
DEFAULT_FORMAT = "DWG"

APP_TITLE = "Convertidor de Planos CAD v2"
DEFAULT_VERSION = "AutoCAD 2018–2024"
DEFAULT_THEME = "superhero"


@dataclass
class HistoryEntry:
    timestamp: str
    source_file: str
    target_version: str
    status: str
    output_path: str

    @classmethod
    def now(cls, source_file: str, target_version: str, status: str, output_path: str):
        return cls(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source_file=source_file,
            target_version=target_version,
            status=status,
            output_path=output_path,
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Preset:
    name: str
    version: str
    output_format: str
    output_dir: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
