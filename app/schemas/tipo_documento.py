from pydantic import BaseModel, Field

class TipoDocumento(BaseModel):
    id: int
    nombre: str = Field(..., description="Nombre del tipo de documento")
    
    model_config = {
        "from_attributes": True
    } 