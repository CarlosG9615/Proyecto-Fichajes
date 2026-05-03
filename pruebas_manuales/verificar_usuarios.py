from pymongo import MongoClient
from pathlib import Path
import os

ROOT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
from dotenv import load_dotenv
load_dotenv(ROOT_ENV_FILE)

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client[os.getenv("DATABASE_NAME", "CVKE")]
users = list(db.usuarios.find({}, {'username': 1, 'rol': 1, 'nombre_completo': 1}))

print(f'\n✅ Total usuarios en MongoDB: {len(users)}\n')
for u in users:
    print(f"👤 Usuario: {u['username']}")
    print(f"   Rol: {u['rol']}")
    print(f"   Nombre: {u['nombre_completo']}")
    print()
