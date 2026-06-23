from scrappers.cndj import ScrapCNDJ
from scrappers.consejoestado import ScrapConsejoEstado
from scrappers.csupremjusticia import ScrapCorteSuprema
from scrappers.jep import ScrapJEP
from scrappers.tribunales import ScrapTribunales, _TRIBUNALES
from scrappers.tribunales_superiores import ScrapTribunalesSuperiores
from .constitucional import ScrapConstitucional

SCRAPERS = {
    "Corte Constitucional": ScrapConstitucional(),
    "Corte Suprema": ScrapCorteSuprema(),
    "Consejo de Estado": ScrapConsejoEstado(),
    "JEP": ScrapJEP(),
    "Tribunales Superiores": ScrapTribunalesSuperiores(),
    **{
        corp_name: ScrapTribunales(corp_code=corp_code, corp_name=corp_name)
        for corp_code, corp_name in _TRIBUNALES.items()
    },
    "Consejo Nacional de Disciplina Judicial": ScrapCNDJ(),
}


def discover_tribunales():
    """Kept for backwards compatibility — tribunales are now populated at import time."""
    return SCRAPERS
