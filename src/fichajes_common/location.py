"""Configuración y cálculos de geolocalización de la empresa."""
from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class CompanySettings(BaseSettings):
    COMPANY_NAME: str = "Instituto de Educación Secundaria Alonso de Avellaneda"
    COMPANY_ADDRESS: str = (
        "Instituto de Educación Secundaria Alonso de Avellaneda, 3, Calle de Vitoria, "
        "Virgen del Val, Distrito V, Alcalá de Henares, Community of Madrid, 28804, Spain"
    )
    COMPANY_LATITUDE: float = 40.490274
    COMPANY_LONGITUDE: float = -3.3431943
    COMPANY_RADIUS_KM: float = 30.0

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        case_sensitive=True,
        extra="ignore",
    )


@dataclass(frozen=True)
class CompanyLocation:
    name: str
    address: str
    latitude: float
    longitude: float
    radius_km: float


settings = CompanySettings()


def get_company_location() -> CompanyLocation:
    return CompanyLocation(
        name=settings.COMPANY_NAME,
        address=settings.COMPANY_ADDRESS,
        latitude=settings.COMPANY_LATITUDE,
        longitude=settings.COMPANY_LONGITUDE,
        radius_km=settings.COMPANY_RADIUS_KM,
    )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia geodésica aproximada en kilómetros."""
    radio_tierra_km = 6371.0

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radio_tierra_km * c


def evaluar_ubicacion_usuario(latitude: float, longitude: float) -> dict:
    """Compara la ubicación del usuario con la ubicación de la empresa."""
    company = get_company_location()
    distance_km = haversine_km(latitude, longitude, company.latitude, company.longitude)
    within_radius = distance_km <= company.radius_km

    return {
        "company": company,
        "distance_km": round(distance_km, 2),
        "within_radius": within_radius,
    }
