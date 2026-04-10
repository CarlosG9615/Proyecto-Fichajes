"""
Utilidades para conexión con MongoDB y el backend
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv
import asyncio
import os
from pathlib import Path
import sys


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_FILE)

# Configuración de MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "CVKE")

# Cliente síncrono para Streamlit
_sync_client = None
_sync_db = None

def get_sync_database():
    """Obtiene la base de datos MongoDB de forma síncrona (para Streamlit)"""
    global _sync_client, _sync_db
    
    if _sync_db is None:
        _sync_client = MongoClient(MONGO_URL)
        _sync_db = _sync_client[DATABASE_NAME]
    
    return _sync_db

def get_usuarios_collection():
    """Obtiene la colección de usuarios"""
    db = get_sync_database()
    return db.usuarios

def get_fichajes_collection():
    """Obtiene la colección de fichajes"""
    db = get_sync_database()
    return db.fichajes

def cerrar_conexion():
    """Cierra la conexión a MongoDB"""
    global _sync_client
    if _sync_client:
        _sync_client.close()
