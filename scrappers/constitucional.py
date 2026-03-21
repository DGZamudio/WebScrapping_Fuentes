from datetime import datetime, timedelta
import os
from typing import List
import requests
from config.config import CORTE_CONSTITUCIONAL_DOWNLOAD_URL, CORTE_CONSTITUCIONAL_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapConstitucional(BaseScrapper):
    def __init__(self):
        self.source = "Corte Constitucional"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=10000) -> List[RawDocModel]:
        fecha_local = datetime.strptime(fini, "%Y-%m-%d")
        fecha_final_global = datetime.strptime(ffin, "%Y-%m-%d")
        docs = []
        
        while fecha_local < datetime.strptime(ffin, "%Y-%m-%d"):
            fecha_inicial = fecha_local.strftime("%Y-%m-%d")
            fecha_final = min(fecha_local + timedelta(days=365), fecha_final_global)
            
            self.url = CORTE_CONSTITUCIONAL_URL(fecha_inicial, fecha_final.strftime("%Y-%m-%d"), q, limit)
            response = requests.get(self.url)
            
            if response.status_code != 200:
                raise Exception(f"Error al obtener datos de {self.source}: {response.status_code} - {response.text} el sitio pudo haber cambiado su estructura o el formato de respuesta, informare al equipo de desarrollo para actualizar el scraper.")
            
            try:
                results = response.json()
            except ValueError:
                raise Exception(
                    f"La respuesta no es JSON válido. Contenido recibido:\n{response.text[:500]}"
                )
            
            data = results["data"]["hits"].get("hits", [])

            for item in data:
                raw = item["_source"]
                
                link = f"{CORTE_CONSTITUCIONAL_DOWNLOAD_URL}{raw['rutahtml'].replace('.htm', '.rtf')}"
                tipo = raw['prov_tipo'] if raw['prov_tipo'] == "Auto" else ""
                
                fecha_p = raw["prov_f_public"] if raw.get("prov_f_public", None) else raw["prov_f_sentencia"]
                
                path = os.path.join(
                    "downloads",
                    self.source,
                    tipo,
                    fecha_p.replace('-', '')[:4],
                    "(filename)"
                )
                doc = RawDocModel(
                    source= self.source,
                    link= {"url":link, "method":"GET", "body": {"path": raw["prov_sentencia"]}},
                    title= raw["prov_sentencia"],
                    tipo= raw["prov_tipo"],
                    f_public= fecha_p,
                    save_path=path
                )

                docs.append(doc)
                
            fecha_local = fecha_final

        return docs