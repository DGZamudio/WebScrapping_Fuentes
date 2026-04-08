from scrappers.consejoestado import ScrapConsejoEstado
from scrappers.csupremjusticia import ScrapCorteSuprema
from scrappers.tribunales import ScrapTribunales
from .constitucional import ScrapConstitucional
import requests
from bs4 import BeautifulSoup
from config.config import CONSEJO_ESTADO_URL

SCRAPERS = {
    "Corte Constitucional": ScrapConstitucional(),
    "Corte Suprema": ScrapCorteSuprema(),
    "Consejo de Estado": ScrapConsejoEstado(), # Tarea pesada
}

_tribunales_discovered = False

def discover_tribunales():
    """Discover all available tribunales from the website and add them to SCRAPERS."""
    global _tribunales_discovered, SCRAPERS
    
    if _tribunales_discovered:
        return SCRAPERS
    
    try:
        # Fetch the page to get tribunal list
        session = requests.Session()
        res = session.get(CONSEJO_ESTADO_URL)
        soup = BeautifulSoup(res.text, "html.parser")
        botones_tribunales = soup.select("#MainContent_CorporacionesTitulanDataList input[type='submit']")
        
        # Add each tribunal (skip first button at index 0)
        for i in range(1, len(botones_tribunales)):
            boton = botones_tribunales[i]
            tribunal_title = boton.get("title", f"Tribunal {i}")
            tribunal_value = boton.get("value", f"tribunal_{i}")
            
            # Create a label combining title and value for clarity
            display_name = f"Tribunal - {tribunal_title}" if tribunal_title != tribunal_value else f"Tribunal {i} - {tribunal_value}"
            
            # Register this tribunal as a separate scraper
            if display_name not in SCRAPERS:
                SCRAPERS[display_name] = ScrapTribunales(
                    tribunal_name=tribunal_title,
                    tribunal_index=i
                )
        
        _tribunales_discovered = True
    except Exception as e:
        # If discovery fails, we'll just use the generic Tribunales scraper
        print(f"Warning: Could not discover individual tribunales: {e}")
        SCRAPERS["Tribunales"] = ScrapTribunales()
        _tribunales_discovered = True
    
    return SCRAPERS