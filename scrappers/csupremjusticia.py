from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from config.config import CORTE_SUPREMA_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapCorteSuprema(BaseScrapper):
    def __init__(self):
        self.source = "Corte Suprema de justicia"
        self.url = CORTE_SUPREMA_URL

    def scrap(self, fini, ffin, q="", limit=1000):
        payload = {
            "query":"""query GetSearchResult {getSearchResult(
                            searchQuery: {
                                query: \"*\"
                                typeOfQuery: \"Tutelas\"
                                start: 0
                                isExact: false
                                magistrate: \"\"
                                year: \"\"
                                autoSentencia: \"\"
                                order: \"\"
                                roomTutelas: \"\"
                            }
                        ) {
                            numOfResults
                            searchResults {
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
                            }
                        }
                    }
                    """,
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(self.url, json=payload, headers=headers)

        response.raise_for_status()
        data = response.json()

        docs = []

        for item in data["data"]["getSearchResult"]["searchResults"]:
            doc = RawDocModel(
                tipo=item["typeOfDocument"] if "typeOfDocument" in item else "Desconocido",
                title=item["title"].strip(".")[-2].strip(),
                link=urljoin("https://consultaprovidenciasbk.cortesuprema.gov.co/", item["onlinePath"]),
                date=item["fechaCreacion"],
                source=self.source
            )
            docs.append(doc)

        return docs