from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from fichajes_backpy.app.services.usuario_service import obtener_usuario_por_username, actualizar_usuario
from fichajes_backpy.app.utils.dependencies import get_current_user, require_admin
from typing import Optional

router = APIRouter()


class VincularTelegramRequest(BaseModel):
    """Esquema para vincular Telegram ID"""
    telegram_id: int


class TelegramStatusResponse(BaseModel):
    """Respuesta del estado de Telegram"""
    telegram_vinculado: bool
    telegram_id: Optional[int] = None


@router.post("/vincular", summary="Vincular cuenta de Telegram")
async def vincular_telegram(
    data: VincularTelegramRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Vincula la cuenta de Telegram del usuario actual.
    El usuario debe proporcionar su Telegram ID.
    """
    # Actualizar el usuario con el telegram_id
    usuario_actualizado = await actualizar_usuario(
        str(current_user["_id"]),
        {"telegram_id": data.telegram_id}
    )
    
    if not usuario_actualizado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al vincular cuenta de Telegram"
        )
    
    return {
        "message": "Cuenta de Telegram vinculada correctamente",
        "telegram_id": data.telegram_id,
        "username": usuario_actualizado["username"]
    }


@router.delete("/desvincular", summary="Desvincular cuenta de Telegram")
async def desvincular_telegram(
    current_user: dict = Depends(get_current_user)
):
    """
    Desvincula la cuenta de Telegram del usuario actual.
    """
    usuario_actualizado = await actualizar_usuario(
        str(current_user["_id"]),
        {"telegram_id": None}
    )
    
    if not usuario_actualizado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al desvincular cuenta de Telegram"
        )
    
    return {
        "message": "Cuenta de Telegram desvinculada correctamente"
    }


@router.get("/estado", response_model=TelegramStatusResponse, summary="Estado de Telegram")
async def estado_telegram(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el estado de vinculación de Telegram del usuario actual.
    """
    telegram_id = current_user.get("telegram_id")
    
    return {
        "telegram_vinculado": telegram_id is not None,
        "telegram_id": telegram_id
    }


@router.post("/admin/vincular/{username}", summary="Vincular Telegram (Admin)")
async def admin_vincular_telegram(
    username: str,
    data: VincularTelegramRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Vincula una cuenta de Telegram a un usuario específico.
    Solo para administradores.
    """
    usuario = await obtener_usuario_por_username(username)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario_actualizado = await actualizar_usuario(
        str(usuario["_id"]),
        {"telegram_id": data.telegram_id}
    )
    
    return {
        "message": f"Telegram vinculado a {username}",
        "telegram_id": data.telegram_id,
        "username": username
    }


@router.post("/enviar-test", summary="Enviar mensaje de prueba")
async def enviar_mensaje_test(
    current_user: dict = Depends(get_current_user)
):
    """
    Envía un mensaje de prueba al Telegram vinculado del usuario.
    """
    telegram_id = current_user.get("telegram_id")
    
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes una cuenta de Telegram vinculada"
        )
    
    # Aquí se implementaría el envío real con el bot
    # Por ahora solo devuelve confirmación
    
    return {
        "message": "Mensaje de prueba enviado",
        "telegram_id": telegram_id,
        "texto": f"✅ Hola {current_user['nombre_completo']}, tu cuenta está vinculada correctamente!"
    }
