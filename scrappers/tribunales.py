from typing import List
from datetime import datetime, timedelta
import requests
from config.config import CONSEJO_ESTADO_URL, driver, wait
from models.models import RawDocModel
from scrappers.base import BaseScrapper
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class ScrapTribunales(BaseScrapper):
    def __init__(self):
        self.source = "Tribunales"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=1000) -> List[RawDocModel]:
        self.url = CONSEJO_ESTADO_URL
        session = requests.Session()

        res = session.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")

        botones_tribunales= soup.select("#MainContent_CorporacionesTitulanDataList input[type='submit']")

        viewstate = soup.select_one("input[name='__VIEWSTATE']")["value"]
        eventvalidation = soup.select_one("input[name='__EVENTVALIDATION']")["value"]

        for i in range(1, len(botones_tribunales)):
            data = {
                "__VIEWSTATE": viewstate,
                "__EVENTVALIDATION": eventvalidation, 
            } # Data para pagina asp.net
            
            boton_local = botones_tribunales[i] # Seleccionar boton
            tipo_tribunal = boton_local.get("title")
            value_tribunal = boton_local.get("value")
            name_tribunal = boton_local.get("name")
            data[name_tribunal] = value_tribunal # Cambiar de boton

            res2 = session.post(self.url, data=data)


        docs = []

        return docs