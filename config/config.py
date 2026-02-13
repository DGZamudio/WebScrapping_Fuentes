import locale
from pathlib import Path
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    encoding="utf-8"
)

DB_PATH = Path("memory.db")

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # sin abrir navegador
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 20)

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

#Entidades#

def CORTE_CONSTITUCIONAL_URL(
        fini: str,
        ffin: str,
        q: str ="",
        limit: int = 1000,
    ):
    return f"https://www.corteconstitucional.gov.co/relatoria/buscador_new/?searchOption=texto&fini={fini}&ffin={ffin}&buscar_por={q}&maxprov={limit}&slop=1&accion=search&tipo=json"
CORTE_CONSTITUCIONAL_DOWNLOAD_URL = "https://www.corteconstitucional.gov.co/sentencias/"

CONSEJO_ESTADO_URL = "https://samai.consejodeestado.gov.co/TitulacionRelatoria/BuscadorProvidenciasTituladas.aspx"

CORTE_SUPREMA_URL = "https://consultaprovidenciasbk.cortesuprema.gov.co/api"