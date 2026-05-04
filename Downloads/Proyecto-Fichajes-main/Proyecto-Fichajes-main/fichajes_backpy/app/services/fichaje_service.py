from app.database.mongodb import fichajes_collection
from datetime import datetime
from typing import List, Optional


async def crear_fichaje(user_id: str, username: str, nombre_completo: str, tipo: str) -> dict:
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
        "username": username,
        "nombre_completo": nombre_completo,
        "tipo": tipo,
        "timestamp": now,
        "fecha": now.strftime("%Y-%m-%d"),
        "hora": now.strftime("%H:%M:%S"),
        "dia_semana": now.strftime("%A")
    }
    
    result = await fichajes_collection.insert_one(fichaje)
    fichaje["_id"] = result.inserted_id
    
    return fichaje


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
