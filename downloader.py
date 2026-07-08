import logging
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

from models.models import RawDocModel
from utils import extract_filename

# Word SaveAs format constants
_WORD_FORMATS = {"rtf": 6, "docx": 16, "pdf": 17}


def _pdf_to_rtf_fallback(input_path: Path) -> Path:
    from pypdf import PdfReader
    reader = PdfReader(str(input_path))
    if reader.is_encrypted:
        reader.decrypt("")
    output_path = input_path.with_suffix(".rtf")
    with open(output_path, "w", encoding="ascii", errors="replace") as f:
        f.write("{\\rtf1\\ansi\\ansicpg1252\\deff0\n")
        f.write("{\\fonttbl{\\f0\\froman\\fcharset0 Times New Roman;}}\n")
        f.write("\\f0\\fs24\n")
        for page in reader.pages:
            for line in (page.extract_text() or "").splitlines():
                escaped = line.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
                rtf_line = "".join(f"\\u{ord(c)}?" if ord(c) > 127 else c for c in escaped)
                f.write(rtf_line + "\\par\n")
            f.write("\\par\n")
        f.write("}\n")
    return output_path


class WordConverter:
    """Abre Word una sola vez y reutiliza la instancia para todas las conversiones."""

    def __init__(self):
        self._word = None

    def _get_word(self):
        if self._word is None:
            import win32com.client
            self._word = win32com.client.Dispatch("Word.Application")
            self._word.Visible = False
            self._word.DisplayAlerts = 0
        return self._word

    def convert(self, input_path: Path, target_format: str) -> Path:
        fmt = _WORD_FORMATS.get(target_format)
        if fmt is None:
            raise ValueError(f"Formato no soportado: {target_format}")

        output_path = input_path.with_suffix(f".{target_format}")
        word = self._get_word()
        doc = word.Documents.Open(
            str(input_path.resolve()),
            ConfirmConversions=False,
            AddToRecentFiles=False,
        )
        doc.SaveAs(str(output_path.resolve()), FileFormat=fmt)
        doc.Close(SaveChanges=False)

        if not output_path.exists():
            raise RuntimeError(f"Word no generó el archivo esperado: {output_path}")
        return output_path

    def quit(self):
        if self._word is not None:
            try:
                self._word.Quit()
            except Exception:
                pass
            self._word = None


class Downloader:
    def __init__(self):
        self._word_converter = WordConverter()

    def _convert(self, out_path: Path, target_format: str) -> Path:
        if target_format == "rtf_word":
            # Word COM first, pypdf fallback
            try:
                return self._word_converter.convert(out_path, "rtf")
            except Exception as word_err:
                logging.warning(f"WordConverter fallo ({out_path.name}): {word_err}. Usando pypdf fallback.")
                try:
                    return _pdf_to_rtf_fallback(out_path)
                except Exception as e:
                    logging.warning(f"No se pudo convertir a RTF ({out_path.name}): {e}")
                    return out_path
        elif target_format == "rtf":
            try:
                return _pdf_to_rtf_fallback(out_path)
            except Exception as e:
                logging.warning(f"No se pudo convertir a RTF ({out_path.name}): {e}")
                return out_path  # keep PDF if conversion fails
        else:
            raise ValueError(f"Formato no soportado: {target_format}")

    @staticmethod
    def _resolve_jwt_indirect(jwt_url: str, headers: dict) -> requests.Response:
        """Fetch VerProvidencia page → blob URL → stream download.

        Raises FileNotFoundError (not a generic Exception) when the document
        exists in the court system but its file has not yet been uploaded to
        blob storage.  The caller can catch this to skip silently.
        """
        session = requests.Session()
        session.headers.update(headers)
        ver = session.get(jwt_url, timeout=30)
        ver.raise_for_status()
        soup = BeautifulSoup(ver.text, "html.parser")

        blob_url = next(
            (a["href"] for a in soup.find_all("a", href=True)
             if "blob.core.windows.net" in a["href"]),
            None,
        )
        if blob_url:
            return session.get(blob_url, stream=True, timeout=120)

        # Document registered in SAMAI but file not yet available in blob storage
        raise FileNotFoundError(f"Archivo aún no disponible en SAMAI: {jwt_url[:80]}")

    def close(self):
        if self._word_converter:
            self._word_converter.quit()
            self._word_converter = None

    def download(self, doc: RawDocModel, filename=None, stop_event=None):
        headers = {"User-Agent": "Mozilla/5.0"}

        last_exc = None
        for attempt in range(3):
            try:
                if doc.link["method"] == "POST":
                    headers["Content-Type"] = "application/json"
                    body = doc.link.get("body", {})
                    response = requests.post(doc.link["url"], json=body, headers=headers, stream=True, timeout=120)
                elif doc.link["method"] == "jwt_indirect":
                    response = self._resolve_jwt_indirect(doc.link["url"], headers)
                else:
                    response = requests.get(doc.link["url"], headers=headers, stream=True, timeout=120)
                break
            except requests.exceptions.Timeout as e:
                last_exc = e
        else:
            raise last_exc

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

            # Si otro hilo ya descargó el mismo archivo (SAMAI paralelo), saltar
            if out_path.exists() and out_path.stat().st_size > 0:
                return out_path

            try:
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                            try:
                                f.close()
                            except Exception:
                                pass
                            try:
                                out_path.unlink(missing_ok=True)
                            except Exception:
                                pass
                            raise InterruptedError("Download cancelled")
                        if chunk:
                            f.write(chunk)
            except PermissionError:
                # Archivo en uso por otro hilo; si ya tiene contenido, lo usamos
                if out_path.exists() and out_path.stat().st_size > 0:
                    return out_path
                raise

        if doc.convert_to:
            converted = self._convert(out_path, doc.convert_to)
            if converted != out_path:
                # Word COM puede mantener el lock brevemente después de Close()
                for _ in range(5):
                    try:
                        out_path.unlink(missing_ok=True)
                        break
                    except PermissionError:
                        time.sleep(0.5)
            return converted

        return out_path
