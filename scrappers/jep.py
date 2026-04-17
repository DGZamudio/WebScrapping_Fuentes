from datetime import datetime, timedelta
import os
from typing import List
import requests
from config.config import JEP_DOWNLOAD_URL, JEP_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapJEP(BaseScrapper):
    def __init__(self):
        self.source = "JEP"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=10000) -> List[RawDocModel]:
        anio_inicial = fini[:4] # Extraer solo el año ya que estas se almacenan por año
        anio_final = ffin[:4]
        self.url = JEP_URL
        docs = []


        response = requests.get(self.url)
        
        if response.status_code != 200:
            raise Exception(f"Error al obtener datos de {self.source}: {response.status_code} - {response.text} el sitio pudo haber cambiado su estructura o el formato de respuesta, informare al equipo de desarrollo para actualizar el scraper.")
        
        try:
            results = response.json()
        except ValueError:
            raise Exception(
                f"La respuesta no es JSON válido. Contenido recibido:\n{response.text[:500]}"
            )
        
        data = results

        for item in data:
            fecha_p = item.get("fecha", 0)
            if fecha_p is None: fecha_p = 0
            
            if int(fecha_p) < int(anio_inicial) or int(fecha_p) > int(anio_final):
                continue #Salta al siguiente item si la fecha no está dentro del rango
            
            link = f"{JEP_DOWNLOAD_URL}{item.get('hipervinculo', '')}"
            
            
            radicado = item.get("radicado", "")
            asunto = item.get("asuntocaso", "")
            fecha_p = str(fecha_p)
            
            path = os.path.join(
                "downloads",
                self.source,
                f"{radicado}_{fecha_p}(extension)",
            )
            
            doc = RawDocModel(
                source= self.source,
                link= {"url":link, "method":"GET"},
                title= item["nombre"]+"-"+radicado,
                tipo= '',
                f_public= fecha_p,
                save_path=path
            )

            docs.append(doc)

        return docs