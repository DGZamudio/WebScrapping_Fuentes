from typing import List, Optional
from pydantic import BaseModel

class RawDocModel(BaseModel):
    source   : str
    link     : str
    title    : str
    tipo     : str
    f_public : str