from pydantic import BaseModel
from typing import List, TypeVar, Generic

T = TypeVar('T')

class PaginacionResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    skip: int
    limit: int