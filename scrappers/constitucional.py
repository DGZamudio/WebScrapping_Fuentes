from typing import List
import requests
from config.config import CORTE_CONSTITUCIONAL_DOWNLOAD_URL, CORTE_CONSTITUCIONAL_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapConstitucional(BaseScrapper):
    def __init__(self):
        self.source = "Corte Constitucional"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=1000) -> List[RawDocModel]:
        self.url = CORTE_CONSTITUCIONAL_URL(fini, ffin, q, limit)
        response = requests.get(self.url)

        results = response.json()
        data = results["data"]["hits"].get("hits", [])

        docs = []

        for item in data:
            raw = item["_source"]

            link = f"{CORTE_CONSTITUCIONAL_DOWNLOAD_URL}{raw['rutahtml'].replace('.htm', '.rtf')}"
            doc = RawDocModel(
                source= self.source,
                link= {"url":link, "method":"GET"},
                title= raw["prov_sentencia"],
                tipo= raw["prov_tipo"],
                f_public= raw["prov_f_public"],
                save_path=f"downloads/{self.source}/{raw['prov_f_public'].replace('-', '')}/{raw['prov_tipo']}/_(filename)_(extension)"
            )

            docs.append(doc)

        return docs