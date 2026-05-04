from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.services.usuario_service import (
    obtener_todos_usuarios,
    obtener_usuario_por_id,
    crear_usuario,
    actualizar_usuario,
    eliminar_usuario,
    obtener_usuario_por_username
)
from app.utils.dependencies import get_current_user, require_admin
from typing import List

router = APIRouter()


@router.get("/me", response_model=UsuarioResponse, summary="Obtener mi perfil")
async def obtener_mi_perfil(current_user: dict = Depends(get_current_user)):
    """Obtiene el perfil del usuario autenticado."""
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "nombre_completo": current_user.get("nombre_completo"),
        "departamento": current_user.get("departamento"),
        "email": current_user.get("email"),
        "rol": current_user.get("rol", "user"),
        "activo": current_user.get("activo", True),
        "telegram_id": current_user.get("telegram_id")
    }


@router.get("/", response_model=List[UsuarioResponse], summary="Listar usuarios (Admin)")
async def listar_usuarios(current_user: dict = Depends(require_admin)):
    """
    Lista todos los usuarios. Requiere permisos de administrador.
    """
    usuarios = await obtener_todos_usuarios()
    return [
        {
            "id": str(u["_id"]),
            "username": u["username"],
            "nombre_completo": u.get("nombre_completo"),
            "departamento": u.get("departamento"),
            "email": u.get("email"),
            "rol": u.get("rol", "user"),
            "activo": u.get("activo", True),
            "telegram_id": u.get("telegram_id")
        }
        for u in usuarios
    ]


@router.get("/{user_id}", response_model=UsuarioResponse, summary="Obtener usuario por ID (Admin)")
async def obtener_usuario(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Obtiene un usuario por su ID. Requiere permisos de administrador.
    """
    usuario = await obtener_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {
        "id": str(usuario["_id"]),
        "username": usuario["username"],
        "nombre_completo": usuario.get("nombre_completo"),
        "departamento": usuario.get("departamento"),
        "email": usuario.get("email"),
        "rol": usuario.get("rol", "user"),
        "activo": usuario.get("activo", True),
        "telegram_id": usuario.get("telegram_id")
    }


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED, summary="Crear usuario (Admin)")
async def crear_nuevo_usuario(
    usuario: UsuarioCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Crea un nuevo usuario. Requiere permisos de administrador.
    """
    # Verificar si el usuario ya existe
    usuario_existente = await obtener_usuario_por_username(usuario.username)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe"
        )
    
    # Crear usuario
    nuevo_usuario = await crear_usuario(usuario.dict())
    
    return {
        "id": str(nuevo_usuario["_id"]),
        "username": nuevo_usuario["username"],
        "nombre_completo": nuevo_usuario.get("nombre_completo"),
        "departamento": nuevo_usuario.get("departamento"),
        "email": nuevo_usuario.get("email"),
        "rol": nuevo_usuario.get("rol", "user"),
        "activo": nuevo_usuario.get("activo", True),
        "telegram_id": nuevo_usuario.get("telegram_id")
    }


@router.put("/{user_id}", response_model=UsuarioResponse, summary="Actualizar usuario (Admin)")
async def actualizar_usuario_endpoint(
    user_id: str,
    datos: UsuarioUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Actualiza un usuario existente. Requiere permisos de administrador.
    """
    usuario_actualizado = await actualizar_usuario(user_id, datos.dict(exclude_unset=True))
    
    if not usuario_actualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {
        "id": str(usuario_actualizado["_id"]),
        "username": usuario_actualizado["username"],
        "nombre_completo": usuario_actualizado.get("nombre_completo"),
        "departamento": usuario_actualizado.get("departamento"),
        "email": usuario_actualizado.get("email"),
        "rol": usuario_actualizado.get("rol", "user"),
        "activo": usuario_actualizado.get("activo", True),
        "telegram_id": usuario_actualizado.get("telegram_id")
    }


@router.delete("/{user_id}", summary="Desactivar usuario (Admin)")
async def desactivar_usuario(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Desactiva un usuario (soft delete). Requiere permisos de administrador.
    """
    success = await eliminar_usuario(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {"message": "Usuario desactivado correctamente"}
