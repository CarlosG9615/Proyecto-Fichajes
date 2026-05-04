from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['CVKE']
users = list(db.usuarios.find({}, {'username': 1, 'rol': 1, 'nombre_completo': 1}))

print(f'\n✅ Total usuarios en MongoDB: {len(users)}\n')
for u in users:
    print(f"👤 Usuario: {u['username']}")
    print(f"   Rol: {u['rol']}")
    print(f"   Nombre: {u['nombre_completo']}")
    print()
