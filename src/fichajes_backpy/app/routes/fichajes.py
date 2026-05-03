from fastapi import APIRouter, Depends, HTTPException, status, Query
from fichajes_backpy.app.schemas.fichaje import FichajeCreate, FichajeResponse, HorasTrabajadasResponse
from fichajes_backpy.app.services.fichaje_service import (
    crear_fichaje,
    obtener_fichajes_usuario,
    calcular_horas_trabajadas,
    obtener_estadisticas_usuario,
    obtener_fichajes_por_fecha
)
from fichajes_backpy.app.utils.dependencies import get_current_user
from typing import List
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=FichajeResponse, status_code=status.HTTP_201_CREATED, summary="Registrar fichaje")
async def registrar_fichaje(
    fichaje: FichajeCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Registra un nuevo fichaje (entrada o salida) para el usuario autenticado.
    """
    try:
        nuevo_fichaje = await crear_fichaje(
            user_id=str(current_user["_id"]),
            username=current_user["username"],
            nombre_completo=current_user.get("nombre_completo", current_user["username"]),
            tipo=fichaje.tipo,
            latitude=fichaje.latitude,
            longitude=fichaje.longitude,
            precision_gps_m=fichaje.precision_gps_m,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    
    return {
        "id": str(nuevo_fichaje["_id"]),
        "user_id": nuevo_fichaje["user_id"],
        "username": nuevo_fichaje["username"],
        "nombre_completo": nuevo_fichaje["nombre_completo"],
        "tipo": nuevo_fichaje["tipo"],
        "timestamp": nuevo_fichaje["timestamp"],
        "fecha": nuevo_fichaje["fecha"],
        "hora": nuevo_fichaje["hora"],
        "dia_semana": nuevo_fichaje["dia_semana"],
        "latitud": nuevo_fichaje.get("latitud"),
        "longitud": nuevo_fichaje.get("longitud"),
        "precision_gps_m": nuevo_fichaje.get("precision_gps_m"),
        "distancia_centro_km": nuevo_fichaje.get("distancia_centro_km"),
        "dentro_radio_autorizado": nuevo_fichaje.get("dentro_radio_autorizado"),
        "empresa_nombre": nuevo_fichaje.get("empresa_nombre"),
    }


@router.get("/mis-fichajes", response_model=List[FichajeResponse], summary="Obtener mis fichajes")
async def obtener_mis_fichajes(
    limit: int = Query(20, ge=1, le=100, description="Número de registros a devolver"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el historial de fichajes del usuario autenticado.
    """
    fichajes = await obtener_fichajes_usuario(current_user["username"], limit)
    
    return [
        {
            "id": str(f["_id"]),
            "user_id": f["user_id"],
            "username": f["username"],
            "nombre_completo": f["nombre_completo"],
            "tipo": f["tipo"],
            "timestamp": f["timestamp"],
            "fecha": f["fecha"],
            "hora": f["hora"],
            "dia_semana": f["dia_semana"]
        }
        for f in fichajes
    ]


@router.get("/mis-fichajes/fecha/{fecha}", response_model=List[FichajeResponse], summary="Obtener fichajes por fecha")
async def obtener_fichajes_fecha(
    fecha: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene los fichajes del usuario autenticado en una fecha específica.
    Formato de fecha: YYYY-MM-DD
    """
    fichajes = await obtener_fichajes_por_fecha(current_user["username"], fecha)
    
    return [
        {
            "id": str(f["_id"]),
            "user_id": f["user_id"],
            "username": f["username"],
            "nombre_completo": f["nombre_completo"],
            "tipo": f["tipo"],
            "timestamp": f["timestamp"],
            "fecha": f["fecha"],
            "hora": f["hora"],
            "dia_semana": f["dia_semana"]
        }
        for f in fichajes
    ]


@router.get("/horas-trabajadas", response_model=HorasTrabajadasResponse, summary="Calcular horas trabajadas")
async def obtener_horas_trabajadas(
    fecha: str = Query(None, description="Fecha en formato YYYY-MM-DD (None para hoy)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Calcula las horas trabajadas por el usuario en una fecha específica.
    Si no se proporciona fecha, se calcula para el día actual.
    """
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    
    horas = await calcular_horas_trabajadas(current_user["username"], fecha)
    
    if horas is None:
        return {
            "fecha": fecha,
            "horas": 0.0,
            "entradas": 0,
            "salidas": 0
        }
    
    # Obtener detalles adicionales
    fichajes_dia = await obtener_fichajes_por_fecha(current_user["username"], fecha)
    entradas = sum(1 for f in fichajes_dia if f['tipo'] == 'entrada')
    salidas = sum(1 for f in fichajes_dia if f['tipo'] == 'salida')
    
    return {
        "fecha": fecha,
        "horas": horas,
        "entradas": entradas,
        "salidas": salidas
    }


@router.get("/estadisticas", summary="Obtener estadísticas")
async def obtener_estadisticas(
    dias: int = Query(30, ge=1, le=365, description="Número de días hacia atrás"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene estadísticas de fichajes del usuario en los últimos N días.
    """
    stats = await obtener_estadisticas_usuario(current_user["username"], dias)
    return stats
