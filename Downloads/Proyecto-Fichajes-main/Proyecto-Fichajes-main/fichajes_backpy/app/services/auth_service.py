from app.database.mongodb import usuarios_collection
from app.core.security import verify_password, create_access_token
from typing import Optional


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Autentica un usuario verificando sus credenciales.
    
    Args:
        username: Nombre de usuario
        password: Contraseña en texto plano
        
    Returns:
        Usuario si las credenciales son válidas, None en caso contrario
    """
    user = await usuarios_collection.find_one({
        "username": username,
        "activo": True
    })
    
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    return user


async def create_token_for_user(user: dict) -> str:
    """
    Crea un token JWT para un usuario.
    
    Args:
        user: Diccionario con los datos del usuario
        
    Returns:
        Token JWT como string
    """
    token_data = {
        "sub": user["username"],
        "role": user.get("rol", "user"),
        "user_id": str(user["_id"])
    }
    return create_access_token(token_data)
