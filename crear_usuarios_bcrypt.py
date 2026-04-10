"""
Script para crear usuarios usando bcrypt directamente (sin passlib)
"""
from pymongo import MongoClient
import bcrypt
from dotenv import load_dotenv
import os
from pathlib import Path

ROOT_ENV_FILE = Path(__file__).resolve().parent / ".env"

def crear_usuario(col, username, password, nombre, departamento, email, rol="user"):
    """Crea un usuario con bcrypt directo"""
    
    # Hash con bcrypt directo
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    usuario = {
        "username": username,
        "password_hash": password_hash,
        "nombre_completo": nombre,
        "departamento": departamento,
        "email": email,
        "telegram_id": None,
        "activo": True,
        "rol": rol
    }
    
    col.insert_one(usuario)
    print(f"✔ Usuario '{username}' creado correctamente.")

def main():
    load_dotenv(ROOT_ENV_FILE)
    
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    db = client[os.getenv("DATABASE_NAME", "CVKE")]
    usuarios_col = db[os.getenv("USUARIOS_COLLECTION", "usuarios")]
    
    # Limpiar usuarios existentes
    result = usuarios_col.delete_many({})
    print(f"🗑️  Usuarios eliminados: {result.deleted_count}\n")
    
    print("Creando usuarios con bcrypt directo...\n")
    
    # Usuario admin
    crear_usuario(
        col=usuarios_col,
        username="kike",
        password="1234",
        nombre="Kike Admin",
        departamento="RRHH",
        email="admin@empresa.com",
        rol="admin"
    )
    
    # Usuario normal
    crear_usuario(
        col=usuarios_col,
        username="pepe",
        password="hola1234",
        nombre="Pepe García",
        departamento="Ventas",
        email="pepe@empresa.com",
        rol="user"
    )
    
    print("\n🎉 Listo. Usuarios creados con bcrypt directo.")

if __name__ == "__main__":
    main()
