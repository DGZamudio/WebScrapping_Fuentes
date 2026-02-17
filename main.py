from datetime import datetime
import logging
from downloader import Downloader
from db.memory import Memory
from scrappers import SCRAPERS
from utils import make_doc_id
from pathlib import Path

Path("downloads").mkdir(exist_ok=True)

db = Memory()
dw = Downloader()
scraper = None

for key in SCRAPERS:
    scraper = SCRAPERS[key]
    logging.info(f"Scraping {scraper.source}...")

    hoy = datetime.now().strftime("%Y-%m-%d")
    
    try:
        docs = scraper.scrap(fini="2026-02-01", ffin=hoy) #db.get_last_inserted(scraper.source) prod

        count = 0
        for doc in docs:
            # Safe extraction of doc_id - handle both POST (with body) and GET (no body)
            if "body" in doc["link"] and doc["link"]["body"] and "path" in doc["link"]["body"]:
                doc_id = make_doc_id(doc["link"]["body"]["path"])
            else:
                doc_id = make_doc_id(doc["link"]["url"])

            if not db.seen(doc_id):
                try:
                    dw.download(doc)
                    db.mark(doc_id, doc)
                    logging.info(f"New doc: {doc['title']} - {doc['link']}")
                    count += 1
                except Exception as download_error:
                    logging.error(f"Failed to download {doc['title']}: {download_error}")
        
        print(f"Total new documents downloaded for {scraper.source}: {count}")
    except Exception as e:
        logging.error(f"Error scraping {scraper.source}: {e}")