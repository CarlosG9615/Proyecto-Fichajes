"""
Utilidades de autenticación para Streamlit
"""
import streamlit as st
import hashlib
import hmac
import re
import secrets
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from datetime import datetime, timedelta
from bson import ObjectId
from streamlit_javascript import st_javascript
from streamlit_app.utils.database import get_usuarios_collection, get_sync_database

# Contexto de encriptación (mismo que el backend)
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# Gestión de sesiones persistentes (MongoDB + localStorage)
# ---------------------------------------------------------------------------

def _crear_sesion_db(user_id: str) -> str:
    """Crea una sesión en MongoDB y retorna el token."""
    token = secrets.token_urlsafe(32)
    db = get_sync_database()
    db.sessions.insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24),
    })
    return token


def _recuperar_sesion_db(token: str):
    """Recupera el usuario asociado a un token de sesión válido."""
    db = get_sync_database()
    session = db.sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.now()},
    })
    if not session:
        return None
    usuarios_col = get_usuarios_collection()
    try:
        return usuarios_col.find_one({"_id": ObjectId(session["user_id"]), "activo": True})
    except Exception:
        return None


def _eliminar_sesion_db(token: str) -> None:
    """Elimina la sesión del servidor."""
    db = get_sync_database()
    db.sessions.delete_one({"token": token})


def password_cumple_politica(password: str) -> tuple[bool, list[str]]:
    """Valida la política de contraseñas del sistema."""
    errores: list[str] = []

    if len(password) < 12:
        errores.append("La contraseña debe tener al menos 12 caracteres.")

    if not re.search(r"[A-Z]", password):
        errores.append("La contraseña debe incluir al menos una letra mayúscula.")

    if not re.search(r"[a-z]", password):
        errores.append("La contraseña debe incluir al menos una letra minúscula.")

    if not re.search(r"\d", password):
        errores.append("La contraseña debe incluir al menos un número.")

    if not re.search(r"[^A-Za-z0-9]", password):
        errores.append("La contraseña debe incluir al menos un símbolo.")

    return len(errores) == 0, errores

def verificar_password(password_plana: str, password_hash: str) -> tuple[bool, bool]:
    """
    Verifica una contraseña contra su hash.
    Retorna (es_valida, requiere_migracion_a_bcrypt).
    """
    if not password_hash:
        return False, False

    # Flujo normal: bcrypt/passlib
    try:
        return pwd_context.verify(password_plana, password_hash), False
    except UnknownHashError:
        # Hash legacy no reconocido por passlib.
        pass
    except Exception:
        return False, False

    # Compatibilidad legacy: SHA256 hexadecimal (64 chars)
    sha256_hash = hashlib.sha256(password_plana.encode("utf-8")).hexdigest()
    if len(password_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in password_hash):
        if hmac.compare_digest(password_hash.lower(), sha256_hash):
            return True, True

    # Compatibilidad extrema legacy: contraseña guardada en texto plano
    if hmac.compare_digest(password_hash, password_plana):
        return True, True

    return False, False

def autenticar_usuario(username: str, password: str):
    """
    Autentica un usuario por username y password
    Retorna el usuario si es válido, None en caso contrario
    """
    usuarios_col = get_usuarios_collection()
    usuario = usuarios_col.find_one({"username": username, "activo": True})

    if not usuario:
        return None

    es_valida, requiere_migracion = verificar_password(password, usuario.get("password_hash", ""))
    if es_valida:
        password_change_required = bool(usuario.get("password_change_required", False))

        if requiere_migracion:
            password_change_required = True

        if "password_change_required" not in usuario or usuario.get("password_change_required") != password_change_required:
            usuarios_col.update_one(
                {"_id": usuario["_id"]},
                {"$set": {"password_change_required": password_change_required}}
            )

        usuario["password_change_required"] = password_change_required

        return usuario
    
    return None


def actualizar_password_usuario(usuario_id, nueva_password: str) -> tuple[bool, str]:
    """Actualiza la contraseña de un usuario y limpia el requisito de cambio."""
    valida, errores = password_cumple_politica(nueva_password)
    if not valida:
        return False, "\n".join(errores)

    usuarios_col = get_usuarios_collection()
    try:
        object_id = usuario_id if isinstance(usuario_id, ObjectId) else ObjectId(str(usuario_id))
        usuarios_col.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "password_hash": hash_password(nueva_password),
                    "password_change_required": False,
                    "actualizado_en": datetime.now()
                }
            }
        )
        return True, "Contraseña actualizada correctamente."
    except Exception as e:
        return False, f"Error al actualizar la contraseña: {e}"

def verificar_rol_admin(usuario: dict) -> bool:
    """Verifica si un usuario tiene rol de administrador"""
    return usuario.get("rol") == "admin"

def inicializar_sesion():
    """Inicializa las variables de sesión y restaura desde localStorage si hay token guardado."""
    defaults = {
        'logged_in': False,
        'usuario': None,
        'rol': None,
        'user_id': None,
        'session_token': None,
        '_token_to_save': None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Primer render tras login: guardar el token en localStorage.
    # Se hace aqui (y no en login_usuario) para evitar la carrera con st.rerun().
    pending = st.session_state.get('_token_to_save')
    if pending:
        st.session_state._token_to_save = None
        st_javascript(f"localStorage.setItem('fichajes_session_token', '{pending}')")
        return  # ya estamos logados, la pagina renderizara correctamente

    # Restaurar sesion desde localStorage en cada recarga de pagina.
    if not st.session_state.logged_in:
        token = st_javascript("localStorage.getItem('fichajes_session_token')")
        if isinstance(token, str) and token:
            usuario = _recuperar_sesion_db(token)
            if usuario:
                st.session_state.logged_in = True
                st.session_state.usuario = usuario
                st.session_state.rol = usuario.get("rol", "user")
                st.session_state.user_id = str(usuario.get("_id"))
                st.session_state.session_token = token
                st.rerun()  # forzar re-render con sesion restaurada

def login_usuario(usuario: dict):
    """Inicia sesión de un usuario. El token se guarda en localStorage en el siguiente render."""
    token = _crear_sesion_db(str(usuario.get("_id")))
    st.session_state.logged_in = True
    st.session_state.usuario = usuario
    st.session_state.rol = usuario.get("rol", "user")
    st.session_state.user_id = str(usuario.get("_id"))
    st.session_state.session_token = token
    st.session_state._token_to_save = token  # inicializar_sesion lo guardara en localStorage

def logout_usuario():
    """Cierra sesión del usuario y elimina el token de localStorage."""
    token = st.session_state.get('session_token')
    if token:
        _eliminar_sesion_db(token)
    st_javascript("localStorage.removeItem('fichajes_session_token')")
    st.session_state.logged_in = False
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.user_id = None
    st.session_state.session_token = None
    st.session_state._token_to_save = None

def requiere_autenticacion():
    """Decorator o función que requiere autenticación"""
    if not st.session_state.get('logged_in', False):
        return False
    return True

def requiere_admin():
    """Verifica si el usuario actual es administrador"""
    if not requiere_autenticacion():
        return False
    return st.session_state.get('rol') == 'admin'
