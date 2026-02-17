import hashlib
import re

def make_doc_id(title):
    return hashlib.sha1(title.encode()).hexdigest()

def extract_filename(disposition, content_type, url, opt_title):
    if disposition:
        match = re.search(r'filename="?([^"]+)"?', disposition)
        if match:
            filename = match.group(1)
            # Extract extension from filename
            ext = "." + filename.split(".")[-1] if "." in filename else ""
            return {"filename": filename.split(".")[0], "extension": ext}

    if "rtf" in content_type.lower():
        ext = ".rtf"
    elif "pdf" in content_type.lower():
        ext = ".pdf"
    elif "word" in content_type.lower() or "officedocument" in content_type.lower():
        ext = ".docx"
    else:
        ext = ""

    return {"filename": url.split("/")[-1] or opt_title, "extension": ext}
