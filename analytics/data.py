import logging
from pathlib import Path

import pandas as pd

_CREDENTIALS_PATH = Path("config/credentials.json")
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsDataLoader:
    SHEET_NAME = "IURISYNC - Providencias"
    COLUMNS = ["Fecha Publicación", "Título", "Tipo", "Fecha Captura", "Enlace Drive"]

    def load(self) -> "pd.DataFrame | None":
        if not _CREDENTIALS_PATH.exists():
            logging.warning("SheetsDataLoader: credentials.json no encontrado")
            return None
        try:
            import gspread
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_file(
                str(_CREDENTIALS_PATH), scopes=_SCOPES
            )
            client = gspread.Client(auth=creds)
            try:
                sheet = client.open(self.SHEET_NAME)
            except gspread.exceptions.SpreadsheetNotFound:
                logging.warning(
                    f"SheetsDataLoader: Sheet '{self.SHEET_NAME}' no encontrado"
                )
                return None

            frames = []
            for ws in sheet.worksheets():
                rows = ws.get_all_records(expected_headers=self.COLUMNS)
                if not rows:
                    continue
                df = pd.DataFrame(rows)
                df["Fuente"] = ws.title
                frames.append(df)

            if not frames:
                return None

            combined = pd.concat(frames, ignore_index=True)
            # gspread castea celdas numéricas (ej. el año "2026" de JEP) a int,
            # mientras otras fuentes guardan fecha completa como str ("2026-07-08").
            # astype(str) evita que pd.to_datetime interprete esos int como
            # nanosegundos desde epoch (dando fechas basura cerca de 1970).
            # format="mixed" evita que un solo formato inferido para toda la
            # columna descarte como NaT el formato minoritario (año vs fecha completa).
            combined["Fecha Publicación"] = pd.to_datetime(
                combined["Fecha Publicación"].astype(str), format="mixed", errors="coerce"
            )
            combined["Fecha Captura"] = pd.to_datetime(
                combined["Fecha Captura"].astype(str), format="mixed", errors="coerce"
            )
            combined = combined.dropna(subset=["Fecha Publicación"])
            return combined if not combined.empty else None

        except Exception as e:
            logging.warning(f"SheetsDataLoader: error cargando datos ({e})")
            return None
