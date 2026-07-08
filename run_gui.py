import threading
from ui.app import App
from runner import run_scrapers
from db.memory import Memory
from drive_uploader import DriveUploader
from sheets_reporter import SheetsReporter
from file_watcher import FileWatcher
from analytics.server import start_server


def start_scrape_thread(app: App, stop_event: "threading.Event"):
    # Read dates from the dashboard execute card (user-editable, pre-filled smartly)
    try:
        fini, ffin = app.dashboard.get_dates()
    except Exception:
        fini, ffin = None, None

    try:
        allowed = app.settings_view.get_enabled_sources()
    except Exception:
        allowed = None

    try:
        source_options = app.settings_view.get_source_options()
    except Exception:
        source_options = {}

    def on_new_doc(doc):
        app.after(0, lambda: app.log(f"Nuevo documento descargado: {doc['title']}"))

    def on_progress(msg):
        app.after(0, lambda: app.log(msg))

    def on_stats(count):
        app.after(0, lambda: app.update_stats(count))

    try:
        run_scrapers(fini=fini, ffin=ffin, on_new_doc=on_new_doc, on_progress=on_progress, on_stats=on_stats, stop_event=stop_event, allowed_sources=allowed, source_options=source_options)
    finally:
        # ensure UI is unblocked when worker finishes
        app.after(0, lambda: app.set_running(False))


if __name__ == "__main__":
    _stats_port = start_server()

    _drive_watcher = DriveUploader()
    _sheets_watcher = SheetsReporter()
    if _drive_watcher.user_email:
        _sheets_watcher.compartir_con(_drive_watcher.user_email)
    _watcher = FileWatcher(_drive_watcher, _sheets_watcher)
    _watcher.start()

    app = App()
    app.set_stats_port(_stats_port)

    # Initial stats: fetch total documents before any run and update dashboard
    try:
        total = Memory().total_docs()
        app.update_stats(total)
    except Exception:
        pass

    # Ejecutar el scraper en un hilo separado para no bloquear la interfaz gráfica
    def start_ui_run():
        stop_event = threading.Event()

        # wire stop button immediately to the stop_event
        try:
            app.dashboard.set_stop_callback(lambda: stop_event.set())
        except Exception:
            pass

        # set UI running state and start worker thread
        app.set_running(True)
        t = threading.Thread(target=start_scrape_thread, args=(app, stop_event), daemon=True)
        t.start()

    app.set_run_callback(start_ui_run)

    def sync_desde_drive(on_progress=None):
        count = _drive_watcher.sync_from_drive("downloads", on_progress=on_progress)
        if on_progress:
            on_progress(f"✓ Sincronización completada: {count} archivo(s) descargados desde Drive")

    app.dashboard.set_sync_callback(sync_desde_drive)

    def subir_pendientes(on_progress=None):
        count = _drive_watcher.upload_pending_to_drive(
            "downloads", on_progress=on_progress, sheets_reporter=_sheets_watcher
        )
        if on_progress:
            on_progress(f"✓ Subida completada: {count} archivo(s) enviados a Drive")

    app.dashboard.set_upload_pending_callback(subir_pendientes)

    app.mainloop()
    _watcher.stop()
    _drive_watcher.close()
    _sheets_watcher.close()
