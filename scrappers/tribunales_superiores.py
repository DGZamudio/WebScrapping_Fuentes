import re
from typing import List
from bs4 import BeautifulSoup, Comment
import requests
from config.config import TRIBUNALES_SUPERIORES_URL
from models.models import RawDocModel
from scrappers.base import BaseScrapper

BASE_DOMAIN = "https://publicacionesprocesales.ramajudicial.gov.co"
_PORTLET = "co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE"
_INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*]')
_TIPOS_PERMITIDOS = {
    "Notificaciones por Estados",
    "Acciones de Tutela",
    "Sentencias",
    "Autos masivo",
}


class ScrapTribunalesSuperiores(BaseScrapper):
    def __init__(self):
        self.source = "Tribunales Superiores"
        self.url = TRIBUNALES_SUPERIORES_URL
        self._instance_id = None

    def _get_instance_id(self, session, headers):
        html = session.get(self.url, headers=headers).text
        match = re.search(rf'p_p_id_{_PORTLET}_([A-Za-z0-9]+)_', html)
        if not match:
            raise Exception(
                "No se encontró instance_id. El sitio puede haber cambiado su estructura."
            )
        return match.group(1)

    def _p(self, key):
        return f"_{_PORTLET}_{self._instance_id}_{key}"

    def _get_detail_files(self, session, headers, detail_url):
        for attempt in range(3):
            try:
                resp = session.get(detail_url, headers=headers, timeout=60)
                if resp.status_code < 500:
                    break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    raise
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        files = []
        table = soup.find("table", id=re.compile(r"tabla-docs"))
        if not table:
            return files
        tbody = table.find("tbody")
        if not tbody:
            return files

        for row in tbody.find_all("tr"):
            a = row.find("a")
            if not a:
                continue
            filename = a.text.strip()
            href = a.get("href", "")
            if not href:
                continue
            download_url = (BASE_DOMAIN + href) if href.startswith("/") else href
            uuid_match = re.search(r'uuid=([^&]+)', href)
            file_uuid = uuid_match.group(1) if uuid_match else filename
            files.append((filename, download_url, file_uuid))

        return files

    def scrap(self, fini, ffin, q="", limit=10, stop_event=None, on_progress=None) -> List[RawDocModel]:
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}

        self._instance_id = self._get_instance_id(session, headers)
        p_p_id = f"{_PORTLET}_{self._instance_id}"

        docs = []
        num_pag = 1
        max_pages = None

        while True:
            params = {
                "p_p_id": p_p_id,
                "p_p_lifecycle": 0,
                "p_p_state": "normal",
                "p_p_mode": "view",
                self._p("action"): "busqueda",
                self._p("idEntidad"): 22,
                self._p("fechaInicio"): fini,
                self._p("fechaFin"): ffin,
                self._p("verTotales"): "true",
                self._p("delta"): limit,
                self._p("resetCur"): "false",
                self._p("cur"): num_pag,
            }

            for attempt in range(3):
                try:
                    response = session.get(self.url, params=params, headers=headers, timeout=60)
                    if response.status_code < 500:
                        break
                except requests.exceptions.Timeout:
                    if attempt == 2:
                        raise
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            if max_pages is None:
                page_span = soup.find("span", string=re.compile(r"Página 1 de \d+"))
                if page_span:
                    m = re.search(r"Página 1 de (\d+)", page_span.text)
                    max_pages = int(m.group(1)) if m else 1
                else:
                    max_pages = 1

            tbody = soup.find("tbody", {"class": "table-data"})
            if not tbody:
                break

            rows = tbody.find_all("tr")
            if not rows:
                break

            for row in rows:
                if stop_event is not None and stop_event.is_set():
                    return docs

                try:
                    title_tag = row.find("div", class_="titulo-publicacion")
                    if not title_tag:
                        continue
                    a_tag = title_tag.find("a")
                    if not a_tag:
                        continue
                    title = a_tag.text.strip()

                    fecha_p_tag = row.find("p", class_="publish-date")
                    if not fecha_p_tag:
                        continue
                    fecha_p = fecha_p_tag.text.split(":")[-1].strip()

                    categorias = {}
                    for span in row.find_all("span", class_="categoria-ep"):
                        text = span.text.strip()
                        if ":" in text:
                            k, v = text.split(":", 1)
                            categorias[k.strip()] = v.strip()

                    tipo         = categorias.get("Tipo de publicación", "")
                    if tipo not in _TIPOS_PERMITIDOS:
                        continue

                    especialidad = categorias.get("Especialidad", "sin-especialidad")
                    despacho_raw = categorias.get("Despacho", "")
                    despacho_dir = _INVALID_PATH_CHARS.sub("-", despacho_raw)[:60]
                    tipo_dir     = _INVALID_PATH_CHARS.sub("-", tipo)

                    detail_url = a_tag.get("href", "")
                    if not detail_url:
                        continue

                    if on_progress:
                        on_progress(f"[Tribunales Superiores] Leyendo detalle: {title}")

                    archivos = self._get_detail_files(session, headers, detail_url)
                    if not archivos:
                        continue

                    for filename, download_url, file_uuid in archivos:
                        name_no_ext = (filename.rsplit(".", 1)[0] if "." in filename else filename).strip()
                        doc_name = _INVALID_PATH_CHARS.sub("-", name_no_ext)

                        save_path = (
                            f"downloads/{self.source}/{tipo_dir}"
                            f"/{especialidad}/{despacho_dir}/{fecha_p}/{doc_name}(extension)"
                        )

                        doc = RawDocModel(
                            source=self.source,
                            link={"url": download_url, "method": "GET", "body": {"path": file_uuid}},
                            title=name_no_ext,
                            tipo=tipo,
                            f_public=fecha_p,
                            save_path=save_path,
                            convert_to="rtf",
                        )
                        docs.append(doc)

                except Exception as e:
                    print(f"Error procesando fila: {e}")
                    continue

            if num_pag >= max_pages:
                break
            num_pag += 1

        return docs
