from datetime import datetime
import logging
from downloader import Downloader
from drive_uploader import DriveUploader
from sheets_reporter import SheetsReporter
from db.memory import Memory
from scrappers import SCRAPERS
from utils import make_doc_id
from pathlib import Path

Path("downloads").mkdir(exist_ok=True)


def run_scrapers(fini=None, ffin=None, on_new_doc=None, on_progress=None, on_stats=None, stop_event=None, allowed_sources=None, source_options=None):
    # stop_event: optional threading.Event-like object; if set, the runner will stop cooperatively
    """Ejecuta todos los scrapers configurados y descarga documentos no vistos.

    Callbacks:
      - on_new_doc(doc): Se usa cuando un documento nuevo es descargado exitosamente. Recibe el documento como argumento.
      - on_progress(msg): Se usa para reportar progreso o errores. Recibe un mensaje de texto como argumento.
    """
    db = Memory()
    dw = Downloader()
    drive = DriveUploader()
    sheets = SheetsReporter()
    docs_por_fuente: dict = {}
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

    try:
        for key in keys:
            # check cancellation before starting next source
            if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                if on_progress:
                    on_progress("Cancelado por el usuario antes de iniciar siguiente fuente")
                return results
            if not fini:
                fini = db.get_last_inserted(SCRAPERS[key].source)

            scraper = SCRAPERS[key]
            opts = (source_options or {}).get(scraper.source, {})
            if hasattr(scraper, "include_details") and "include_details" in opts:
                scraper.include_details = opts["include_details"]
            msg = f"Scraping {scraper.source} desde {fini} hasta {ffin}..."
            logging.info(msg)
            if on_progress:
                on_progress(msg)

            count = 0
            try:
                docs = scraper.scrap(fini=fini, ffin=ffin, stop_event=stop_event, on_progress=on_progress)
                for doc in docs:
                    # check cancellation between documents
                    if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                        if on_progress:
                            on_progress("Cancelado por el usuario")
                        return results
                    if "body" in doc["link"] and doc["link"]["body"] and "path" in doc["link"]["body"]:
                        doc_id = make_doc_id(doc["link"]["body"]["path"], doc["f_public"])
                    else:
                        doc_id = make_doc_id(doc["link"]["url"], doc["f_public"])

                    if not db.seen(doc_id):
                        drive_url = drive.archivo_existe(doc_id)
                        if drive_url:
                            # otro computador ya descargó este documento
                            docs_por_fuente.setdefault(key, []).append((doc, drive_url))
                            db.mark(doc_id, doc)
                            count += 1
                            if on_new_doc:
                                on_new_doc(doc)
                        else:
                            try:
                                # check cancellation right before starting a potentially long download
                                if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                                    if on_progress:
                                        on_progress("Cancelado por el usuario antes de descargar")
                                    return results
                                out_path = dw.download(doc, stop_event=stop_event)
                                drive_url = drive.upload_file(out_path, doc, doc_id)
                                docs_por_fuente.setdefault(key, []).append((doc, drive_url))
                                try:
                                    local_rel = str(out_path.relative_to(Path("downloads"))).replace("\\", "/")
                                except ValueError:
                                    local_rel = None
                                db.mark(doc_id, doc, local_path=local_rel)
                                count += 1
                                logging.info(msg)
                                if on_new_doc:
                                    on_new_doc(doc)
                            except FileNotFoundError as missing:
                                logging.warning(str(missing))
                            except Exception as download_error:
                                msg = f"Error al descargar {doc['title']}: {download_error}"
                                logging.error(msg)
                                if on_progress:
                                    on_progress(msg)
            except Exception as e:
                logging.error(f"Error scraping {scraper.source}: {e}")
                if on_progress:
                    on_progress(f"Error scraping {scraper.source}: {e}")

            results[key] = count
            msg = f"Total de documentos descargados para {scraper.source}: {count}"
            if on_progress:
                on_progress(msg)
            logging.info(msg)
            try:
                if on_stats:
                    on_stats(db.total_docs())
            except Exception:
                pass

        return results
    finally:
        sheets.report_run(docs_por_fuente)
        sheets.close()
        drive.close()
        dw.close()
