"""
Crear un entorno de prueba: inserta/actualiza usuarios de prueba en MongoDB local.

Genera dos usuarios:
- Username: Admin      Password: AdminPrueba1234! (rol: admin)
- Username: Usuario    Password: UsuarioPrueba1234! (rol: user)

Este script reutiliza el `hash_password` desde el backend para generar `password_hash`.
"""
from pathlib import Path
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar .env desde la raíz del proyecto (2 niveles arriba desde src/scripts/)
ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_FILE)

from fichajes_backpy.app.core.security import hash_password

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "CVKE")
USUARIOS_COLLECTION = os.getenv("USUARIOS_COLLECTION", "usuarios")

def main():
    client = MongoClient(MONGO_URL)
    db = client[DATABASE_NAME]
    usuarios = db[USUARIOS_COLLECTION]

    test_users = [
        {
            "username": "Admin",
            "nombre_completo": "Usuario Admin Prueba",
            "departamento": "Administracion",
            "email": "admin@prueba.local",
            "rol": "admin",
            "activo": True,
            "password": "AdminPrueba1234!",
        },
        {
            "username": "Usuario",
            "nombre_completo": "Usuario Empleado Prueba",
            "departamento": "Operaciones",
            "email": "usuario@prueba.local",
            "rol": "user",
            "activo": True,
            "password": "UsuarioPrueba1234!",
        }
    ]

    for u in test_users:
        password = u.pop("password")
        u["password_hash"] = hash_password(password)
        # Upsert el usuario (sobrescribe para asegurar credenciales de prueba)
        usuarios.replace_one({"username": u["username"]}, u, upsert=True)

    print("Usuarios de prueba creados/actualizados:")
    print("- Admin / AdminPrueba1234!")
    print("- Usuario / UsuarioPrueba1234!")

if __name__ == "__main__":
    main()
