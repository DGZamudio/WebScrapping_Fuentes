from pathlib import Path
import logging

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    encoding="utf-8"
)

DB_PATH = Path("memory.db")


def CORTE_CONSTITUCIONAL_URL(
        fini: str,
        ffin: str,
        q: str ="",
        limit: int = 1000,
    ):
    return f"https://www.corteconstitucional.gov.co/relatoria/buscador_new/?searchOption=texto&fini={fini}&ffin={ffin}&buscar_por={q}&maxprov={limit}&slop=1&accion=search&tipo=json"
CORTE_CONSTITUCIONAL_DOWNLOAD_URL = "https://www.corteconstitucional.gov.co/sentencias/"


CONSEJO_ESTADO_URL = "https://samai.consejodeestado.gov.co/TitulacionRelatoria/BuscadorProvidenciasTituladas.aspx"
CONSEJO_ESTADO_DOWNLOAD_URL = "https://samaicore.consejodeestado.gov.co/api/DescargarProvidenciaPublica"

CORTE_SUPREMA_URL = "https://consultajurisprudencial.ramajudicial.gov.co/WebRelatoria/csj/index.xhtml"