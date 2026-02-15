from scrappers.consejoestado import ScrapConsejoEstado
from scrappers.csupremjusticia import ScrapCorteSuprema
from .constitucional import ScrapConstitucional

SCRAPERS = {
    "corte suprema": ScrapCorteSuprema(),
    "constitucional": ScrapConstitucional(),
    "consejo estado": ScrapConsejoEstado(), # Tarea pesada
}