import logging
import time
from datetime import datetime
from pathlib import Path

import gspread
import requests
from google.oauth2 import service_account

from models.models import RawDocModel

_CREDENTIALS_PATH = Path("config/credentials.json")
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# fallos de red (DNS caído, timeout, conexión rechazada) — no otros errores como
# cuota excedida o problemas de permisos, que reintentar de inmediato no arregla
_ERRORES_DE_RED = (requests.exceptions.RequestException,)
_MAX_REINTENTOS = 3
_ESPERA_INICIAL_SEG = 5


class SheetsReporter:
    SHEET_NAME = "IURISYNC - Providencias"
    HEADERS = ["Fecha Publicación", "Título", "Tipo", "Fecha Captura", "Enlace Drive", "Fecha Providencia", "Sección", "Detalle", "Especialidad", "Magistrado"]

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

    def _con_reintentos(self, func, descripcion: str):
        """Reintenta func() con espera creciente, solo ante fallos de red —
        si el corte de conexión persiste tras _MAX_REINTENTOS, se propaga."""
        espera = _ESPERA_INICIAL_SEG
        for intento in range(1, _MAX_REINTENTOS + 1):
            try:
                return func()
            except _ERRORES_DE_RED as e:
                if intento == _MAX_REINTENTOS:
                    raise
                logging.warning(
                    f"SheetsReporter: fallo de red en {descripcion} "
                    f"(intento {intento}/{_MAX_REINTENTOS}): {e}. Reintentando en {espera}s..."
                )
                time.sleep(espera)
                espera *= 2

    def _ensure_tab(self, source: str) -> gspread.Worksheet:
        try:
            ws = self._sheet.worksheet(source)
        except gspread.exceptions.WorksheetNotFound:
            ws = self._sheet.add_worksheet(
                title=source, rows=1000, cols=len(self.HEADERS)
            )
            ws.append_row(self.HEADERS)
            return ws

        # tabs creados antes de agregar columnas nuevas solo tienen menos columnas;
        # se completan al final sin tocar las columnas ya existentes
        existentes = ws.row_values(1)
        if existentes != self.HEADERS:
            faltantes = self.HEADERS[len(existentes):]
            if faltantes:
                rango = f"{gspread.utils.rowcol_to_a1(1, len(existentes) + 1)}:{gspread.utils.rowcol_to_a1(1, len(self.HEADERS))}"
                ws.update(rango, [faltantes])
        return ws

    def report_run(self, docs_por_fuente: dict) -> None:
        if self._client is None:
            return
        fecha_captura = datetime.now().strftime("%Y-%m-%d")
        for source_docs in docs_por_fuente.values():
            if not source_docs:
                continue
            source_name = source_docs[0][0].source
            # cada fuente se maneja aparte: si una falla incluso tras reintentar,
            # las demás igual se reportan en vez de perderse todas juntas
            try:
                ws = self._con_reintentos(
                    lambda: self._ensure_tab(source_name), f"abrir pestaña '{source_name}'"
                )
                rows = [
                    [
                        doc.f_public,
                        doc.title,
                        doc.tipo,
                        fecha_captura,
                        drive_url or "",
                        doc.f_providencia or "",
                        doc.seccion or "",
                        doc.detalle or "",
                        doc.especialidad or "",
                        doc.magistrado or "",
                    ]
                    for doc, drive_url in source_docs
                ]
                self._con_reintentos(
                    lambda: ws.append_rows(rows, value_input_option="USER_ENTERED"),
                    f"escribir filas en '{source_name}'",
                )
                logging.info(
                    f"SheetsReporter: {len(rows)} filas agregadas en '{source_name}'"
                )
            except Exception as e:
                logging.warning(f"SheetsReporter: error en report_run para '{source_name}': {e}")

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
            ya_tiene_acceso = any(
                p.get("emailAddress", "").lower() == email.lower()
                for p in self._sheet.list_permissions()
            )
            if ya_tiene_acceso:
                return
            self._sheet.share(email, perm_type="user", role="reader", notify=False)
            logging.info(f"SheetsReporter: Sheet compartido con {email}")
        except Exception as e:
            logging.warning(f"SheetsReporter: no se pudo compartir Sheet con {email} ({e})")

    def close(self):
        self._client = None
        self._sheet = None
