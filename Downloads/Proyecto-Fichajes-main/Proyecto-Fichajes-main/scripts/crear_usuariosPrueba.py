from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import os 
from pathlib import Path

ROOT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# =================================
# CONFIGURACIÓN
# =================================

# Contexto para bcrypt (consistente con el backend)
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

# =================================
# FUNCIONES
# =================================

def hash_password(password):
    """Hashea una contraseña usando bcrypt (consistente con el backend)"""
    return pwd_context.hash(password)

def crear_usuario(col, username, password, nombre, departamento, email, rol="user", telegram_id=None, activo=True):
    """Crea un usuario con la estructura necesaria para la app"""

    usuario = {
        "username": username,
        "password_hash": hash_password(password),
        "nombre_completo": nombre,
        "departamento": departamento,
        "email": email,
        "telegram_id": telegram_id,   # puede ser None
        "activo": activo,
        "rol": rol                    # << NUEVO CAMPO (admin/user)
    }

    col.insert_one(usuario)
    print(f"✔ Usuario '{username}' creado correctamente.")

# =================================
# PROGRAMA PRINCIPAL
# =================================

def main():
    # Conexión
    load_dotenv(ROOT_ENV_FILE)  # Carga variables desde el .env raíz
    
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DATABASE_NAME")]
    usuarios_col = db[os.getenv("USUARIOS_COLLECTION")]

    print("Creando usuarios...\n")

    # ===========================
    # Usuario admin
    # ===========================
    crear_usuario(
        col=usuarios_col,
        username="kike",
        password="1234",
        nombre="Kike",
        departamento="RRHH",
        email="admin@empresa.com",
        rol="admin"   # << ADMIN
    )

    # ===========================
    # Usuario normal
    # ===========================
    crear_usuario(
        col=usuarios_col,
        username="pepe",
        password="hola1234",
        nombre="Pepe García",
        departamento="Ventas",
        email="pepe@empresa.com",
        rol="user"   # << USUARIO NORMAL
    )

    print("\n🎉 Listo. Usuarios insertados en MongoDB.")

if __name__ == "__main__":
    main()
