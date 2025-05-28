from pydantic import BaseModel, Field
from typing import Union

class LovElemento(BaseModel):
    id: Union[str, int] = Field(None, description="ID del elemento")
    name: str = Field(None, description="Nombre del elemento")