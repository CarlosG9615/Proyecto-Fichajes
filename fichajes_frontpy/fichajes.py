import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from passlib.context import CryptContext
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
ROOT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_FILE)

# Configuración desde .env
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
USUARIOS_COLLECTION = os.getenv("USUARIOS_COLLECTION")
FICHAJES_COLLECTION = os.getenv("FICHAJES_COLLECTION")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "False").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

if TELEGRAM_ENABLED:
    from telegram import Bot
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
    except:
        st.error("Error al conectar con Telegram")
        TELEGRAM_ENABLED = False

@st.cache_resource
def get_database():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        client.server_info()
        return db
    except Exception as e:
        st.error(f"Error al conectar con MongoDB: {e}")
        return None
db=get_database()

if db is not None:
    usuarios_col = db[USUARIOS_COLLECTION]
    fichajes_col = db[FICHAJES_COLLECTION]

# Contexto para bcrypt (consistente con el backend)
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

def verificar_usuario(username, password):
    """Verifica las credenciales del usuario usando bcrypt"""
    if db is None:
        return None
    
    user = usuarios_col.find_one({
        "username": username,
        "activo": True
    })
    
    if not user:
        return None
    
    # Verificar la contraseña usando bcrypt
    if not pwd_context.verify(password, user["password_hash"]):
        return None
    
    return user

def guardar_fichaje(user_id, username, nombre_completo, tipo):
    if db is None:
        return False
    fichaje = {
        "user_id": user_id,
        "username": username,
        "nombre_completo": nombre_completo,
        "tipo": tipo,
        "timestamp": datetime.now(),
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "dia_semana": datetime.now().strftime("%A")
    }

    result = fichajes_col.insert_one(fichaje)
    fichaje['_id'] = result.inserted_id
    return fichaje


def obtener_fichajes_usuario(username, limit=20):
    if db is None:
        return []
    fichajes = fichajes_col.find({
        "username": username}
        ).sort("timestamp", -1).limit(limit)
    return list(fichajes)

def calcular_horas_trabajadas(username):
    if db is None:
        return 0
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    fichajes_hoy = list(fichajes_col.find({
        "username": username,
        "fecha": fecha_hoy
    }).sort("timestamp", 1))

    if len(fichajes_hoy) < 2:
        return None
    
    entradas = [f for f in fichajes_hoy if f['tipo'] == 'entrada']
    salidas = [f for f in fichajes_hoy if f['tipo'] == 'salida']

    if entradas and salidas:
        tiempo_total = 0
        for i in range(min(len(entradas), len(salidas))):
            entrada_time = entradas[i]['timestamp']
            salida_time = salidas[i]['timestamp']
            diferencia = (salida_time - entrada_time).total_seconds() / 3600
            tiempo_total += diferencia
            return round(tiempo_total, 2)
    return None


def enviar_notificacion_telegram(telegram_id, mensaje):
    if not TELEGRAM_ENABLED:
        return False
    
    if telegram_id is None:
        return False
    try:
        bot.send_message(chat_id=telegram_id, text=mensaje)
        return True
    except Exception as e:
        return False
    
# AQUI VA LA INTERFAZ DE STREAMLIT#
st.set_page_config(
    page_title="Sistema de Fichajes",
    page_icon="🕒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .big-font {
        font-size:24px !important;
        font-weight: bold;
    }
    .stButton>button {
        height: 80px;
        font-size: 20px;
    }
    </style>
