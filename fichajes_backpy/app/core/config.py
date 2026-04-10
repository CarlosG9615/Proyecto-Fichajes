from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno"""
    
    # Seguridad
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MongoDB
    MONGO_URI: str
    DATABASE_NAME: str
    USUARIOS_COLLECTION: str = "usuarios"
    FICHAJES_COLLECTION: str = "fichajes"
    
    # Telegram (opcional)
    TELEGRAM_TOKEN: Optional[str] = None
    TELEGRAM_ENABLED: bool = False
    
    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
