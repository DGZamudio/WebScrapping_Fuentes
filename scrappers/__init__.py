from scrappers.consejoestado import ScrapConsejoEstado
from scrappers.csupremjusticia import ScrapCorteSuprema
from scrappers.tribunales import ScrapTribunales
from .constitucional import ScrapConstitucional

SCRAPERS = {
    "Corte Constitucional": ScrapConstitucional(),
    "Corte Suprema": ScrapCorteSuprema(),
    "Consejo de Estado": ScrapConsejoEstado(), # Tarea pesada
    "Tribunales": ScrapTribunales() # Tarea pesada
}