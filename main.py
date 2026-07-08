"""Punto de entrada para ejecutar scraping sin interfaz gráfica."""

import logging
from pathlib import Path

from runner import run_scrapers
from notifier import Notifier
from drive_uploader import DriveUploader
from sheets_reporter import SheetsReporter
from file_watcher import FileWatcher

logging.basicConfig(
    filename=str(Path(__file__).parent / "iurisync.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)

if __name__ == "__main__":
    _drive_watcher = DriveUploader()
    _sheets_watcher = SheetsReporter()
    if _drive_watcher.user_email:
        _sheets_watcher.compartir_con(_drive_watcher.user_email)
    _watcher = FileWatcher(_drive_watcher, _sheets_watcher)
    _watcher.start()
    results = None
    try:
        results = run_scrapers()
    finally:
        for fuente, count in (results or {}).items():
            Notifier().notify(count, fuente=fuente)
        _watcher.stop()
        _drive_watcher.close()
        _sheets_watcher.close()
