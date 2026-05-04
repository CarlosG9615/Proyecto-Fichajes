from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_token_for_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
async def login(credentials: LoginRequest):
    """
    Autentica un usuario y devuelve un token JWT.
    
    - **username**: Nombre de usuario
    - **password**: Contraseña
    """
    user = await authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token JWT
    token = await create_token_for_user(user)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "nombre_completo": user.get("nombre_completo"),
            "rol": user.get("rol", "user"),
            "departamento": user.get("departamento"),
            "email": user.get("email")
        }
    }


@router.post("/logout", summary="Cerrar sesión")
async def logout():
    """
    Cierra la sesión del usuario.
    Nota: En JWT el logout se maneja en el cliente eliminando el token.
    """
    return {"message": "Sesión cerrada correctamente"}
