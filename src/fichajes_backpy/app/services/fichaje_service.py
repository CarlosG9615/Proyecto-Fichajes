from fichajes_backpy.app.database.mongodb import fichajes_collection
from datetime import datetime
from typing import List, Optional
from fichajes_common.location import evaluar_ubicacion_usuario, get_company_location


async def crear_fichaje(
    user_id: str,
    username: str,
    nombre_completo: str,
    tipo: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    precision_gps_m: Optional[float] = None,
) -> dict:
    """
    Crea un nuevo registro de fichaje.
    
    Args:
        user_id: ID del usuario
        username: Nombre de usuario
        nombre_completo: Nombre completo del usuario
        tipo: Tipo de fichaje ('entrada' o 'salida')
        
    Returns:
        Fichaje creado con su ID
    """
    now = datetime.now()
    fichaje = {
        "user_id": user_id,
        "usuario_id": user_id,
        "username": username,
        "nombre_completo": nombre_completo,
        "tipo": tipo,
        "timestamp": now,
        "fecha": now.strftime("%Y-%m-%d"),
        "hora": now.strftime("%H:%M:%S"),
        "dia_semana": now.strftime("%A"),
        "latitud": latitude,
        "longitud": longitude,
        "precision_gps_m": precision_gps_m,
        "distancia_centro_km": None,
        "dentro_radio_autorizado": None,
        "empresa_nombre": get_company_location().name,
    }

    if latitude is not None and longitude is not None:
        evaluacion = evaluar_ubicacion_usuario(latitude, longitude)
        if not evaluacion["within_radius"]:
            company = evaluacion["company"]
            raise ValueError(
                f"Fichaje bloqueado: estás a {evaluacion['distance_km']:.2f} km de {company.name} y el radio permitido es de {company.radius_km:.0f} km"
            )
        fichaje["distancia_centro_km"] = evaluacion["distance_km"]
        fichaje["dentro_radio_autorizado"] = evaluacion["within_radius"]
        fichaje["empresa_nombre"] = evaluacion["company"].name
    
    result = await fichajes_collection.insert_one(fichaje)
    fichaje["_id"] = result.inserted_id
    
    return fichaje


async def crear_fichaje_geolocalizado(
    user_id: str,
    username: str,
    nombre_completo: str,
    tipo: str,
    latitude: float,
    longitude: float,
    precision_gps_m: Optional[float] = None,
) -> dict:
    """Crea un fichaje y calcula automáticamente la distancia con la empresa."""
    return await crear_fichaje(
        user_id=user_id,
        username=username,
        nombre_completo=nombre_completo,
        tipo=tipo,
        latitude=latitude,
        longitude=longitude,
        precision_gps_m=precision_gps_m,
    )


async def obtener_fichajes_usuario(username: str, limit: int = 20) -> List[dict]:
    """
    Obtiene los fichajes de un usuario.
    
    Args:
        username: Nombre de usuario
        limit: Número máximo de registros a devolver
        
    Returns:
        Lista de fichajes ordenados por fecha descendente
    """
    cursor = fichajes_collection.find(
        {"username": username}
    ).sort("timestamp", -1).limit(limit)
    
    fichajes = await cursor.to_list(length=limit)
    return fichajes


async def obtener_fichajes_por_fecha(username: str, fecha: str) -> List[dict]:
    """
    Obtiene los fichajes de un usuario en una fecha específica.
    
    Args:
        username: Nombre de usuario
        fecha: Fecha en formato YYYY-MM-DD
        
    Returns:
        Lista de fichajes ordenados por timestamp
    """
    cursor = fichajes_collection.find({
        "username": username,
        "fecha": fecha
    }).sort("timestamp", 1)
    
    fichajes = await cursor.to_list(length=None)
    return fichajes


async def calcular_horas_trabajadas(username: str, fecha: Optional[str] = None) -> Optional[float]:
    """
    Calcula las horas trabajadas por un usuario en una fecha.
    
    Args:
        username: Nombre de usuario
        fecha: Fecha en formato YYYY-MM-DD (None para hoy)
        
    Returns:
        Horas trabajadas o None si no hay suficientes datos
    """
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    
    fichajes_dia = await obtener_fichajes_por_fecha(username, fecha)
    
    if len(fichajes_dia) < 2:
        return None
    
    entradas = [f for f in fichajes_dia if f['tipo'] == 'entrada']
    salidas = [f for f in fichajes_dia if f['tipo'] == 'salida']
    
    if not entradas or not salidas:
        return None
    
    tiempo_total = 0.0
    for i in range(min(len(entradas), len(salidas))):
        entrada_time = entradas[i]['timestamp']
        salida_time = salidas[i]['timestamp']
        diferencia = (salida_time - entrada_time).total_seconds() / 3600
        tiempo_total += diferencia
    
    return round(tiempo_total, 2)


async def obtener_estadisticas_usuario(username: str, dias: int = 30) -> dict:
    """
    Obtiene estadísticas de fichajes de un usuario.
    
    Args:
        username: Nombre de usuario
        dias: Número de días hacia atrás a considerar
        
    Returns:
        Diccionario con estadísticas
    """
    from datetime import timedelta
    fecha_inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    
    cursor = fichajes_collection.find({
        "username": username,
        "fecha": {"$gte": fecha_inicio}
    })
    
    fichajes = await cursor.to_list(length=None)
    
    total = len(fichajes)
    entradas = sum(1 for f in fichajes if f['tipo'] == 'entrada')
    salidas = sum(1 for f in fichajes if f['tipo'] == 'salida')
    
    return {
        "total_fichajes": total,
        "total_entradas": entradas,
        "total_salidas": salidas,
        "periodo_dias": dias
    }
