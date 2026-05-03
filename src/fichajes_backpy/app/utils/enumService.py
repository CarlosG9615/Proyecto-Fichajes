from enum import Enum


class UserRole(str, Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    USER = "user"


class FichajeType(str, Enum):
    """Tipos de fichaje disponibles"""
    ENTRADA = "entrada"
    SALIDA = "salida"