from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    """Esquema base de usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    nombre_completo: str = Field(..., min_length=3, max_length=100)
    departamento: str = Field(..., max_length=100)
    email: EmailStr
    rol: str = Field(default="user", pattern="^(admin|user)$")
    activo: bool = True
    telegram_id: Optional[int] = None


class UsuarioCreate(UsuarioBase):
    """Esquema para crear un usuario (incluye password)"""
    password: str = Field(..., min_length=4)


class UsuarioUpdate(BaseModel):
    """Esquema para actualizar un usuario (campos opcionales)"""
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    rol: Optional[str] = Field(None, pattern="^(admin|user)$")
    activo: Optional[bool] = None
    telegram_id: Optional[int] = None
    password: Optional[str] = Field(None, min_length=4)


class UsuarioResponse(UsuarioBase):
    """Esquema de respuesta de usuario (sin password)"""
    id: str
    
    class Config:
        from_attributes = True


class UsuarioInDB(UsuarioBase):
    """Esquema de usuario en la base de datos"""
    password_hash: str
