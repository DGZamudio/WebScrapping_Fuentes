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
        driver.get(self.url)
        docs = []

        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'búsqueda avanzada')]")
        ))

        botones_tribunales = driver.find_elements(By.CSS_SELECTOR, "#MainContent_CorporacionesTitulanDataList input[type='submit']")

        for i in range(1, len(botones_tribunales)):
            wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#MainContent_CorporacionesTitulanDataList input[type='submit']")
            ))

            botones_tribunales_local = driver.find_elements(By.CSS_SELECTOR, "#MainContent_CorporacionesTitulanDataList input[type='submit']")
            boton_local = botones_tribunales_local[i]
            tipo_tribunal = boton_local.get_attribute("title")
            driver.execute_script("arguments[0].click();", boton_local) # cambiar de tribunal

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

            stop = False

            while not stop:
                botones_ver_documentos = soup.find_all("a", id=lambda x: x and x.startswith("MainContent_ResultadoBusqueda1_TitulacionesRepeater_documentlink_"))

                for j, boton in enumerate(botones_ver_documentos):
                    try:
                        boton_ver_doc = driver.find_element(By.ID, f"MainContent_ResultadoBusqueda1_TitulacionesRepeater_documentlink_{j}")
                        url_doc = boton_ver_doc.get_attribute("onclick").split("'")[1] #Extraer URL del documento del atributo onclick

                        session = requests.Session()
                        for cookie in driver.get_cookies():
                            session.cookies.set(cookie['name'], cookie['value'])

                        response = session.get(url_doc)
                        
                        if response.status_code != 200:
                            raise Exception(f"Error al obtener datos de {self.source}: {response.status_code} - {response.text} el sitio pudo haber cambiado su estructura o el formato de respuesta, informare al equipo de desarrollo para actualizar el scraper.")
                        
                        soup_doc = BeautifulSoup(response.text, "html.parser")

                        # Verificar que los elementos esperados existan
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

                #Pasar de pagina
                boton_siguiente = driver.find_element(By.ID, f"MainContent_ResultadoBusqueda1_PaginaSiguienteLinkButton")
                driver.execute_script("arguments[0].scrollIntoView(true);", boton_siguiente)
                driver.execute_script("arguments[0].click();", boton_siguiente) #Clickear boton para ver documento

                #Esperar a que cargue la nueva pagina
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bg-body")))

                #Actualizar el soup con la nueva pagina
                soup = BeautifulSoup(driver.page_source, "html.parser")

            driver.get(self.url) # Volver a la seleccion de tribunal

        return docs