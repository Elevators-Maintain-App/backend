from pydantic import BaseModel, Field, UUID4
from typing import Union

class LovElemento(BaseModel):
    id: Union[str, int, UUID4] = Field(None, description="ID del elemento")
    name: str = Field(None, description="Nombre del elemento")