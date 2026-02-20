import threading
from ui.app import App
from runner import run_scrapers
from db.memory import Memory


def start_scrape_thread(app: App, stop_event: "threading.Event"):
    # Read dates from settings just before starting
    try:
        cfg = app.settings_view.get_dates()
    except Exception:
        cfg = {}

    fini = cfg.get("start") or None
    ffin = cfg.get("end") or None
    # read enabled scrapers from settings
    try:
        allowed = app.settings_view.get_enabled_sources()
    except Exception:
        allowed = None

    def on_new_doc(doc):
        app.after(0, lambda: app.log(f"Nuevo documento descargado: {doc['title']}"))

    def on_progress(msg):
        app.after(0, lambda: app.log(msg))

    def on_stats(count):
        app.after(0, lambda: app.update_stats(count))

    try:
        run_scrapers(fini=fini, ffin=ffin, on_new_doc=on_new_doc, on_progress=on_progress, on_stats=on_stats, stop_event=stop_event, allowed_sources=allowed)
    finally:
        # ensure UI is unblocked when worker finishes
        app.after(0, lambda: app.set_running(False))


if __name__ == "__main__":
    app = App()

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
            app.console.set_stop_callback(lambda: stop_event.set())
        except Exception:
            pass

        # set UI running state and start worker thread
        app.set_running(True)
        t = threading.Thread(target=start_scrape_thread, args=(app, stop_event), daemon=True)
        t.start()

    app.set_run_callback(start_ui_run)

    app.mainloop()
