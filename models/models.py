from typing import List, Optional
from pydantic import BaseModel

class RawDocModel(BaseModel):
    source    : str
    link      : dict
    title     : str
    tipo      : str
    f_public  : str
    save_path : Optional[str] = None

    def __getitem__(self, key):
        return getattr(self, key)