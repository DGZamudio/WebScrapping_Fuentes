from datetime import datetime, timedelta
import os
import re
from typing import List
from bs4 import BeautifulSoup
import requests
from config.config import TRIBUNALES_SUPERIORES_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper


class ScrapTribunalesSuperiores(BaseScrapper):
    def __init__(self):
        self.source = "Tribunales Superiores"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=1000) -> List[RawDocModel]:
        self.url = TRIBUNALES_SUPERIORES_URL
        docs = []
        num_pag = 1
        max_pages = 10
        instance_id = None

        html = requests.get(self.url).text

        # Extraer id de navegacion de los tribunales superiores
        match = re.search(
            r'p_p_id_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_([A-Za-z0-9]+)_',
            html
        )
        
        if match:
            instance_id = match.group(1)
            print(instance_id)

        while num_pag <= max_pages:
            # Parametros de busqueda
            params = {
                "p_p_id": f"co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}",
                "p_p_lifecycle": 0,
                "p_p_state": "normal",
                "p_p_mode": "view",
                
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_action": "busqueda",
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_idEntidad": 22, # Numero de id de los tribunales superiores
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_fechaInicio": fini,
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_fechaFin": ffin,
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_verTotales": "true",
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_delta": limit,
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_resetCur": "false",
                f"_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_{instance_id}_cur": num_pag
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            
            response = requests.get(self.url, params=params, headers=headers) # Hacer peticion
            soup = BeautifulSoup(response.text, "html.parser")
            
            if num_pag == 1:
                page_info = soup.find("span", string=lambda s: s and re.search(r"Página 1 de (\d+)", s))
                if page_info:
                    match = re.search(r"Página 1 de (\d+)", page_info.text)
                    max_pages = int(match.group(1)) if match else 10  # Captura el digito y lo convierte a int
                else:
                    max_pages = 10

            tbody = soup.find("tbody", {"class": "table-data"}) # Encontrar el contenedor de la tabla
            
            if tbody:
                rows = tbody.find_all("tr")  # Obtener todas las filas de la tabla
                
                for row in rows:
                    try:
                        # Extraer información de cada celda <td> dentro de la fila
                        cells = row.find_all("td")
                        
                        if len(cells) > 0:
                            # extraer link del primer celda que tenga un <a>
                            link_tag = row.find("a", href=True)
                            link = link_tag.get("href") if link_tag else None
                            fecha_p = cells[0].find("p", {"class": "publish-date"}).text.split(":")[1].strip() if cells[0].find("p", {"class": "publish-date"}) else "N/A"
                            

                            # Si tienes link, visitar la página para obtener más detalles
                            if link:
                                try:
                                    doc_soup = BeautifulSoup(requests.get(link).text, "html.parser")
                                    title = doc_soup.find("h2").text.strip() if doc_soup.find("h2") else "N/A"
                                    
                                    # Buscar Despacho en los spans
                                    tipo_tribunal = "N/A"
                                    for span in doc_soup.find_all("span", {"class": "categoria-ep"}):
                                        if "Despacho:" in span.text:
                                            tipo_tribunal = span.text.strip()
                                            break
                                    
                                    print(f"Título: {title}")
                                    print(f"Tipo Tribunal: {tipo_tribunal}")
                                    print(f"Fecha Publicación: {fecha_p}")
                                except Exception as e:
                                    print(f"Error al procesar link: {e}")
                    except Exception as e:
                        print(f"Error procesando fila: {e}")
            
            # path = os.path.join(
            #     "downloads",
            #     self.source,
            #     fecha_p,
            #     f"(filename)-{radicado}"
            # )
            
            # doc = RawDocModel(
            #     source= self.source,
            #     link= {"url":link, "method":"GET"},
            #     title= item["nombre"]+"-"+radicado,
            #     tipo= '',
            #     f_public= fecha_p,
            #     save_path=path
            # )

            # docs.append(doc)
            num_pag += 1

        return docs