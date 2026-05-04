"""
Script para resetear el administrador del sistema
Útil si hay problemas con el hash de la contraseña
"""
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from pathlib import Path

# Cargar variables de entorno
ROOT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ROOT_ENV_FILE)

# Configuración
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "CVKE")

# Contexto para bcrypt
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

def resetear_admin():
    """Resetea el administrador por defecto"""
    try:
        # Conectar a MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        
        # Verificar conexión
        client.server_info()
        print("✅ Conectado a MongoDB")
        
        # Eliminar administradores existentes
        result = db['administradores'].delete_many({})
        print(f"🗑️  Eliminados {result.deleted_count} administradores")
        
        # Crear nuevo administrador
        admin_password = 'admin123'
        admin_hash = pwd_context.hash(admin_password)
        
        db['administradores'].insert_one({
            'usuario': 'admin',
            'password_hash': admin_hash,
            'nombre': 'Administrador',
            'email': 'admin@empresa.com',
            'rol': 'admin',
            'activo': True
        })
        
        print("✅ Administrador creado correctamente")
        print()
        print("📋 Credenciales:")
        print(f"   Usuario: admin")
        print(f"   Contraseña: admin123")
        print()
        print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("  RESETEAR ADMINISTRADOR DEL SISTEMA")
    print("=" * 50)
    print()
    
    # Si se pasa --force como argumento, no preguntar
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        resetear_admin()
    else:
        respuesta = input("¿Estás seguro de resetear el administrador? (S/N): ")
        
        if respuesta.upper() == 'S':
            print()
            resetear_admin()
        else:
            print("Operación cancelada")
