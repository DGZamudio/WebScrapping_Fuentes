from pathlib import Path
import requests

from models.models import RawDocModel
from utils import extract_filename

class Downloader:
    def __init__(self):
        pass

    def download(self, doc: RawDocModel, filename=None):
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        with requests.get(doc["link"], headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "")
            disposition = r.headers.get("Content-Disposition", "")

            if not filename:
                filename = extract_filename(disposition, content_type, doc["link"])

            out_path = Path(f"downloads/{doc.f_public.replace('-', '')}/{doc.source}/{doc.tipo}/{filename}")
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)

            return out_path