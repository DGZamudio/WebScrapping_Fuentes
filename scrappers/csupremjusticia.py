from typing import List
from urllib.parse import urljoin
from datetime import datetime
import requests
from config.config import CORTE_SUPREMA_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapCorteSuprema(BaseScrapper):
    def __init__(self):
        self.source = "CSJ"
        self.url = CORTE_SUPREMA_URL
        self.tipos = {"Tutelas": "SCT", "Laboral": "SCL", "Civil": "SCC", "Penal": "SCP"}

    def scrap(self, fini, ffin, q="", limit=1000):
        docs = []
                    
        for tipo in self.tipos:
            stop = False
            start = 0
            while not stop:
                try:
                    payload = {
                        "query": """query GetSearchResult {{
                            getSearchResult(
                                searchQuery: {{
                                    query: "*"
                                    typeOfQuery: "{}"
                                    start: {}
                                    isExact: false
                                    magistrate: ""
                                    year: ""
                                    autoSentencia: ""
                                    order: "NEW_FIRST"
                                    roomTutelas: ""
                                }}
                            ) {{
                                numOfResults
                                searchResults {{
                                    typeOfDocument
                                    aplicationName
                                    fiveParaphraseResult
                                    title
                                    id
                                    onlinePath
                                    doctor
                                    fechaCreacion
                                    ano
                                    autoSentencia
                                    leyesOArticulos
                                }}
                            }}
                        }}
                        """.format(tipo, start),
                    }
                    headers = {
                        'Content-Type': 'application/json'
                    }

                    response = requests.post(self.url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    search_results = data.get("data", {}).get("getSearchResult", {}).get("searchResults", [])
                    
                    # Stop if no results returned
                    if not search_results:
                        stop = True
                        break

                    for item in search_results:
                        if item["fechaCreacion"] < fini or item["fechaCreacion"] > ffin:
                            stop = True
                            break
                        
                        anio = item["fechaCreacion"].replace('-', '')[:4]
                        fecha_obj = datetime.fromisoformat(item["fechaCreacion"].replace('Z', '+00:00'))
                        fecha = fecha_obj.strftime("%Y%m%d")
                        
                        doc = RawDocModel(
                            tipo=item.get("typeOfDocument") or "Desconocido",
                            title=item["title"].split(".")[-2].strip(),
                            link={"url":"https://consultaprovidenciasbk.cortesuprema.gov.co/downloadFile/", "body":{"path": item["onlinePath"]}, "method":"POST"},
                            f_public=fecha,
                            source=self.source,
                            save_path=f"downloads/{self.source}/{fecha}/CSJ_{self.tipos[tipo]}_(filename)_{anio}(extension)"
                        )
                        docs.append(doc)
                        
                    start += 10
                
                except KeyError as e:
                    print(f"Error: Missing expected field {e} in response for tipo '{tipo}'")
                    stop = True
                except Exception as e:
                    print(f"Error scraping tipo '{tipo}': {str(e)}")
                    stop = True
                    
        return docs