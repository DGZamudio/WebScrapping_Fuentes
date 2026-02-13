from scrappers.consejoestado import ScrapConsejoEstado
from scrappers.csupremjusticia import ScrapCorteSuprema
from .constitucional import ScrapConstitucional

SCRAPERS = {
    "consejo estado": ScrapConsejoEstado(),
    "constitucional": ScrapConstitucional(),
    # "corte suprema": ScrapCorteSuprema()
}
