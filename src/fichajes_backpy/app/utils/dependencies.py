from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from fichajes_backpy.app.core.security import verify_token
from fichajes_backpy.app.database.mongodb import usuarios_collection

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Obtiene el usuario actual desde el token JWT.
    
    Args:
        credentials: Credenciales HTTP Bearer
        
    Returns:
        Diccionario con los datos del usuario
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    try:
        payload = verify_token(credentials.credentials)
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no se encontró el usuario",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await usuarios_collection.find_one({"username": username, "activo": True})
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Verifica que el usuario actual sea administrador.
    
    Args:
        current_user: Usuario actual obtenido del token
        
    Returns:
        Diccionario con los datos del usuario si es admin
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if current_user.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    return current_user
