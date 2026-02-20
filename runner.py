from datetime import datetime
import logging
from downloader import Downloader
from db.memory import Memory
from scrappers import SCRAPERS
from utils import make_doc_id
from pathlib import Path

Path("downloads").mkdir(exist_ok=True)


def run_scrapers(fini=None, ffin=None, on_new_doc=None, on_progress=None, on_stats=None, stop_event=None, allowed_sources=None):
    # stop_event: optional threading.Event-like object; if set, the runner will stop cooperatively
    """Ejecuta todos los scrapers configurados y descarga documentos no vistos.

    Callbacks:
      - on_new_doc(doc): Se usa cuando un documento nuevo es descargado exitosamente. Recibe el documento como argumento.
      - on_progress(msg): Se usa para reportar progreso o errores. Recibe un mensaje de texto como argumento.
    """
    db = Memory()
    dw = Downloader()
    # Emit initial stats before starting downloads
    try:
        if on_stats:
            on_stats(db.total_docs())
    except Exception:
        pass

    if ffin is None:
        ffin = datetime.now().strftime("%Y-%m-%d")

    results = {}
    # determine which scrapers to run
    keys = list(SCRAPERS.keys())
    if allowed_sources is not None:
        keys = [k for k in keys if k in set(allowed_sources)]

    for key in keys:
        # check cancellation before starting next source
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            if on_progress:
                on_progress("Cancelado por el usuario antes de iniciar siguiente fuente")
            return results
        if not fini:
            fini = db.get_last_inserted(SCRAPERS[key].source)

        scraper = SCRAPERS[key]
        msg = f"Scraping {scraper.source} desde {fini} hasta {ffin}..."
        logging.info(msg)
        if on_progress:
            on_progress(msg)

        count = 0
        try:
            docs = scraper.scrap(fini=fini, ffin=ffin)
            for doc in docs:
                # check cancellation between documents
                if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                    if on_progress:
                        on_progress("Cancelado por el usuario")
                    return results
                if "body" in doc["link"] and doc["link"]["body"] and "path" in doc["link"]["body"]:
                    doc_id = make_doc_id(doc["link"]["body"]["path"])
                else:
                    doc_id = make_doc_id(doc["link"]["url"])

                if not db.seen(doc_id):
                    try:
                        # check cancellation right before starting a potentially long download
                        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                            if on_progress:
                                on_progress("Cancelado por el usuario antes de descargar")
                            return results
                        dw.download(doc, stop_event=stop_event)
                        db.mark(doc_id, doc)
                        count += 1
                        logging.info(msg)
                        if on_new_doc:
                            on_new_doc(doc)
                    except Exception as download_error:
                        logging.error(f"Error al descargar {doc['title']}: {download_error}")
        except Exception as e:
            logging.error(f"Error scraping {scraper.source}: {e}")
            if on_progress:
                on_progress(f"Error scraping {scraper.source}: {e}")

        results[scraper.source] = count
        msg = f"Total de documentos descargados para {scraper.source}: {count}"
        if on_progress:
            on_progress(msg)
        logging.info(msg)
        # update stats after finishing each source
        try:
            if on_stats:
                on_stats(db.total_docs())
        except Exception:
            pass

    return results
