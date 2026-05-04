from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class FichajeBase(BaseModel):
    """Esquema base de fichaje"""
    tipo: Literal["entrada", "salida"] = Field(..., description="Tipo de fichaje")


class FichajeCreate(FichajeBase):
    """Esquema para crear un fichaje"""
    pass


class FichajeResponse(BaseModel):
    """Esquema de respuesta de fichaje"""
    id: str
    user_id: str
    username: str
    nombre_completo: str
    tipo: str
    timestamp: datetime
    fecha: str
    hora: str
    dia_semana: str
    
    class Config:
        from_attributes = True


class HorasTrabajadasResponse(BaseModel):
    """Esquema para respuesta de horas trabajadas"""
    fecha: str
    horas: float
    entradas: int
    salidas: int
