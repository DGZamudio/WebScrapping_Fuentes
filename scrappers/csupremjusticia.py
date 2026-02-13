from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from lxml import etree
from config.config import CORTE_SUPREMA_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapCorteSuprema(BaseScrapper):
    def __init__(self):
        self.source = "Corte Suprema de justicia"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        })
        
    def _get_viewstate(self):
        r = self.session.get(CORTE_SUPREMA_URL, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")
        viewstate = soup.find("input", {"name": "javax.faces.ViewState"})

        if not viewstate:
            raise RuntimeError("No se encontró javax.faces.ViewState")

        return viewstate["value"]
    
    def _post_search(self, viewstate):
        headers = {
            "Faces-Request": "partial/ajax",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": CORTE_SUPREMA_URL,
        }

        payload = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "searchForm:searchButton",
            "javax.faces.partial.execute": "@all",
            "javax.faces.partial.render": "resultForm:jurisTable",
            "searchForm:searchButton": "searchForm:searchButton",
            "searchForm": "searchForm",
            "searchForm:tutelaselect": "TODO",
            "javax.faces.ViewState": viewstate,
        }

        r = self.session.post(CORTE_SUPREMA_URL, data=payload, headers=headers, timeout=600)
        r.raise_for_status()
        return r.content

    def _extract_html_fragment(self, xml_bytes):
        root = etree.fromstring(xml_bytes)

        for update in root.xpath("//update"):
            if "jurisTable" in update.attrib.get("id", ""):
                return update.text

        raise RuntimeError("No se encontró fragmento HTML en la respuesta JSF")

    def _extract_docs(self, html_fragment):
        soup = BeautifulSoup(html_fragment, "lxml")

        docs = []
        for a in soup.select("a[href]"):
            link 
            doc = RawDocModel(
                source= self.source,
                link= link,
                title= raw["prov_sentencia"],
                tipo= raw["prov_tipo"],
                f_public= raw["prov_f_public"]
            )
            href = a["href"]
            if any(href.lower().endswith(ext) for ext in (".pdf", ".doc", ".docx")):
                docs.append(urljoin(CORTE_SUPREMA_URL, href))

        return list(set(docs))

    def scrap(self, fini, ffin, q="", limit=1000):
        viewstate = self._get_viewstate()
        xml_response = self._post_search(viewstate)
        print("El pepe: ", self._post_search(viewstate))
        html_fragment = self._extract_html_fragment(xml_response)
        docs = self._extract_docs(html_fragment)

        return docs