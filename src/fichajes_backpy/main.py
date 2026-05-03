from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fichajes_backpy.app.core.config import settings
from fichajes_backpy.app.routes import auth, usuarios, fichajes, telegram
from fichajes_backpy.app.database.mongodb import ping_database, close_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    Se ejecuta al inicio y al final de la aplicación.
    """
    # Startup
    print("🚀 Iniciando aplicación...")
    db_connected = await ping_database()
    if db_connected:
        print("✅ Conexión con MongoDB establecida")
    else:
        print("❌ Error al conectar con MongoDB")
    
    yield
    
    # Shutdown
    print("🛑 Cerrando aplicación...")
    await close_database()
    print("✅ Conexión con MongoDB cerrada")


# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Fichajes API",
    description="API REST para sistema de control de fichajes de empleados",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["🔐 Autenticación"]
)

app.include_router(
    usuarios.router,
    prefix="/api/usuarios",
    tags=["👥 Usuarios"]
)

app.include_router(
    fichajes.router,
    prefix="/api/fichajes",
    tags=["🕒 Fichajes"]
)

app.include_router(
    telegram.router,
    prefix="/api/telegram",
    tags=["📱 Telegram"]
)


@app.get("/", tags=["📍 Root"])
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "Sistema de Fichajes API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["📍 Root"])
async def health_check():
    """Verifica el estado de la API y la base de datos"""
    db_status = await ping_database()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "api_version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fichajes_backpy.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
