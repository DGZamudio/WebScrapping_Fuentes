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
            combined["Fecha Publicación"] = pd.to_datetime(
                combined["Fecha Publicación"], errors="coerce"
            )
            combined["Fecha Captura"] = pd.to_datetime(
                combined["Fecha Captura"], errors="coerce"
            )
            combined = combined.dropna(subset=["Fecha Publicación"])
            return combined if not combined.empty else None

        except Exception as e:
            logging.warning(f"SheetsDataLoader: error cargando datos ({e})")
            return None
