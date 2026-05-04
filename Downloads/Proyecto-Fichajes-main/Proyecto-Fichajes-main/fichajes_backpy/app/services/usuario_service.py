from app.database.mongodb import usuarios_collection
from app.core.security import hash_password
from bson import ObjectId
from typing import List, Optional


async def obtener_usuario_por_username(username: str) -> Optional[dict]:
    """Obtiene un usuario por su username"""
    return await usuarios_collection.find_one({"username": username})


async def obtener_usuario_por_id(user_id: str) -> Optional[dict]:
    """Obtiene un usuario por su ID"""
    try:
        return await usuarios_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return None


async def obtener_todos_usuarios() -> List[dict]:
    """Obtiene todos los usuarios"""
    cursor = usuarios_collection.find({})
    usuarios = await cursor.to_list(length=None)
    return usuarios


async def crear_usuario(usuario_data: dict) -> dict:
    """
    Crea un nuevo usuario.
    
    Args:
        usuario_data: Datos del usuario incluyendo password
        
    Returns:
        Usuario creado con su ID
    """
    # Hashear la contraseña
    password = usuario_data.pop("password")
    usuario_data["password_hash"] = hash_password(password)
    
    # Insertar en la base de datos
    result = await usuarios_collection.insert_one(usuario_data)
    usuario_data["_id"] = result.inserted_id
    
    return usuario_data


async def actualizar_usuario(user_id: str, datos_actualizacion: dict) -> Optional[dict]:
    """
    Actualiza un usuario existente.
    
    Args:
        user_id: ID del usuario
        datos_actualizacion: Datos a actualizar
        
    Returns:
        Usuario actualizado o None si no existe
    """
    # Si se actualiza la contraseña, hashearla
    if "password" in datos_actualizacion:
        password = datos_actualizacion.pop("password")
        datos_actualizacion["password_hash"] = hash_password(password)
    
    # Filtrar campos None
    datos_actualizacion = {k: v for k, v in datos_actualizacion.items() if v is not None}
    
    if not datos_actualizacion:
        return await obtener_usuario_por_id(user_id)
    
    try:
        result = await usuarios_collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": datos_actualizacion},
            return_document=True
        )
        return result
    except:
        return None


async def eliminar_usuario(user_id: str) -> bool:
    """
    Desactiva un usuario (soft delete).
    
    Args:
        user_id: ID del usuario
        
    Returns:
        True si se desactivó correctamente, False en caso contrario
    """
    try:
        result = await usuarios_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"activo": False}}
        )
        return result.modified_count > 0
    except:
        return False
