from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional


class FichajeBase(BaseModel):
    """Esquema base de fichaje"""
    tipo: Literal["entrada", "salida"] = Field(..., description="Tipo de fichaje")
    latitude: Optional[float] = Field(None, description="Latitud GPS")
    longitude: Optional[float] = Field(None, description="Longitud GPS")
    precision_gps_m: Optional[float] = Field(None, description="Precisión GPS en metros")


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
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    precision_gps_m: Optional[float] = None
    distancia_centro_km: Optional[float] = None
    dentro_radio_autorizado: Optional[bool] = None
    empresa_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True


class HorasTrabajadasResponse(BaseModel):
    """Esquema para respuesta de horas trabajadas"""
    fecha: str
    horas: float
    entradas: int
    salidas: int
