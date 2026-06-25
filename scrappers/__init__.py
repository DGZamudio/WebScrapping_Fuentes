from scrappers.cndj import ScrapCNDJ
from scrappers.csupremjusticia import ScrapCorteSuprema
from scrappers.jep import ScrapJEP
from scrappers.samai import ScrapTribunales, _SAMAI_CORPS
from scrappers.tribunales_superiores import ScrapTribunalesSuperiores, _SUPERIORES_DEPTS
from .constitucional import ScrapConstitucional

SCRAPERS = {
    "Corte Constitucional": ScrapConstitucional(),
    "Corte Suprema": ScrapCorteSuprema(),
    "JEP": ScrapJEP(),
    **{
        dept_name: ScrapTribunalesSuperiores(dept_code=dept_code, dept_name=dept_name)
        for dept_code, dept_name in _SUPERIORES_DEPTS.items()
    },
    **{
        corp_name: ScrapTribunales(corp_code=corp_code, corp_name=corp_name)
        for corp_code, corp_name in _SAMAI_CORPS.items()
    },
    "Consejo Nacional de Disciplina Judicial": ScrapCNDJ(),
}
