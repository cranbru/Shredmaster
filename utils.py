import os, json, logging
from typing import List, Optional

class QueueHandler(logging.Handler):
    """Handler that puts logs into a queue for the GUI."""
    def __init__(self, q): super().__init__(); self.q = q
    def emit(self, record): self.q.put(self.format(record))


def setup_logger(queue=None, logfile=None):
    logger = logging.getLogger("ShredMaster")
    logger.setLevel(logging.INFO)
    for h in logger.handlers[:]: logger.removeHandler(h)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    sh = logging.StreamHandler(); sh.setFormatter(fmt); logger.addHandler(sh)
    if logfile:
        fh = logging.FileHandler(logfile, encoding="utf-8"); fh.setFormatter(fmt); logger.addHandler(fh)
    if queue:
        qh = QueueHandler(queue); qh.setFormatter(fmt); logger.addHandler(qh)
    return logger


class FileValidator:
    @staticmethod
    def validate_directory(path: str) -> bool:
        return os.path.isdir(path) and os.access(path, os.R_OK)
    @staticmethod
    def get_files_in_directory(path: str) -> List[str]:
        files = []
        for root, _, names in os.walk(path):
            for n in names:
                f = os.path.join(root, n)
                if os.path.isfile(f) and os.access(f, os.W_OK): files.append(f)
        return files


class SettingsManager:
    FILE = "settings.json"
    """THIS FILE GETS AUTO-GENERATED"""
    @classmethod
    def load(cls):
        if os.path.exists(cls.FILE):
            with open(cls.FILE, "r") as f: return json.load(f)
        return {}

    @classmethod
    def save(cls, data: dict):
        with open(cls.FILE, "w") as f: json.dump(data, f, indent=4)

