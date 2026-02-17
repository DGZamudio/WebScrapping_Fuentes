from scrappers.consejoestado import ScrapConsejoEstado
from scrappers.csupremjusticia import ScrapCorteSuprema
from .constitucional import ScrapConstitucional

SCRAPERS = {
    "constitucional": ScrapConstitucional(),
    "corte suprema": ScrapCorteSuprema(),
    "consejo estado": ScrapConsejoEstado(), # Tarea pesada
}