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
        docs = scraper.scrap(fini="2026-01-01", ffin=hoy) #db.get_last_inserted(scraper.source) prod

        for doc in docs:
            doc_id = make_doc_id(doc["link"])

            if not db.seen(doc_id):
                logging.info(f"New doc: {doc['title']} - {doc['link']}")
                dw.download(doc)
                db.mark(doc_id, doc)
    except Exception as e:
        logging.error(f"Error scraping {scraper.source}: {e}")