""", unsafe_allow_html=True)

if db is None:
    st.error("No se pudo conectar a MongoDB. Verifica la configuración.")
    st.stop()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

#PANTALLA DEL LOGIN#
if not st.session_state.logged_in:
    st.title("🕒 Sistema de Fichajes")
    st.markdown("---")

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        st.subheader("Acceso de Empleados")
        st.write("Por favor, ingresa tus credenciales.")

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Usuario",
                placeholder="Ingresa tu nombre de usuario",
                help="Tu nombre de usuario asignado por RRHH"
            )
            password = st.text_input(
                "Contraseña",
                type="password",
                placeholder="Ingresa tu contraseña",
                help="Tu contraseña asignada por RRHH"
            )

            col_btn1, col_btn2 = st.columns([1,1])
            with col_btn1:
                submit = st.form_submit_button(
                    "Iniciar Sesión",
                    use_container_width=True,
                    type="primary"
                )

            if submit:
                if username and password:
                    with st.spinner("Verificando credenciales..."):
                        user = verificar_usuario(username, password)

                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = str(user['_id'])
                        st.session_state.username = user['username']
                        st.session_state.nombre = user.get('nombre_completo', username)
                        st.session_state.departamento = user.get('departamento', 'N/A')
                        st.session_state.email = user.get('email', 'N/A')
                        st.session_state.telegram_id = user.get('telegram_id', None)
                        st.session_state.rol = user.get('rol', 'user')

                        st.success(f"¡Bienvenido, {st.session_state.nombre}!")
                        st.balloons
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
                        st.warning("Si no tienes acceso, contacta con RRHH.")
                else:
                    st.warning("Por favor, completa todos los campos.")
    st.markdown("---")
    st.markdown("Desarrollado por CVKE Solutions © 2025") 
    st.caption("Sistema interno - Solo usuarios autorizados")
    st.caption("Usuarios gestionados por el departamento de RRHH")

else:
    with st.sidebar:
        st.image("https://via.placeholder.com/150/0066cc/ffffff?text=👤", width=150)
        st.markdown(f"## Hola, {st.session_state.nombre}!")
        st.write(f"**Usuario:** {st.session_state.username}")
        st.write(f"**Departamento:** {st.session_state.departamento}")
        st.write(f"**Rol:** {st.session_state.rol.capitalize()}")

        if st.session_state.email != 'N/A':
            st.write(f"**Email:** {st.session_state.email}")
        st.markdown("---")

        if st.session_state.telegram_id:
            st.success("✅ Telegram vinculado")
            st.info(f"📱 ID: {st.session_state.telegram_id}")
        else:
            st.warning("⚠️ Telegram no vinculado")
            st.caption("Para vincular tu cuenta:")
            st.code("1. Abre Telegram\n2. Busca: @cvke_fichajes_bot\n3. Envía: /start\n4. Copia tu ID y pégalo aquí")
            
            with st.form("vincular_telegram"):
                telegram_id_input = st.number_input("Tu Telegram ID", min_value=1, step=1)
                submit_telegram = st.form_submit_button("Vincular Telegram")
                
                if submit_telegram and telegram_id_input:
                    # Actualizar en MongoDB
                    result = usuarios_col.update_one(
                        {"username": st.session_state.username},
                        {"$set": {"telegram_id": int(telegram_id_input)}}
                    )
                    if result.modified_count > 0:
                        st.session_state.telegram_id = int(telegram_id_input)
                        st.success("✅ Telegram vinculado correctamente!")
                        st.rerun()
                    else:
                        st.error("Error al vincular Telegram")
        st.markdown("---")

        if st.button("Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
    st.title(f"Hola, {st.session_state.nombre.split()[0]}!")
    col_fecha, col_hora = st.columns(2)
    with col_fecha:
        st.metric("Fecha", datetime.now().strftime("%d/%m/%Y"))
    with col_hora:
        st.metric("Hora", datetime.now().strftime("%H:%M:%S"))
    st.markdown("---")

    st.subheader("🕒 Registrar Fichaje")
    col1, col_space, col2 = st.columns([5,1,5])
    with col1:
        if st.button(
            "ENTRADA",
            use_container_width=True,
            type="primary",
            key="btn_entrada"
        ):
            fichaje = guardar_fichaje(
                st.session_state.user_id,
                st.session_state.username,
                st.session_state.nombre,
                'entrada'
            )
            if fichaje:
                hora = fichaje['hora']
                fecha = fichaje['fecha']
                st.success(f"Fichaje de ENTRADA registrado a las {hora}.")

                mensaje = f"🟢 ENTRADA REGISTRADA\n\n" \
                         f"👤 {st.session_state.nombre}\n" \
                         f"📅 {fecha}\n" \
                         f"⏰ {hora}"
                
                if enviar_notificacion_telegram(st.session_state.telegram_id, mensaje):
                    st.info("📱 Notificación enviada a Telegram")
                
                st.balloons()
            else:
                st.error("Error al guardar el fichaje")
    with col2:
        if st.button(
            "🔴 SALIDA",
            use_container_width=True,
            key="btn_salida"
        ):
            # Guardar fichaje en MongoDB
            fichaje = guardar_fichaje(
                st.session_state.user_id,
                st.session_state.username,
                st.session_state.nombre,
                'salida'
            )
            
            if fichaje:
                hora = fichaje['hora']
                fecha = fichaje['fecha']
                
                # Calcular horas trabajadas hoy
                horas_trabajadas = calcular_horas_trabajadas(st.session_state.username)
                
                st.success(f"✅ **SALIDA registrada** a las **{hora}**")
                
                if horas_trabajadas:
                    st.info(f"⏱️ Has trabajado **{horas_trabajadas} horas** hoy")
                
                # Enviar notificación a Telegram
                mensaje = f"🔴 SALIDA REGISTRADA\n\n" \
                         f"👤 {st.session_state.nombre}\n" \
                         f"📅 {fecha}\n" \
                         f"⏰ {hora}"
                
                if horas_trabajadas:
                    mensaje += f"\n\n⏱️ Horas trabajadas hoy: {horas_trabajadas}h"
                
                if enviar_notificacion_telegram(st.session_state.telegram_id, mensaje):
                    st.info("📱 Notificación enviada a Telegram")
            else:
                st.error("Error al guardar el fichaje")
    
    st.markdown("---")
    
    # ============================================
    # HISTORIAL DE FICHAJES
    # ============================================
    
    st.subheader("📊 Mi Historial de Fichajes")
    
    # Controles
    col_limite, col_actualizar = st.columns([4, 1])
    with col_limite:
        limite = st.slider("Número de registros a mostrar", 5, 50, 20)
    with col_actualizar:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    # Obtener fichajes
    fichajes = obtener_fichajes_usuario(st.session_state.username, limit=limite)
    
    if fichajes:
        # Tabla de fichajes
        for i, fichaje in enumerate(fichajes, 1):
            col1, col2, col3, col4, col5 = st.columns([0.5, 0.5, 2, 2, 2])
            
            with col1:
                st.write(f"**#{i}**")
            with col2:
                emoji = "🟢" if fichaje['tipo'] == "entrada" else "🔴"
                st.write(emoji)
            with col3:
                st.write(f"**{fichaje['tipo'].upper()}**")
            with col4:
                st.write(f"📅 {fichaje['fecha']}")
            with col5:
                st.write(f"⏰ {fichaje['hora']}")
        
        st.markdown("---")
        
        # Estadísticas
        st.subheader("📈 Estadísticas")
        
        total = len(fichajes)
        entradas = sum(1 for f in fichajes if f['tipo'] == 'entrada')
        salidas = sum(1 for f in fichajes if f['tipo'] == 'salida')
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        col_stat1.metric("Total Registros", total)
        col_stat2.metric("🟢 Entradas", entradas)
        col_stat3.metric("🔴 Salidas", salidas)
        
        # Horas trabajadas hoy
        horas_hoy = calcular_horas_trabajadas(st.session_state.username)
        if horas_hoy:
            st.metric("⏱️ Horas trabajadas hoy", f"{horas_hoy} h")
        
    else:
        st.info("📭 Aún no tienes fichajes registrados")
        st.write("¡Comienza registrando tu primera entrada! 👆")
    
    # Footer
    st.markdown("---")
    st.caption(
        f"Sistema de Fichajes v2.0 | "
        f"MongoDB + Streamlit + " + 
        ("Telegram Bot | " if TELEGRAM_ENABLED else "") +
        f"Usuario: {st.session_state.username}"
    )