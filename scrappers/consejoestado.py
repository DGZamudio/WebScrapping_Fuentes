from typing import List
import requests
from config.config import CONSEJO_ESTADO_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper
from bs4 import BeautifulSoup


class ScrapConsejoEstado(BaseScrapper):
    def __init__(self):
        self.source = "Consejo de estado"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=1000) -> List[RawDocModel]:
        session = requests.Session()
        self.url = CONSEJO_ESTADO_URL
        
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")

        viewstate = soup.find("input", {"id": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"id": "__EVENTVALIDATION"})["value"]
        
        payload = {
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$MainContent$txtFechaDesde": "01/01/2024",
            "ctl00$MainContent$txtFechaHasta": "31/12/2024",
            "ctl00$MainContent$btnBuscar": "Buscar"
        }
        
        r2 = session.post(self.url, data=payload)
        soup2 = BeautifulSoup(r2.text, "html.parser")

        links = soup2.select("a[href$='.pdf']")

        docs = []

        for item in data:
            raw = item["_source"]

            link = f"{CORTE_CONSTITUCIONAL_DOWNLOAD_URL}{raw['rutahtml'].replace('.htm', '.rtf')}"
            doc = RawDocModel(
                source= self.source,
                link= link,
                title= raw["prov_sentencia"],
                tipo= raw["prov_tipo"],
                f_public= raw["prov_f_public"]
            )

            docs.append(doc)

        return docs