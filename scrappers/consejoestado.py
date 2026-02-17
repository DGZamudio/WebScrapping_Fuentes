from typing import List
from datetime import datetime, timedelta
import requests
from config.config import CONSEJO_ESTADO_URL, driver, wait
from models.models import RawDocModel
from scrappers.base import BaseScrapper
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class ScrapConsejoEstado(BaseScrapper):
    def __init__(self):
        self.source = "CE"
        self.url = None
        
    def scrap(self, fini, ffin, q="", limit=1000) -> List[RawDocModel]:
        self.url = CONSEJO_ESTADO_URL
        driver.get(self.url)

        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'búsqueda avanzada')]")
        ))

        btn_avanzada = driver.find_element(
            By.XPATH,
            "//button[contains(., 'búsqueda avanzada')]"
        )

        driver.execute_script("arguments[0].click();", btn_avanzada) #Clickear boton 1

        #Definir fecha inicial
        fini_dt = datetime.strptime(fini, "%Y-%m-%d") - timedelta(days=1)

        link = driver.find_element(By.ID, "MainContent_BuscarProvidenciasLinkButton")
        driver.execute_script("arguments[0].click();", link) #Clickear boton 2 (Busqueda)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bg-body")))  # Esperar a que la página cargue completamente

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        docs = []

        stop = False

        while not stop and len(docs) < limit:
            botones_ver_documentos = soup.find_all("a", id=lambda x: x and x.startswith("MainContent_ResultadoBusqueda1_TitulacionesRepeater_documentlink_"))

            for i, boton in enumerate(botones_ver_documentos):
                boton_ver_doc = driver.find_element(By.ID, f"MainContent_ResultadoBusqueda1_TitulacionesRepeater_documentlink_{i}")
                url_doc = boton_ver_doc.get_attribute("onclick").split("'")[1] #Extraer URL del documento del atributo onclick

                session = requests.Session()
                for cookie in driver.get_cookies():
                    session.cookies.set(cookie['name'], cookie['value'])

                response = session.get(url_doc)
                soup_doc = BeautifulSoup(response.text, "html.parser")

                link_descarga = soup_doc.find("a", id="ContentPlaceHolder1_VerProvidencia1_DescargarProvideciaLinkButton").get("href", '') #Extraer link de descarga
                fecha_str = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_LblFECHAPROV").text.split(",")[1].strip()
                fecha_dt = datetime.strptime(fecha_str, "%d de %B de %Y")

                if fecha_dt < fini_dt:
                    stop = True
                    break
                
                sala_desicion = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_InfoProceso1_LblSalaDecision").text.strip()
                proceso = soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_InfoProceso1_LblClaseProceso").text.strip()
                fecha = fecha_dt.strftime("%Y%m%d")

                doc = RawDocModel(
                    source=self.source,
                    link={"url":link_descarga, "method":"GET"},
                    title=soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_InfoProceso1_LblRadicado").text.strip(),
                    tipo=soup_doc.find("span", id="ContentPlaceHolder1_InfoProcesoProvidencia1_LblTIPOPROVIDENCIA").text.strip(),
                    f_public=fecha,
                    save_path=f"downloads/{self.source}/{fecha[:4]}/{sala_desicion}/{proceso}/_(filename)_{''.join(palabra[0].upper() for palabra in proceso.split())}_(extension)"
                )
                docs.append(doc)

            #Pasar de pagina
            boton_siguiente = driver.find_element(By.ID, f"MainContent_ResultadoBusqueda1_PaginaSiguienteLinkButton")
            driver.execute_script("arguments[0].scrollIntoView(true);", boton_siguiente)
            driver.execute_script("arguments[0].click();", boton_siguiente) #Clickear boton para ver documento

            #Esperar a que cargue la nueva pagina
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bg-body")))

            #Actualizar el soup con la nueva pagina
            soup = BeautifulSoup(driver.page_source, "html.parser")

        driver.quit()

        return docs