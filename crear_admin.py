"""
Script para crear el primer usuario administrador
Sistema de Fichajes Integrado
"""
from pymongo import MongoClient
from passlib.context import CryptContext
from datetime import datetime
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

ROOT_ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(ROOT_ENV_FILE)

# Configuración
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "CVKE")

# Contexto de encriptación
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


def crear_admin_auto():
    """Crea un administrador por defecto sin interacción."""
    try:
        client = MongoClient(MONGO_URL)
        db = client[DATABASE_NAME]
        usuarios_col = db.usuarios

        admin_existente = usuarios_col.find_one({"rol": "admin"})
        if admin_existente:
            print("ℹ️  Ya existe un administrador. Se omite la creación automática.")
            return

        admin = {
            "username": "admin",
            "nombre_completo": "Administrador",
            "email": "admin@empresa.com",
            "departamento": "RRHH",
            "rol": "admin",
            "password_hash": pwd_context.hash("admin123"),
            "activo": True,
            "telegram_id": None,
            "creado_en": datetime.now(),
            "creado_por": "sistema",
        }

        usuarios_col.insert_one(admin)
        print("✅ Administrador creado automáticamente: admin / admin123")
    except Exception as e:
        print(f"❌ Error al crear administrador automáticamente: {e}")

def crear_admin():
    """Crea el usuario administrador inicial"""
    print("=" * 60)
    print("   CREAR ADMINISTRADOR - Sistema de Fichajes")
    print("=" * 60)
    print()
    
    # Conectar a MongoDB
    try:
        client = MongoClient(MONGO_URL)
        db = client[DATABASE_NAME]
        usuarios_col = db.usuarios
        
        print(f"✅ Conectado a MongoDB: {MONGO_URL}")
        print(f"✅ Base de datos: {DATABASE_NAME}")
        print()
    except Exception as e:
        print(f"❌ Error al conectar a MongoDB: {e}")
        print("   Asegúrate de que MongoDB esté ejecutándose")
        return
    
    # Verificar si ya existe un administrador
    admin_existente = usuarios_col.find_one({"rol": "admin"})
    
    if admin_existente:
        print("⚠️  Ya existe al menos un administrador en el sistema")
        print(f"   Username: {admin_existente.get('username')}")
        print(f"   Nombre: {admin_existente.get('nombre_completo')}")
        print()
        
        respuesta = input("¿Deseas crear otro administrador de todas formas? (s/n): ")
        if respuesta.lower() != 's':
            print("❌ Operación cancelada")
            return
        print()
    
    # Solicitar datos del administrador
    print("📝 Ingresa los datos del nuevo administrador:")
    print()
    
    username = input("Username: ").strip()
    if not username:
        print("❌ El username no puede estar vacío")
        return
    
    # Verificar si el username ya existe
    if usuarios_col.find_one({"username": username}):
        print(f"❌ El username '{username}' ya está en uso")
        return
    
    nombre_completo = input("Nombre completo: ").strip()
    if not nombre_completo:
        print("❌ El nombre completo no puede estar vacío")
        return
    
    email = input("Email: ").strip()
    if not email:
        print("❌ El email no puede estar vacío")
        return
    
    # Verificar si el email ya existe
    if usuarios_col.find_one({"email": email}):
        print(f"❌ El email '{email}' ya está registrado")
        return
    
    departamento = input("Departamento (RRHH): ").strip()
    if not departamento:
        departamento = "RRHH"
    
    password = input("Contraseña (mínimo 4 caracteres): ").strip()
    if len(password) < 4:
        print("❌ La contraseña debe tener al menos 4 caracteres")
        return
    
    password_confirm = input("Confirmar contraseña: ").strip()
    if password != password_confirm:
        print("❌ Las contraseñas no coinciden")
        return
    
    print()
    
    # Crear el administrador
    admin = {
        "username": username,
        "nombre_completo": nombre_completo,
        "email": email,
        "departamento": departamento,
        "rol": "admin",
        "password_hash": pwd_context.hash(password),
        "activo": True,
        "telegram_id": None,
        "creado_en": datetime.now(),
        "creado_por": "sistema"
    }
    
    try:
        result = usuarios_col.insert_one(admin)
        print("=" * 60)
        print("✅ ADMINISTRADOR CREADO EXITOSAMENTE")
        print("=" * 60)
        print()
        print(f"   Username: {username}")
        print(f"   Nombre: {nombre_completo}")
        print(f"   Email: {email}")
        print(f"   Departamento: {departamento}")
        print(f"   Rol: Administrador")
        print()
        print("🔐 Credenciales de acceso:")
        print(f"   Usuario: {username}")
        print(f"   Contraseña: {password}")
        print()
        print("🌐 Puedes acceder al Portal RRHH en:")
        print("   http://localhost:8501")
        print()
        print("=" * 60)
    except Exception as e:
        print(f"❌ Error al crear administrador: {e}")
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Crear admin sin interacción")
    args = parser.parse_args()

    if args.auto:
        crear_admin_auto()
        return

    crear_admin()
    print()
    input("Presiona Enter para salir...")


if __name__ == "__main__":
    main()
