import locale
from pathlib import Path
import logging

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    encoding="utf-8"
)

DB_PATH = Path("memory.db")

# options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # sin abrir navegador
# options.add_argument("--start-maximized")

# driver = webdriver.Chrome(
#     service=Service(ChromeDriverManager().install()),
#     options=options
# )

# wait = WebDriverWait(driver, 20)
try:
    locale.setlocale(locale.LC_TIME, 'Spanish_Colombia')
except Exception as e:
    logging.error("Error al obtener locale")

#Entidades#

# Corte Constitucional
def CORTE_CONSTITUCIONAL_URL(
        fini: str,
        ffin: str,
        q: str = "",
        limit: int = 1000,
    ):
    return f"https://www.corteconstitucional.gov.co/relatoria/buscador_new/?searchOption=texto&fini={fini}&ffin={ffin}&buscar_por={q}&maxprov={limit}&slop=1&accion=search&tipo=json"

CORTE_CONSTITUCIONAL_DOWNLOAD_URL = "https://www.corteconstitucional.gov.co/sentencias/"




# Corte Suprema de Justicia
CORTE_SUPREMA_URL = "https://consultaprovidenciasbk.cortesuprema.gov.co/api"



# JEP
JEP_URL = "https://relatoria.jep.gov.co/listarProvidecias"
JEP_DOWNLOAD_URL = "https://relatoria.jep.gov.co/"



# Tribunales Administrativos
SAMAI_URL = "https://samai.consejodeestado.gov.co/vistas/utiles/WEstados.aspx"

# Tribunales Superiores
TRIBUNALES_SUPERIORES_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"



# Consejo Nacional de Disciplina Judicial
CNDJ_BASE_URL = "https://relatoria.cndj.gov.co/"
CNDJ_DOWNLOAD_URL = "https://relatoria.cndj.gov.co/docs_relatoria/"