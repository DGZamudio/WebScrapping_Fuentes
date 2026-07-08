import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

_DOWNLOADS_DIR = Path("downloads")


class _Handler(FileSystemEventHandler):
    def __init__(self, drive_uploader, sheets_reporter=None):
        self._drive = drive_uploader
        self._sheets = sheets_reporter

    def on_deleted(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        try:
            rel = path.relative_to(_DOWNLOADS_DIR)
            drive_url = self._drive.delete_file_by_local_path(str(rel).replace("\\", "/"))
            if drive_url and self._sheets:
                self._sheets.delete_row_by_drive_url(drive_url)
        except Exception as e:
            logging.warning(f"FileWatcher: error al sincronizar eliminación de {path}: {e}")


class FileWatcher:
    def __init__(self, drive_uploader, sheets_reporter=None):
        self._observer = Observer()
        self._handler = _Handler(drive_uploader, sheets_reporter)
        self._started = False

    def start(self):
        if not _DOWNLOADS_DIR.exists():
            _DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self._observer.schedule(self._handler, str(_DOWNLOADS_DIR), recursive=True)
        self._observer.start()
        self._started = True
        logging.info("FileWatcher: monitoreo de downloads/ iniciado")

    def stop(self):
        if self._started:
            self._observer.stop()
            self._observer.join()
            self._started = False
            logging.info("FileWatcher: monitoreo detenido")
