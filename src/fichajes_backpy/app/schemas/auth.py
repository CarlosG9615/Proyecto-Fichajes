from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Esquema para la solicitud de login"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Esquema para la respuesta del token JWT"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class TokenData(BaseModel):
    """Datos contenidos en el token JWT"""
    username: str
    role: str
    user_id: str
