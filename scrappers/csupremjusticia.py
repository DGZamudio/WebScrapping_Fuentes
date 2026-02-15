from typing import List
from urllib.parse import urljoin
import requests
from config.config import CORTE_SUPREMA_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapCorteSuprema(BaseScrapper):
    def __init__(self):
        self.source = "CSJ"
        self.url = CORTE_SUPREMA_URL
        self.tipos = {"Tutela": "", "Laboral": "SCL", "Civil": "", "Penal": "SCP"}

    def scrap(self, fini, ffin, q="", limit=1000):
        docs = []
                    
        for tipo in self.tipos:
            stop = False
            start = 0
            while not stop:
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

                for item in data["data"]["getSearchResult"]["searchResults"]:
                    if item["fechaCreacion"] < fini or item["fechaCreacion"] > ffin:
                        stop = True
                        break
                    
                    anio = item["fechaCreacion"].replace('-', '')[:4]
                    
                    doc = RawDocModel(
                        tipo=item["typeOfDocument"] if "typeOfDocument" in item else "Desconocido",
                        title=item["title"].strip(".")[-2].strip(),
                        link=urljoin("https://consultaprovidenciasbk.cortesuprema.gov.co/", item["onlinePath"]),
                        f_public=item["fechaCreacion"].replace('-', ''),
                        source=self.source,
                        save_path=f"downloads/{self.source}/{item['fechaCreacion']}/CSJ_{self.tipos[tipo]}_(filename)_{anio}(extension)"
                    )
                    docs.append(doc)
                    
                start += 10
        return docs