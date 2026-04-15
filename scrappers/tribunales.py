import re
from typing import List
from datetime import datetime, timedelta
import requests
from config.config import CONSEJO_ESTADO_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper
from bs4 import BeautifulSoup

from utils import get_asp_data, parse_ajax_response


class ScrapTribunales(BaseScrapper):
    def __init__(self, tribunal_name=None, tribunal_index=None):
        """
        Initialize ScrapTribunales.
        
        Args:
            tribunal_name: Name of specific tribunal to scrap (e.g., "Tribunal Superior")
            tribunal_index: Index of tribunal button to scrap (1-based, excluding index 0)
                           If None, scraps all tribunales
        """
        self.tribunal_name = tribunal_name
        self.tribunal_index = tribunal_index
        self.source = tribunal_name if tribunal_name else "Tribunales"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=1000) -> List[RawDocModel]:
        self.url = CONSEJO_ESTADO_URL
        session = requests.Session()
        docs = []

        # GET inicial para obtener cookies y VS base
        res = session.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-MicrosoftAjax": "Delta=true",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "Referer": self.url
        }

        botones_tribunales = soup.select("#MainContent_CorporacionesTitulanDataList input[type='submit']")

        # Determinar que tribunales scrapear según los parámetros
        indices_to_scrap = [self.tribunal_index] if self.tribunal_index is not None else range(1, len(botones_tribunales))

        for i in indices_to_scrap:
            asp_data = get_asp_data(soup)
            boton_local = botones_tribunales[i]
            name_tribunal = boton_local.get("name")
            tipo_tribunal = boton_local.get("title")
            value_tribunal = boton_local.get("value")
            print(tipo_tribunal)

            data = {
                **asp_data,
                "__ASYNCPOST": "true",
                "ctl00$MainContent$ScriptManager1": f"ctl00$MainContent$PanelUpdate|{name_tribunal}",
                name_tribunal: value_tribunal
            }

            # POST 1: Seleccionar Tribunal
            res2 = session.post(self.url, data=data, headers=headers)
            html_update, asp_data = parse_ajax_response(res2.text)
            localsoup = BeautifulSoup(html_update, "html.parser")

            # POST 2: Apartado de filtros y ver resultados

            # Settear fecha inicio y fin
            boton_fechas = localsoup.find("a", id="MainContent_OQueContengaFechaLinkButton")
            postback_str = boton_fechas.get("href")
            valores = re.findall(r'["\'](.*?)["\']', postback_str)
            data = {
                **asp_data,
                "__ASYNCPOST": "true",
                "__EVENTTARGET": valores[0],
                "__EVENTARGUMENT": valores[1] if len(valores) > 1 else "",
                "ctl00$MainContent$ScriptManager1": "ctl00$MainContent$PanelUpdate|ctl00$MainContent$OQueContengaFechaLinkButton",
                "ctl00$MainContent$FechaDesdeTextBox": fini,
                "ctl00$MainContent$FechaHastaTextBox": ffin
            }
            resf = session.post(self.url, data=data, headers=headers)
            html_update, asp_data = parse_ajax_response(resf.text)
            localsoup = BeautifulSoup(html_update, "html.parser")

            # Buscar botón de "Ver resultados"
            boton_busqueda = localsoup.find("a", id="MainContent_BuscarProvidenciasLinkButton")
            if not boton_busqueda: continue
            
            postback_str = boton_busqueda.get("href")
            valores = re.findall(r"'(.*?)'", postback_str)
            
            data = {
                **asp_data,
                "__ASYNCPOST": "true",
                "__EVENTTARGET": valores[0],
                "__EVENTARGUMENT": valores[1] if len(valores) > 1 else "",
                "ctl00$MainContent$ScriptManager1": "ctl00$MainContent$PanelUpdate|MainContent_BuscarProvidenciasLinkButton"
            }
            
            # Clic en "Ver resultados"
            res3 = session.post(self.url, data=data, headers=headers)
            html_update, asp_data = parse_ajax_response(res3.text)
            localsoup = BeautifulSoup(html_update, "html.parser")

            fini_dt = datetime.strptime(fini, "%Y-%m-%d") - timedelta(days=1)
            stop = False

            while not stop:
                # Buscar enlaces de documentos en la tabla de resultados
                botones_ver_documentos = localsoup.find_all("a", id=re.compile(r"MainContent_ResultadoBusqueda1_TitulacionesRepeater_documentlink_"))

                for j, boton in enumerate(botones_ver_documentos):
                    try:
                        # Extraer URL del popup (onclick)
                        url_doc_rel = boton.get("onclick").split("'")[1]
                        url_doc = f"https://www.consejodeestado.gov.co{url_doc_rel}" if url_doc_rel.startswith("/") else url_doc_rel

                        # GET al detalle del documento
                        res_doc = session.get(url_doc)
                        soup_doc = BeautifulSoup(res_doc.text, "html.parser")

                        download_elem = soup_doc.find("a", id="ContentPlaceHolder1_VerProvidencia1_DescargarProvideciaLinkButton")
                        if not download_elem:
                            raise Exception(f"Error al obtener datos de {self.source}: No se encontró el elemento de descarga. El sitio pudo haber cambiado su estructura o el formato de respuesta, informare al equipo de desarrollo para actualizar el scraper.")
                        
                        link_descarga = download_elem.get("href", '')
                        
                        fecha_elem = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_LblFECHAPROV")
                        if not fecha_elem:
                            raise Exception(f"Error al obtener datos de {self.source}: No se encontró el elemento de fecha. El sitio pudo haber cambiado su estructura o el formato de respuesta, informare al equipo de desarrollo para actualizar el scraper.")
                        
                        fecha_str = fecha_elem.text.split(",")[1].strip()
                        fecha_dt = datetime.strptime(fecha_str, "%d de %B de %Y")

                        if fecha_dt < fini_dt:
                            stop = True
                            break
                        
                        sala_desicion = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_InfoProceso1_LblSalaDecision").text.strip()
                        proceso = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_InfoProceso1_LblClaseProceso").text.strip()
                        fecha = fecha_dt.strftime("%Y%m%d")
                        radicado = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_InfoProceso1_LblRadicado").text.strip()
                        radicado_formateado = f"{radicado[:5]}-{radicado[5:7]}-{radicado[7:9]}-{radicado[9:12]}-{radicado[12:16]}-{radicado[16:21]}-{radicado[21:]}"
                        interno = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_InfoProceso1_LblInterno").text.strip()

                        doc = RawDocModel(
                            source=self.source,
                            link={"url":link_descarga, "method":"GET", "body": {"path": radicado}},
                            title=radicado,
                            tipo=soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_LblTIPOPROVIDENCIA").text.strip(),
                            f_public=fecha,
                            save_path=f"downloads/{self.source}/{tipo_tribunal}/{fecha[:5]}/{sala_desicion}/{proceso}/{radicado_formateado}{'('+interno+')' if interno else None}(extension)"
                        )
                        docs.append(doc)
                    except Exception as e:
                        print(f"Error procesando documento {j}: {str(e)}")
                        continue

                if stop: break

                btn_sig = localsoup.find("a", id="MainContent_ResultadoBusqueda1_PaginaSiguienteLinkButton")
                if not btn_sig: break # No hay más páginas

                postback_sig = btn_sig.get("href")
                v_sig = re.findall(r"'(.*?)'", postback_sig)
                
                data_pag = {
                    **asp_data,
                    "__ASYNCPOST": "true",
                    "__EVENTTARGET": v_sig[0],
                    "__EVENTARGUMENT": v_sig[1] if len(v_sig) > 1 else "",
                    "ctl00$MainContent$ScriptManager1": f"ctl00$MainContent$PanelUpdate|{v_sig[0]}"
                }

                res_pag = session.post(self.url, data=data_pag, headers=headers)
                html_update, asp_data = parse_ajax_response(res_pag.text)
                localsoup = BeautifulSoup(html_update, "html.parser")
        
            # Refrescar la página principal para el siguiente tribunal
            res = session.get(self.url)
            soup = BeautifulSoup(res.text, "html.parser")
            botones_tribunales = soup.select("#MainContent_CorporacionesTitulanDataList input[type='submit']")

        return docs