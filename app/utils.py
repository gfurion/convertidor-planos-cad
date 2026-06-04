import json
import logging
import os
import re
from logging.handlers import RotatingFileHandler

from app.models import HistoryEntry

HISTORY_FILE = "historial.json"
MAX_HISTORY = 1000


def scan_folder(path: str) -> list:
    results = []
    valid = (".dwg", ".dxf")
    for root, _dirs, files in os.walk(path):
        for f in files:
            if os.path.splitext(f)[1].lower() in valid:
                results.append(os.path.join(root, f))
    return results


def parse_drop_data(data: str) -> list:
    paths = []
    if "{" in data:
        paths = re.findall(r"\{([^}]+)\}", data)
        rest = re.sub(r"\{[^}]+\}", "", data).strip()
        if rest:
            paths.extend(rest.split())
    else:
        paths = data.split()
    return [p for p in paths if os.path.exists(p)]


def setup_logging():
    handler = RotatingFileHandler(
        "convertidor.log",
        maxBytes=1 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [HistoryEntry(**item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_history(entries: list) -> None:
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in entries[-MAX_HISTORY:]], f,
                      indent=2, ensure_ascii=False)
    except OSError as e:
        logging.error("Error saving history: %s", e)


def add_history(entry: HistoryEntry) -> None:
    entries = load_history()
    entries.append(entry)
    save_history(entries)


def clear_history() -> None:
    save_history([])


class GUILogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.widget = None

    def set_widget(self, text_widget):
        self.widget = text_widget

    def emit(self, record):
        if self.widget is None:
            return
        msg = self.format(record) + "\n"
        try:
            self.widget.after(0, self._append, msg)
        except Exception:
            pass

    def _append(self, msg):
        try:
            self.widget.insert("end", msg)
            self.widget.see("end")
        except Exception:
            pass
