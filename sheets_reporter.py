import logging
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2 import service_account

from models.models import RawDocModel

_CREDENTIALS_PATH = Path("config/credentials.json")
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsReporter:
    SHEET_NAME = "IURISYNC - Providencias"
    HEADERS = ["Fecha Publicación", "Título", "Tipo", "Fecha Captura", "Enlace Drive"]

    def __init__(self):
        self._client = None
        self._sheet = None
        self._init_client()

    def _init_client(self):
        if not _CREDENTIALS_PATH.exists():
            logging.warning(
                "SheetsReporter: config/credentials.json no encontrado — "
                "reporte a Sheets deshabilitado"
            )
            return
        try:
            creds = service_account.Credentials.from_service_account_file(
                str(_CREDENTIALS_PATH), scopes=_SCOPES
            )
            self._client = gspread.Client(auth=creds)
            try:
                self._sheet = self._client.open(self.SHEET_NAME)
                logging.info(f"SheetsReporter: conectado a '{self.SHEET_NAME}'")
            except gspread.exceptions.SpreadsheetNotFound:
                self._sheet = self._client.create(self.SHEET_NAME)
                logging.info(
                    f"SheetsReporter: Sheet creado → "
                    f"https://docs.google.com/spreadsheets/d/{self._sheet.id}"
                )
        except Exception as e:
            logging.warning(
                f"SheetsReporter: no se pudo inicializar ({e}) — reporte deshabilitado"
            )
            self._client = None
            self._sheet = None

    def _ensure_tab(self, source: str) -> gspread.Worksheet:
        try:
            return self._sheet.worksheet(source)
        except gspread.exceptions.WorksheetNotFound:
            ws = self._sheet.add_worksheet(
                title=source, rows=1000, cols=len(self.HEADERS)
            )
            ws.append_row(self.HEADERS)
            return ws

    def report_run(self, docs_por_fuente: dict) -> None:
        if self._client is None:
            return
        try:
            fecha_captura = datetime.now().strftime("%Y-%m-%d")
            for source_docs in docs_por_fuente.values():
                if not source_docs:
                    continue
                source_name = source_docs[0][0].source
                ws = self._ensure_tab(source_name)
                rows = [
                    [
                        doc.f_public,
                        doc.title,
                        doc.tipo,
                        fecha_captura,
                        drive_url or "",
                    ]
                    for doc, drive_url in source_docs
                ]
                ws.append_rows(rows, value_input_option="USER_ENTERED")
                logging.info(
                    f"SheetsReporter: {len(rows)} filas agregadas en '{source_name}'"
                )
        except Exception as e:
            logging.warning(f"SheetsReporter: error en report_run: {e}")

    def delete_row_by_drive_url(self, drive_url: str) -> None:
        if self._sheet is None:
            return
        try:
            for ws in self._sheet.worksheets():
                try:
                    cell = ws.find(drive_url, in_column=5)
                    if cell:
                        ws.delete_rows(cell.row)
                        logging.info(f"SheetsReporter: fila eliminada en '{ws.title}' — {drive_url}")
                        return
                except Exception:
                    continue
        except Exception as e:
            logging.warning(f"SheetsReporter: error eliminando fila ({e})")

    def agregar_fila(self, source: str, f_public: str, titulo: str, tipo: str, drive_url: str) -> None:
        """Agrega una fila nueva a la pestaña de la fuente."""
        if self._sheet is None:
            return
        try:
            ws = self._ensure_tab(source)
            fecha_captura = datetime.now().strftime("%Y-%m-%d")
            ws.append_row(
                [f_public, titulo, tipo, fecha_captura, drive_url],
                value_input_option="USER_ENTERED",
            )
            logging.info(f"SheetsReporter: fila agregada en '{source}' — {titulo}")
        except Exception as e:
            logging.warning(f"SheetsReporter: no se pudo agregar fila para '{titulo}': {e}")

    def actualizar_enlace_drive(self, source: str, titulo: str, drive_url: str) -> bool:
        if self._sheet is None:
            return False
        try:
            ws = self._sheet.worksheet(source)
            cell = ws.find(titulo, in_column=2)
            if cell:
                ws.update_cell(cell.row, 5, drive_url)
                logging.info(f"SheetsReporter: enlace Drive actualizado — fila {cell.row} en '{source}'")
                return True
        except Exception as e:
            logging.warning(f"SheetsReporter: no se pudo actualizar enlace Drive para '{titulo}': {e}")
        return False

    def compartir_con(self, email: str) -> None:
        if self._sheet is None:
            return
        try:
            self._sheet.share(email, perm_type="user", role="reader", notify=False)
            logging.info(f"SheetsReporter: Sheet compartido con {email}")
        except Exception as e:
            logging.warning(f"SheetsReporter: no se pudo compartir Sheet con {email} ({e})")

    def close(self):
        self._client = None
        self._sheet = None
