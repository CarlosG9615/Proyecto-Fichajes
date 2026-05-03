"""Utilidades de geolocalización para el portal Streamlit."""
from __future__ import annotations

import json
import requests
import streamlit as st

import streamlit.components.v1 as components

from fichajes_common.location import evaluar_ubicacion_usuario, get_company_location


def obtener_ubicacion_por_ip() -> dict | None:
    """
    Obtiene la ubicación basada en la IP pública del usuario (WiFi/red).
    Usa el servicio ip-api.com que es gratuito, sin API key y con mejor rate limiting.
    """
    try:
        with st.spinner("🔍 Detectando tu ubicación por WiFi/Red..."):
            # ip-api.com: 45 requests/minuto en free tier (suficiente para fichajes)
            response = requests.get(
                "http://ip-api.com/json/",
                timeout=5,
                headers={"User-Agent": "fichajes-app/1.0"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "ok": True,
                        "latitude": float(data.get("lat", 0)),
                        "longitude": float(data.get("lon", 0)),
                        "accuracy": 5000,  # Aproximadamente 5km de precisión por IP
                        "ip": data.get("query"),
                        "city": data.get("city"),
                        "country": data.get("country"),
                        "isp": data.get("isp"),
                        "method": "IP"
                    }
                else:
                    error_msg = data.get("message", "Error desconocido")
                    return {"ok": False, "error": f"Servicio de ubicación: {error_msg}"}
            else:
                return {"ok": False, "error": f"Error al consultar ubicación por IP (status: {response.status_code})"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Timeout al consultar ubicación por IP (>5s)"}
    except Exception as e:
        return {"ok": False, "error": f"Error al obtener ubicación por IP: {str(e)}"}


def render_google_maps_embed(latitude: float, longitude: float, title: str = "Ubicación") -> None:
    """Renderiza un mapa embed de Google Maps compacto."""
    html = f"""
    <iframe 
        src="https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d3034.32128019159!2d{longitude}!3d{latitude}!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2z{latitude}N+{abs(longitude)}W!5e0!3m2!1ses!2ses!4v1777808738624!5m2!1ses!2ses" 
        width="100%" 
        height="300" 
        style="border:0; border-radius: 8px;" 
        allowfullscreen="" 
        loading="lazy" 
        referrerpolicy="no-referrer-when-downgrade">
    </iframe>
    """
    components.html(html, height=320)


def evaluar_ubicacion_compania(latitude: float, longitude: float) -> dict:
    return evaluar_ubicacion_usuario(latitude, longitude)


def obtener_empresa() -> dict:
    company = get_company_location()
    return {
        "name": company.name,
        "address": company.address,
        "latitude": company.latitude,
        "longitude": company.longitude,
        "radius_km": company.radius_km,
    }
