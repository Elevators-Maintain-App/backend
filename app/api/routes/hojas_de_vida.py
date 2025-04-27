# app/api/routes/hojas_de_vida.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.hojas_de_vida import HojaDeVidaCreate, HojaDeVidaUpdate, HojaDeVidaInDBBase
from app.services.hojas_de_vida import HojaDeVidaService

router = APIRouter(prefix="/hojas-vida", tags=["Hojas de Vida"])

@router.get("/", response_model=List[HojaDeVidaInDBBase])
async def get_hojas_de_vida(db: AsyncSession = Depends(get_db)):
    service = HojaDeVidaService(db)
    return await service.get_all()

@router.get("/{hoja_id}", response_model=HojaDeVidaInDBBase)
async def get_hoja_de_vida(hoja_id: UUID, db: AsyncSession = Depends(get_db)):
    service = HojaDeVidaService(db)
    return await service.get_by_id(hoja_id)

@router.post("/", response_model=HojaDeVidaInDBBase, status_code=status.HTTP_201_CREATED)
async def create_hoja_de_vida(hoja_in: HojaDeVidaCreate, db: AsyncSession = Depends(get_db)):
    service = HojaDeVidaService(db)
    return await service.create(hoja_in)

@router.put("/{hoja_id}", response_model=HojaDeVidaInDBBase)
async def update_hoja_de_vida(hoja_id: UUID, hoja_in: HojaDeVidaUpdate, db: AsyncSession = Depends(get_db)):
    service = HojaDeVidaService(db)
    return await service.update(hoja_id, hoja_in)

@router.delete("/{hoja_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hoja_de_vida(hoja_id: UUID, db: AsyncSession = Depends(get_db)):
    service = HojaDeVidaService(db)
    await service.delete(hoja_id)
