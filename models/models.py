from typing import List, Optional
from pydantic import BaseModel

class RawDocModel(BaseModel):
    source     : str
    link       : dict
    title      : str
    tipo       : str
    f_public   : str
    f_providencia : Optional[str] = None  # fecha de la providencia/sentencia, distinta de f_public (fecha de publicación)
    seccion    : Optional[str] = None  # sección/sala/despacho dentro de la fuente (ej. SAMAI, Rama Judicial, CNDJ)
    seccion_en_carpeta : bool = True  # si False, `seccion` solo se reporta en Sheets, sin crear carpeta en Drive (ej. JEP)
    especialidad : Optional[str] = None  # especialidad jurídica (Civil/Penal/Laboral...), ej. Rama Judicial
    magistrado : Optional[str] = None  # magistrado ponente, ej. CNDJ
    detalle    : Optional[str] = None  # descripción completa cuando `tipo` es una categoría general
    save_path  : Optional[str] = None
    convert_to : Optional[str] = None  # e.g. "rtf" — converts after download via LibreOffice

    def __getitem__(self, key):
        return getattr(self, key)