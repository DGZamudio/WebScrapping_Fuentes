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
        
        if doc.link["method"] == "POST":
            headers["Content-Type"] = "application/json"
            body = doc.link.get("body", {})
            response = requests.post(doc.link["url"], json=body, headers=headers, stream=True, timeout=60)
        else:
            response = requests.get(doc.link["url"], headers=headers, stream=True, timeout=60)
        
        with response as r:
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "")
            disposition = r.headers.get("Content-Disposition", "")

            if not filename:
                filename = extract_filename(disposition, content_type, doc.link["url"], doc.title)

            if doc.save_path:
                out_path = Path(f"{doc.save_path.replace('(filename)', filename['filename']).replace('(extension)', filename['extension'])}")
            else:
                out_path = Path(f"downloads/{doc.source}/{doc.f_public}/{doc.tipo}/{filename['filename']}{filename['extension']}")
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)

            return out_path