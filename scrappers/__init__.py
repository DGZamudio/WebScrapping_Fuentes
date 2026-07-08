from scrappers.cndj import ScrapCNDJ
from scrappers.csupremjusticia import ScrapCorteSuprema
from scrappers.jep import ScrapJEP
from scrappers.samai import ScrapTribunales, _SAMAI_CORPS
from scrappers.rama_judicial import ScrapRamaJudicial, _SUPERIORES_DEPTS, _JUZGADOS_ENTIDADES
from .constitucional import ScrapConstitucional

SCRAPERS = {
    "Corte Constitucional": ScrapConstitucional(),
    "Corte Suprema": ScrapCorteSuprema(),
    "JEP": ScrapJEP(),
    **{
        dept_name: ScrapRamaJudicial(dept_code=dept_code, dept_name=dept_name, entidad_id="22")
        for dept_code, dept_name in _SUPERIORES_DEPTS.items()
    },
    **{
        juz_name: ScrapRamaJudicial(dept_code="", dept_name=juz_name, entidad_id=juz_id)
        for juz_id, juz_name in _JUZGADOS_ENTIDADES.items()
    },
    **{
        corp_name: ScrapTribunales(corp_code=corp_code, corp_name=corp_name)
        for corp_code, corp_name in _SAMAI_CORPS.items()
    },
    "Consejo Nacional de Disciplina Judicial": ScrapCNDJ(),
}
