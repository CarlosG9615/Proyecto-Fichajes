"""
Utilidades para la aplicación Streamlit
"""

from .auth import (
    verificar_password,
    autenticar_usuario,
    verificar_rol_admin,
    inicializar_sesion,
    login_usuario,
    logout_usuario,
    requiere_autenticacion,
    requiere_admin,
    password_cumple_politica,
    actualizar_password_usuario
)

from .database import (
    get_sync_database,
    get_usuarios_collection,
    get_fichajes_collection,
    cerrar_conexion
)

from .helpers import (
    validar_email,
    validar_username,
    formatear_fecha,
    formatear_fecha_corta,
    convertir_objectid_a_str,
    crear_dataframe_fichajes,
    calcular_horas_trabajadas,
    obtener_saludo
)

__all__ = [
    'verificar_password',
    'autenticar_usuario',
    'verificar_rol_admin',
    'inicializar_sesion',
    'login_usuario',
    'logout_usuario',
    'requiere_autenticacion',
    'requiere_admin',
    'password_cumple_politica',
    'actualizar_password_usuario',
    'get_sync_database',
    'get_usuarios_collection',
    'get_fichajes_collection',
    'cerrar_conexion',
    'validar_email',
    'validar_username',
    'formatear_fecha',
    'formatear_fecha_corta',
    'convertir_objectid_a_str',
    'crear_dataframe_fichajes',
    'calcular_horas_trabajadas',
    'obtener_saludo'
]
