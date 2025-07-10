#app/schemas/comunes/shared.py

from pydantic import BaseModel
from datetime import date

class DateRangeInput(BaseModel):
    fecha_inicio: date
    fecha_fin: date
