import re
from typing import List
from datetime import datetime, timedelta
import requests
from config.config import CONSEJO_ESTADO_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper
from bs4 import BeautifulSoup

from utils import get_asp_data, parse_ajax_response


class ScrapConsejoEstado(BaseScrapper):
    def __init__(self):
        self.source = "CE"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=1000, stop_event=None, on_progress=None) -> List[RawDocModel]:
        self.url = CONSEJO_ESTADO_URL
        session = requests.Session()
        docs = []
        
        # GET inicial para obtener cookies y VS base
        res = session.get(self.url)
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-MicrosoftAjax": "Delta=true",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "Referer": self.url
        }
        
        # Primera respuesta es HTML completo, no AJAX
        localsoup = BeautifulSoup(res.text, "html.parser")
        asp_data = get_asp_data(localsoup)
        
        # Setear fechas
        boton_fechas = localsoup.find("a", id="MainContent_OQueContengaFechaLinkButton")
        if not boton_fechas:
            raise Exception(f"Error: No se encontró el botón de fechas. La estructura del sitio puede haber cambiado.")
        
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
        
        # Boton de búsqueda
        boton_busqueda = localsoup.find("a", id="MainContent_BuscarProvidenciasLinkButton")
        if not boton_busqueda:
            raise Exception(f"Error: No se encontró el botón de búsqueda. Verificar respuesta AJAX.")
        
        postback_str = boton_busqueda.get("href")
        valores = re.findall(r"'(.*?)'", postback_str)
        
        data = {
            **asp_data,
            "__ASYNCPOST": "true",
            "__EVENTTARGET": valores[0],
            "__EVENTARGUMENT": valores[1] if len(valores) > 1 else "",
            "ctl00$MainContent$ScriptManager1": "ctl00$MainContent$PanelUpdate|MainContent_BuscarProvidenciasLinkButton",
            "ctl00$MainContent$FechaDesdeTextBox": fini,
            "ctl00$MainContent$FechaHastaTextBox": ffin
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
                        print(soup_doc.prettify())
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
                        save_path=f"downloads/{self.source}/{fecha[:5]}/{sala_desicion}/{proceso}/{radicado_formateado}{'('+interno+')' if interno else None}(extension)"
                    )
                    print(f"Documento procesado: {doc.title} - Fecha: {doc.f_public}")
                    docs.append(doc)
                except Exception as e:
                    print(f"Error procesando documento {j}: {str(e)}")
                    continue

            if stop: break

            btn_sig = localsoup.find("a", id="MainContent_ResultadoBusqueda1_PaginaSiguienteLinkButton")
            if not btn_sig: 
                break # No hay más páginas

            postback_sig = btn_sig.get("href")
            if not postback_sig:
                break
            
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

        return docs