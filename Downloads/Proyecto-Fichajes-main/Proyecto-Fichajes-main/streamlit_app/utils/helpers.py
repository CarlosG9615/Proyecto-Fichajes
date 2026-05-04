"""
Utilidades de validación y helpers
"""
import re
from datetime import datetime, date
import pandas as pd

def validar_email(email: str) -> bool:
    """Valida el formato de un email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_username(username: str) -> bool:
    """Valida el formato de un username"""
    # Solo letras, números y guión bajo, 3-50 caracteres
    patron = r'^[a-zA-Z0-9_]{3,50}$'
    return re.match(patron, username) is not None

def formatear_fecha(fecha: datetime) -> str:
    """Formatea una fecha para mostrar"""
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        except:
            return fecha
    
    if isinstance(fecha, datetime):
        return fecha.strftime('%d/%m/%Y %H:%M:%S')
    
    return str(fecha)

def formatear_fecha_corta(fecha: datetime) -> str:
    """Formatea una fecha en formato corto"""
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        except:
            return fecha
    
    if isinstance(fecha, datetime):
        return fecha.strftime('%d/%m/%Y')
    
    return str(fecha)

def convertir_objectid_a_str(documento: dict) -> dict:
    """Convierte ObjectId a string en un documento"""
    if documento and '_id' in documento:
        documento['id'] = str(documento['_id'])
        del documento['_id']
    return documento

def crear_dataframe_fichajes(fichajes: list) -> pd.DataFrame:
    """Crea un DataFrame de pandas a partir de una lista de fichajes"""
    if not fichajes:
        return pd.DataFrame()
    
    df = pd.DataFrame(fichajes)
    
    # Convertir fechas
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['fecha_str'] = df['fecha'].dt.strftime('%d/%m/%Y %H:%M:%S')
    
    # Formatear tipo
    if 'tipo' in df.columns:
        df['tipo'] = df['tipo'].str.upper()
    
    return df

def calcular_horas_trabajadas(entrada: datetime, salida: datetime) -> float:
    """Calcula las horas trabajadas entre dos fechas"""
    if not entrada or not salida:
        return 0.0
    
    diferencia = salida - entrada
    horas = diferencia.total_seconds() / 3600
    
    return round(horas, 2)

def obtener_saludo() -> str:
    """Retorna un saludo según la hora del día"""
    hora = datetime.now().hour
    
    if 5 <= hora < 12:
        return "Buenos días"
    elif 12 <= hora < 20:
        return "Buenas tardes"
    else:
        return "Buenas noches"
