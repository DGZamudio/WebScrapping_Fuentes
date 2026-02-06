import hashlib
import re

def make_doc_id(url):
    return hashlib.sha1(url.encode()).hexdigest()

def extract_filename(disposition, content_type, url):
    if disposition:
        match = re.search(r'filename="?([^"]+)"?', disposition)
        if match:
            return match.group(1)

    if "rtf" in content_type.lower():
        ext = ".rtf"
    elif "pdf" in content_type.lower():
        ext = ".pdf"
    else:
        ext = ""

    return url.split("/")[-1] or f"document{ext}"
