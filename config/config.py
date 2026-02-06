from pathlib import Path

DB_PATH = Path("memory.db")

def CORTE_CONSTITUCIONAL_URL(
        fini: str,
        ffin: str,
        q: str ="",
        limit: int = 1000,
    ):
    return f"https://www.corteconstitucional.gov.co/relatoria/buscador_new/?searchOption=texto&fini={fini}&ffin={ffin}&buscar_por={q}&maxprov={limit}&slop=1&accion=search&tipo=json"

CORTE_CONSTITUCIONAL_DOWNLOAD_URL = "https://www.corteconstitucional.gov.co/sentencias/"