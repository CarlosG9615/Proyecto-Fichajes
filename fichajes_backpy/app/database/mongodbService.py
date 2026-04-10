from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Cliente de MongoDB con motor (async)
client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]

# Colecciones
usuarios_collection = db[settings.USUARIOS_COLLECTION]
fichajes_collection = db[settings.FICHAJES_COLLECTION]


async def ping_database():
    """Verifica la conexión con MongoDB"""
    try:
        await client.admin.command('ping')
        return True
    except Exception as e:
        print(f"Error al conectar con MongoDB: {e}")
        return False


async def close_database():
    """Cierra la conexión con MongoDB"""
    client.close()