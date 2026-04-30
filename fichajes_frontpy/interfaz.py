"""
Sistema de Fichajes - Interfaz Administrativa Completa
Dashboard de RRHH para gestión de empleados y fichajes
"""
import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
from passlib.context import CryptContext
import pandas as pd
import re
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
ROOT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_FILE)

# Configuración de la página
st.set_page_config(
    page_title="Sistema RRHH - Administración",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración desde .env
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
USUARIOS_COLLECTION = os.getenv("USUARIOS_COLLECTION")
FICHAJES_COLLECTION = os.getenv("FICHAJES_COLLECTION")

# Contexto para bcrypt (consistente con el backend)
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

# Conexión a MongoDB
@st.cache_resource
def get_database():
    """Conexión singleton a MongoDB"""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        
        # Verificar conexión
        client.server_info()
        
        # Crear administrador por defecto si no existe
        try:
            if db['administradores'].count_documents({}) == 0:
                admin_password = 'admin123'
                admin_hash = pwd_context.hash(admin_password)
                db['administradores'].insert_one({
                    'usuario': 'admin',
                    'password_hash': admin_hash,
                    'nombre': 'Administrador',
                    'email': 'admin@empresa.com',
                    'rol': 'admin',
                    'activo': True,
                    'fecha_creacion': datetime.now()
                })
        except Exception as e:
            # Si falla la creación del admin, continuar de todas formas
            pass
        
        # Crear índices
        db[USUARIOS_COLLECTION].create_index("username", unique=True)
        db[USUARIOS_COLLECTION].create_index("telegram_id", unique=True, sparse=True)
        db['administradores'].create_index("usuario", unique=True)
        
        return db
    except Exception as e:
        st.error(f"❌ Error al conectar con MongoDB: {e}")
        return None

db = get_database()

# Funciones auxiliares
def verificar_password(plain_password, hashed_password):
    """Verifica una contraseña usando bcrypt"""
    try:
        # bcrypt tiene un límite de 72 bytes
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password[:72]
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        st.error(f"Error al verificar contraseña: {e}")
        return False

def hash_password(password):
    """Hashea una contraseña usando bcrypt"""
    try:
        # bcrypt tiene un límite de 72 bytes
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        return pwd_context.hash(password)
    except Exception as e:
        st.error(f"Error al hashear contraseña: {e}")
        return None

def verificar_login(usuario, password):
    """Verifica las credenciales del administrador"""
    if db is None:
        return None
    
    admin = db['administradores'].find_one({
        'usuario': usuario,
        'activo': True
    })
    
    if not admin:
        return None
    
    if not verificar_password(password, admin['password_hash']):
        return None
    
    return admin

def validar_email(email):
    """Valida formato de email"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Inicializar estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.admin = None

# ========== ESTILOS CSS ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== PÁGINA DE LOGIN ==========
def mostrar_login():
    """Muestra la página de inicio de sesión"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🔐 Sistema RRHH - Administración")
        st.markdown("---")
        
        with st.form("login_form", clear_on_submit=False):
            usuario = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True, type="primary")
            
            if submit:
                if usuario and password:
                    admin = verificar_login(usuario, password)
                    if admin:
                        st.session_state.logged_in = True
                        st.session_state.admin = admin
                        st.success("✅ Acceso concedido")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                else:
                    st.warning("⚠️ Por favor, completa todos los campos")
        
        st.info("💡 **Credenciales por defecto:**\n- Usuario: `admin`\n- Contraseña: `admin123`")
        st.caption("Sistema de Fichajes © 2024")

# ========== PÁGINA PRINCIPAL (DASHBOARD) ==========
def mostrar_dashboard():
    """Muestra el dashboard principal con menú de navegación"""
    if db is None:
        st.error("❌ No se puede conectar con la base de datos")
        return
    
    st.sidebar.title(f"👋 {st.session_state.admin['nombre']}")
    st.sidebar.markdown(f"**Rol:** {st.session_state.admin.get('rol', 'admin').upper()}")
    st.sidebar.markdown("---")
    
    # Menú de navegación
    menu = st.sidebar.radio(
        "📋 Navegación",
        ["🏠 Dashboard", "➕ Crear Empleado", "👥 Lista de Empleados", "⏰ Fichajes", "📊 Reportes", "⚙️ Configuración"]
    )
    
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.admin = None
        st.rerun()
    
    # Contenido según menú seleccionado
    if menu == "🏠 Dashboard":
        pagina_dashboard()
    elif menu == "➕ Crear Empleado":
        pagina_crear_empleado()
    elif menu == "👥 Lista de Empleados":
        pagina_lista_empleados()
    elif menu == "⏰ Fichajes":
        pagina_fichajes()
    elif menu == "📊 Reportes":
        pagina_reportes()
    elif menu == "⚙️ Configuración":
        pagina_configuracion()

# ========== DASHBOARD ==========
def pagina_dashboard():
    """Página principal con estadísticas y resumen"""
    st.markdown('<h1 class="main-header">🏠 Dashboard General</h1>', unsafe_allow_html=True)
    
    # Estadísticas principales
    col1, col2, col3, col4 = st.columns(4)
    
    total_empleados = db[USUARIOS_COLLECTION].count_documents({'activo': True})
    total_inactivos = db[USUARIOS_COLLECTION].count_documents({'activo': False})
    
    # Fichajes de hoy
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fichajes_hoy = db[FICHAJES_COLLECTION].count_documents({'timestamp': {'$gte': hoy_inicio}})
    
    # Empleados con Telegram vinculado
    con_telegram = db[USUARIOS_COLLECTION].count_documents({
        'telegram_id': {'$exists': True, '$ne': None},
        'activo': True
    })
    
    with col1:
        st.metric("👥 Empleados Activos", total_empleados)
    with col2:
        st.metric("⏰ Fichajes Hoy", fichajes_hoy)
    with col3:
        st.metric("📱 Con Telegram", con_telegram)
    with col4:
        st.metric("🚫 Inactivos", total_inactivos)
    
    st.markdown("---")
    
    # Últimos fichajes
    st.subheader("📋 Últimos Fichajes Registrados")
    
    ultimos_fichajes = list(db[FICHAJES_COLLECTION].find().sort('timestamp', -1).limit(15))
    
    if ultimos_fichajes:
        df_fichajes = pd.DataFrame(ultimos_fichajes)
        
        # Formatear datos
        df_fichajes['fecha_hora'] = pd.to_datetime(df_fichajes['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
        df_fichajes['tipo_fmt'] = df_fichajes['tipo'].str.upper()
        
        # Agregar emoji según tipo
        df_fichajes['tipo_emoji'] = df_fichajes['tipo'].apply(lambda x: '🟢 ENTRADA' if x == 'entrada' else '🔴 SALIDA')
        
        # Seleccionar columnas a mostrar
        columnas_mostrar = ['fecha_hora', 'nombre_completo', 'username', 'tipo_emoji']
        if 'departamento' in df_fichajes.columns:
            columnas_mostrar.append('departamento')
        
        df_display = df_fichajes[columnas_mostrar]
        df_display.columns = ['Fecha y Hora', 'Nombre', 'Usuario', 'Tipo'] + (['Departamento'] if 'departamento' in df_fichajes.columns else [])
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No hay fichajes registrados todavía")
    
    # Gráfico de actividad
    st.markdown("---")
    st.subheader("📈 Actividad de Fichajes - Últimos 7 Días")
    
    fecha_inicio = datetime.now() - timedelta(days=7)
    fichajes_semana = list(db[FICHAJES_COLLECTION].find({'timestamp': {'$gte': fecha_inicio}}))
    
    if fichajes_semana:
        df_semana = pd.DataFrame(fichajes_semana)
        df_semana['dia'] = pd.to_datetime(df_semana['timestamp']).dt.date
        fichajes_por_dia = df_semana.groupby('dia').size().reset_index(name='Cantidad')
        fichajes_por_dia.columns = ['Día', 'Fichajes']
        
        st.line_chart(fichajes_por_dia.set_index('Día'), use_container_width=True)
    else:
        st.info("No hay suficientes datos para mostrar el gráfico")

# ========== CREAR EMPLEADO ==========
def pagina_crear_empleado():
    """Página para crear nuevos empleados"""
    st.markdown('<h1 class="main-header">➕ Crear Nuevo Empleado</h1>', unsafe_allow_html=True)
    
    with st.form("form_empleado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 Datos Personales")
            nombre_completo = st.text_input("Nombre Completo *", placeholder="Juan Pérez García")
            username = st.text_input("Usuario (para login) *", placeholder="jperez")
            email = st.text_input("Email *", placeholder="juan.perez@empresa.com")
            telefono = st.text_input("Teléfono", placeholder="+34 600 000 000")
            dni = st.text_input("DNI/NIE *", placeholder="12345678A")
        
        with col2:
            st.subheader("💼 Datos Laborales")
            cargo = st.text_input("Cargo *", placeholder="Desarrollador Senior")
            departamento = st.text_input("Departamento *", placeholder="IT / Tecnología")
            password = st.text_input("Contraseña inicial *", type="password", placeholder="Contraseña temporal")
            password_confirm = st.text_input("Confirmar Contraseña *", type="password")
            
            st.markdown("---")
            st.subheader("📱 Telegram (Opcional)")
            telegram_id = st.text_input("Telegram ID", placeholder="Se vinculará después", help="El empleado puede vincularse usando el bot")
            telegram_username = st.text_input("Username Telegram", placeholder="@usuario")
        
        st.markdown("---")
        submitted = st.form_submit_button("✅ Crear Empleado", use_container_width=True, type="primary")
        
        if submitted:
            # Validaciones
            errores = []
            
            if not all([nombre_completo, username, email, dni, cargo, departamento, password, password_confirm]):
                errores.append("Por favor, completa todos los campos obligatorios (*)")
            
            if password != password_confirm:
                errores.append("Las contraseñas no coinciden")
            
            if len(password) < 6:
                errores.append("La contraseña debe tener al menos 6 caracteres")
            
            if not validar_email(email):
                errores.append("Email inválido")
            
            # Verificar duplicados
            if db[USUARIOS_COLLECTION].find_one({'username': username}):
                errores.append(f"El usuario '{username}' ya existe")
            
            if db[USUARIOS_COLLECTION].find_one({'dni': dni.upper()}):
                errores.append(f"Ya existe un empleado con el DNI {dni.upper()}")
            
            if db[USUARIOS_COLLECTION].find_one({'email': email}):
                errores.append(f"El email {email} ya está registrado")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                # Crear empleado
                empleado = {
                    'username': username.lower(),
                    'nombre_completo': nombre_completo,
                    'email': email.lower(),
                    'telefono': telefono,
                    'dni': dni.upper(),
                    'cargo': cargo,
                    'departamento': departamento,
                    'password_hash': hash_password(password),
                    'telegram_id': int(telegram_id) if telegram_id else None,
                    'telegram_username': telegram_username if telegram_username else None,
                    'fecha_alta': datetime.now(),
                    'activo': True,
                    'rol': 'empleado',
                    'creado_por': st.session_state.admin['usuario'],
                    'fecha_creacion': datetime.now()
                }
                
                try:
                    result = db[USUARIOS_COLLECTION].insert_one(empleado)
                    st.success(f"✅ Empleado **{nombre_completo}** creado correctamente con ID: {result.inserted_id}")
                    st.balloons()
                    
                    # Mostrar información
                    st.info(f"📧 **Credenciales de acceso:**\n- Usuario: `{username}`\n- Contraseña: `{password}`\n\n⚠️ El empleado debe cambiar su contraseña en el primer acceso.")
                except Exception as e:
                    st.error(f"❌ Error al crear empleado: {str(e)}")

# ========== LISTA DE EMPLEADOS ==========
def pagina_lista_empleados():
    """Página de listado y gestión de empleados"""
    st.markdown('<h1 class="main-header">👥 Gestión de Empleados</h1>', unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filtro_estado = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"])
    with col2:
        filtro_telegram = st.selectbox("Telegram", ["Todos", "Con Telegram", "Sin Telegram"])
    with col3:
        filtro_departamento = st.selectbox("Departamento", ["Todos"] + obtener_departamentos())
    with col4:
        buscar = st.text_input("🔍 Buscar", placeholder="Nombre o DNI")
    
    # Construir query
    query = {}
    
    if filtro_estado == "Activos":
        query['activo'] = True
    elif filtro_estado == "Inactivos":
        query['activo'] = False
    
    if filtro_telegram == "Con Telegram":
        query['telegram_id'] = {'$exists': True, '$ne': None}
    elif filtro_telegram == "Sin Telegram":
        query['$or'] = [
            {'telegram_id': {'$exists': False}},
            {'telegram_id': None}
        ]
    
    if filtro_departamento != "Todos":
        query['departamento'] = filtro_departamento
    
    if buscar:
        query['$or'] = [
            {'nombre_completo': {'$regex': buscar, '$options': 'i'}},
            {'username': {'$regex': buscar, '$options': 'i'}},
            {'dni': {'$regex': buscar, '$options': 'i'}}
        ]
    
    # Obtener empleados
    empleados = list(db[USUARIOS_COLLECTION].find(query).sort('nombre_completo', 1))
    
    st.markdown(f"**Total de empleados encontrados:** {len(empleados)}")
    st.markdown("---")
    
    if empleados:
        # Crear DataFrame para visualización
        df = pd.DataFrame(empleados)
        
        # Formatear columnas
        df['fecha_alta_fmt'] = pd.to_datetime(df['fecha_alta']).dt.strftime('%d/%m/%Y')
        df['telegram_status'] = df['telegram_id'].apply(lambda x: '✅ Sí' if x else '❌ No')
        df['estado'] = df['activo'].apply(lambda x: '🟢 Activo' if x else '🔴 Inactivo')
        
        # Seleccionar y renombrar columnas
        columnas = ['nombre_completo', 'username', 'dni', 'cargo', 'departamento', 'email', 'telefono', 'telegram_status', 'estado', 'fecha_alta_fmt']
        df_display = df[columnas]
        df_display.columns = ['Nombre', 'Usuario', 'DNI', 'Cargo', 'Departamento', 'Email', 'Teléfono', 'Telegram', 'Estado', 'Fecha Alta']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Opciones de exportación
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"empleados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Detalle de empleado seleccionado
        st.markdown("---")
        st.subheader("🔍 Detalle de Empleado")
        
        empleado_seleccionado = st.selectbox(
            "Seleccionar empleado para ver detalles",
            options=range(len(empleados)),
            format_func=lambda i: f"{empleados[i]['nombre_completo']} ({empleados[i]['username']})"
        )
        
        if empleado_seleccionado is not None:
            mostrar_detalle_empleado(empleados[empleado_seleccionado])
    else:
        st.info("📭 No se encontraron empleados con los filtros seleccionados")

def obtener_departamentos():
    """Obtiene lista única de departamentos"""
    departamentos = db[USUARIOS_COLLECTION].distinct('departamento')
    return sorted([d for d in departamentos if d])

def mostrar_detalle_empleado(empleado):
    """Muestra el detalle completo de un empleado"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Información Personal")
        st.write(f"**Nombre:** {empleado['nombre_completo']}")
        st.write(f"**Usuario:** {empleado['username']}")
        st.write(f"**DNI:** {empleado['dni']}")
        st.write(f"**Email:** {empleado['email']}")
        st.write(f"**Teléfono:** {empleado.get('telefono', 'N/A')}")
        
        st.markdown("### 💼 Información Laboral")
        st.write(f"**Cargo:** {empleado['cargo']}")
        st.write(f"**Departamento:** {empleado['departamento']}")
        st.write(f"**Fecha de Alta:** {empleado['fecha_alta'].strftime('%d/%m/%Y')}")
        st.write(f"**Estado:** {'🟢 Activo' if empleado['activo'] else '🔴 Inactivo'}")
    
    with col2:
        st.markdown("### 📱 Telegram")
        if empleado.get('telegram_id'):
            st.write(f"**ID:** {empleado['telegram_id']}")
            st.write(f"**Username:** {empleado.get('telegram_username', 'N/A')}")
            st.success("✅ Telegram vinculado")
        else:
            st.warning("⚠️ Telegram no vinculado")
            st.info("El empleado puede vincularse usando el comando /start en el bot de Telegram")
        
        st.markdown("### ⏰ Estadísticas de Fichaje")
        # Contar fichajes del empleado
        total_fichajes = db[FICHAJES_COLLECTION].count_documents({'username': empleado['username']})
        
        hoy = datetime.now().replace(hour=0, minute=0, second=0)
        fichajes_hoy = db[FICHAJES_COLLECTION].count_documents({
            'username': empleado['username'],
            'timestamp': {'$gte': hoy}
        })
        
        mes_actual = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        fichajes_mes = db[FICHAJES_COLLECTION].count_documents({
            'username': empleado['username'],
            'timestamp': {'$gte': mes_actual}
        })
        
        st.metric("Total Fichajes", total_fichajes)
        st.metric("Fichajes Hoy", fichajes_hoy)
        st.metric("Fichajes Este Mes", fichajes_mes)
    
    # Acciones sobre el empleado
    st.markdown("---")
    st.markdown("### ⚙️ Acciones")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Resetear Contraseña", use_container_width=True):
            nueva_password = "temporal123"
            db[USUARIOS_COLLECTION].update_one(
                {'_id': empleado['_id']},
                {'$set': {'password_hash': hash_password(nueva_password)}}
            )
            st.success(f"✅ Contraseña reseteada a: `{nueva_password}`")
    
    with col2:
        if empleado['activo']:
            if st.button("🚫 Desactivar Empleado", use_container_width=True, type="secondary"):
                db[USUARIOS_COLLECTION].update_one(
                    {'_id': empleado['_id']},
                    {'$set': {'activo': False}}
                )
                st.success("✅ Empleado desactivado")
                st.rerun()
        else:
            if st.button("✅ Activar Empleado", use_container_width=True, type="primary"):
                db[USUARIOS_COLLECTION].update_one(
                    {'_id': empleado['_id']},
                    {'$set': {'activo': True}}
                )
                st.success("✅ Empleado activado")
                st.rerun()
    
    with col3:
        if st.button("🗑️ Eliminar Empleado", use_container_width=True, type="secondary"):
            st.warning("⚠️ Esta acción no se puede deshacer. Usa 'Desactivar' en su lugar.")

# ========== FICHAJES ==========
def pagina_fichajes():
    """Página de gestión de fichajes"""
    st.markdown('<h1 class="main-header">⏰ Gestión de Fichajes</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Fichaje Manual", "📊 Historial de Fichajes"])
    
    with tab1:
        st.subheader("Registrar Fichaje Manual")
        st.info("💡 Usa esta opción para fichajes presenciales o correcciones manuales")
        
        with st.form("form_fichaje"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Obtener empleados activos
                empleados_activos = list(db[USUARIOS_COLLECTION].find({'activo': True}).sort('nombre_completo', 1))
                
                if not empleados_activos:
                    st.warning("⚠️ No hay empleados activos en el sistema")
                else:
                    empleados_dict = {
                        f"{emp['nombre_completo']} ({emp['username']})": emp 
                        for emp in empleados_activos
                    }
                    
                    empleado_seleccionado = st.selectbox(
                        "Seleccionar Empleado *",
                        options=list(empleados_dict.keys())
                    )
            
            with col2:
                tipo_fichaje = st.radio(
                    "Tipo de Fichaje *",
                    ["Entrada", "Salida"],
                    horizontal=True
                )
            
            # Fecha y hora (por defecto ahora)
            col1, col2 = st.columns(2)
            with col1:
                fecha_fichaje = st.date_input("Fecha", datetime.now())
            with col2:
                hora_fichaje = st.time_input("Hora", datetime.now().time())
            
            observaciones = st.text_area("Observaciones (opcional)", placeholder="Motivo del fichaje manual")
            
            submitted = st.form_submit_button("✅ Registrar Fichaje", use_container_width=True, type="primary")
            
            if submitted and empleados_activos:
                empleado = empleados_dict[empleado_seleccionado]
                
                # Combinar fecha y hora
                timestamp = datetime.combine(fecha_fichaje, hora_fichaje)
                
                fichaje = {
                    'user_id': str(empleado['_id']),
                    'username': empleado['username'],
                    'nombre_completo': empleado['nombre_completo'],
                    'tipo': tipo_fichaje.lower(),
                    'timestamp': timestamp,
                    'fecha': timestamp.strftime("%Y-%m-%d"),
                    'hora': timestamp.strftime("%H:%M:%S"),
                    'dia_semana': timestamp.strftime("%A"),
                    'departamento': empleado.get('departamento'),
                    'origen': 'manual_admin',
                    'registrado_por': st.session_state.admin['usuario'],
                    'observaciones': observaciones if observaciones else None
                }
                
                try:
                    db[FICHAJES_COLLECTION].insert_one(fichaje)
                    st.success(f"✅ Fichaje de **{tipo_fichaje}** registrado para **{empleado['nombre_completo']}**")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error al registrar fichaje: {str(e)}")
    
    with tab2:
        st.subheader("Historial de Fichajes")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            fecha_desde = st.date_input("Desde", datetime.now() - timedelta(days=7))
        with col2:
            fecha_hasta = st.date_input("Hasta", datetime.now())
        with col3:
            tipo_filtro = st.selectbox("Tipo", ["Todos", "Entrada", "Salida"])
        with col4:
            buscar_empleado = st.text_input("🔍 Empleado")
        
        # Construir query
        query = {
            'timestamp': {
                '$gte': datetime.combine(fecha_desde, datetime.min.time()),
                '$lte': datetime.combine(fecha_hasta, datetime.max.time())
            }
        }
        
        if tipo_filtro != "Todos":
            query['tipo'] = tipo_filtro.lower()
        
        if buscar_empleado:
            query['$or'] = [
                {'nombre_completo': {'$regex': buscar_empleado, '$options': 'i'}},
                {'username': {'$regex': buscar_empleado, '$options': 'i'}}
            ]
        
        # Obtener fichajes
        fichajes = list(db[FICHAJES_COLLECTION].find(query).sort('timestamp', -1).limit(500))
        
        if fichajes:
            df = pd.DataFrame(fichajes)
            
            # Formatear datos
            df['fecha_hora'] = pd.to_datetime(df['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
            df['tipo_fmt'] = df['tipo'].apply(lambda x: '🟢 ENTRADA' if x == 'entrada' else '🔴 SALIDA')
            df['origen_fmt'] = df.get('origen', 'desconocido').fillna('telegram')
            
            # Seleccionar columnas
            columnas = ['fecha_hora', 'nombre_completo', 'username', 'tipo_fmt', 'origen_fmt']
            if 'departamento' in df.columns:
                columnas.append('departamento')
            
            df_display = df[columnas]
            nombres_columnas = ['Fecha y Hora', 'Nombre', 'Usuario', 'Tipo', 'Origen']
            if 'departamento' in df.columns:
                nombres_columnas.append('Departamento')
            df_display.columns = nombres_columnas
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Estadísticas
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Fichajes", len(fichajes))
            with col2:
                entradas = len([f for f in fichajes if f['tipo'] == 'entrada'])
                st.metric("Entradas", entradas)
            with col3:
                salidas = len([f for f in fichajes if f['tipo'] == 'salida'])
                st.metric("Salidas", salidas)
            with col4:
                empleados_unicos = df['username'].nunique()
                st.metric("Empleados", empleados_unicos)
            
            # Descargar CSV
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Fichajes CSV",
                data=csv,
                file_name=f"fichajes_{fecha_desde}_{fecha_hasta}.csv",
                mime="text/csv"
            )
        else:
            st.info("📭 No hay fichajes en el rango seleccionado")

# ========== REPORTES ==========
def pagina_reportes():
    """Página de reportes y estadísticas"""
    st.markdown('<h1 class="main-header">📊 Reportes y Estadísticas</h1>', unsafe_allow_html=True)
    
    # Selector de período
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input("Desde", datetime.now() - timedelta(days=30))
    with col2:
        fecha_hasta = st.date_input("Hasta", datetime.now())
    
    fecha_inicio = datetime.combine(fecha_desde, datetime.min.time())
    fecha_fin = datetime.combine(fecha_hasta, datetime.max.time())
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Fichajes por Día")
        
        fichajes = list(db[FICHAJES_COLLECTION].find({
            'timestamp': {'$gte': fecha_inicio, '$lte': fecha_fin}
        }))
        
        if fichajes:
            df = pd.DataFrame(fichajes)
            df['dia'] = pd.to_datetime(df['timestamp']).dt.date
            fichajes_por_dia = df.groupby('dia').size().reset_index(name='cantidad')
            fichajes_por_dia.columns = ['Día', 'Fichajes']
            
            st.line_chart(fichajes_por_dia.set_index('Día'), use_container_width=True)
        else:
            st.info("No hay datos suficientes")
    
    with col2:
        st.subheader("👥 Empleados por Departamento")
        
        empleados = list(db[USUARIOS_COLLECTION].find({'activo': True}))
        
        if empleados:
            df = pd.DataFrame(empleados)
            if 'departamento' in df.columns and not df['departamento'].isna().all():
                dept_count = df['departamento'].value_counts()
                st.bar_chart(dept_count)
            else:
                st.info("No hay información de departamentos")
        else:
            st.info("No hay empleados registrados")
    
    st.markdown("---")
    
    # Resumen general del período
    st.subheader(f"📋 Resumen del Período ({fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')})")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_fichajes = db[FICHAJES_COLLECTION].count_documents({
        'timestamp': {'$gte': fecha_inicio, '$lte': fecha_fin}
    })
    
    entradas = db[FICHAJES_COLLECTION].count_documents({
        'timestamp': {'$gte': fecha_inicio, '$lte': fecha_fin},
        'tipo': 'entrada'
    })
    
    salidas = db[FICHAJES_COLLECTION].count_documents({
        'timestamp': {'$gte': fecha_inicio, '$lte': fecha_fin},
        'tipo': 'salida'
    })
    
    # Empleados que han fichado
    fichajes_periodo = list(db[FICHAJES_COLLECTION].find({
        'timestamp': {'$gte': fecha_inicio, '$lte': fecha_fin}
    }))
    empleados_activos = len(set(f['username'] for f in fichajes_periodo)) if fichajes_periodo else 0
    
    with col1:
        st.metric("Total Fichajes", total_fichajes)
    with col2:
        st.metric("🟢 Entradas", entradas)
    with col3:
        st.metric("🔴 Salidas", salidas)
    with col4:
        st.metric("👤 Empleados Activos", empleados_activos)
    
    # Top 10 empleados con más fichajes
    st.markdown("---")
    st.subheader("🏆 Top 10 Empleados con Más Fichajes")
    
    if fichajes_periodo:
        df_top = pd.DataFrame(fichajes_periodo)
        top_empleados = df_top.groupby(['nombre_completo', 'username']).size().reset_index(name='fichajes')
        top_empleados = top_empleados.sort_values('fichajes', ascending=False).head(10)
        top_empleados['nombre'] = top_empleados['nombre_completo'] + ' (' + top_empleados['username'] + ')'
        
        chart_data = top_empleados.set_index('nombre')['fichajes']
        st.bar_chart(chart_data)
    else:
        st.info("No hay datos para mostrar")

# ========== CONFIGURACIÓN ==========
def pagina_configuracion():
    """Página de configuración del sistema"""
    st.markdown('<h1 class="main-header">⚙️ Configuración del Sistema</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔐 Mi Cuenta", "🤖 Telegram", "💾 Base de Datos"])
    
    with tab1:
        st.subheader("Información de la Cuenta")
        
        admin = st.session_state.admin
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Usuario:** {admin['usuario']}")
            st.write(f"**Nombre:** {admin['nombre']}")
            st.write(f"**Email:** {admin.get('email', 'N/A')}")
            st.write(f"**Rol:** {admin.get('rol', 'admin').upper()}")
        
        with col2:
            if 'fecha_creacion' in admin:
                st.write(f"**Cuenta creada:** {admin['fecha_creacion'].strftime('%d/%m/%Y')}")
        
        st.markdown("---")
        st.subheader("🔄 Cambiar Contraseña")
        
        with st.form("cambiar_password"):
            password_actual = st.text_input("Contraseña Actual", type="password")
            password_nueva = st.text_input("Nueva Contraseña", type="password")
            password_confirmar = st.text_input("Confirmar Nueva Contraseña", type="password")
            
            if st.form_submit_button("Cambiar Contraseña", type="primary"):
                if not password_actual or not password_nueva or not password_confirmar:
                    st.error("❌ Completa todos los campos")
                elif password_nueva != password_confirmar:
                    st.error("❌ Las contraseñas nuevas no coinciden")
                elif len(password_nueva) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres")
                elif not verificar_password(password_actual, admin['password_hash']):
                    st.error("❌ Contraseña actual incorrecta")
                else:
                    # Cambiar contraseña
                    db['administradores'].update_one(
                        {'_id': admin['_id']},
                        {'$set': {'password_hash': hash_password(password_nueva)}}
                    )
                    st.success("✅ Contraseña cambiada correctamente")
    
    with tab2:
        st.subheader("🤖 Configuración de Telegram Bot")
        
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        telegram_enabled = os.getenv("TELEGRAM_ENABLED", "False").lower() == "true"
        
        if telegram_token:
            st.success(f"✅ Bot configurado")
            st.code(f"Token: {telegram_token[:10]}..." if len(telegram_token) > 10 else telegram_token)
            
            if telegram_enabled:
                st.info("🟢 Bot activo y funcionando")
            else:
                st.warning("⚠️ Bot configurado pero no habilitado")
        else:
            st.warning("⚠️ Bot de Telegram no configurado")
            st.info("Configura el token en el archivo .env:\n```\nTELEGRAM_TOKEN=tu_token_aqui\nTELEGRAM_ENABLED=True\n```")
        
        st.markdown("---")
        st.subheader("📊 Estadísticas de Telegram")
        
        empleados_con_telegram = db[USUARIOS_COLLECTION].count_documents({
            'telegram_id': {'$exists': True, '$ne': None},
            'activo': True
        })
        
        total_empleados = db[USUARIOS_COLLECTION].count_documents({'activo': True})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Empleados con Telegram", empleados_con_telegram)
        with col2:
            porcentaje = (empleados_con_telegram / total_empleados * 100) if total_empleados > 0 else 0
            st.metric("% de Vinculación", f"{porcentaje:.1f}%")
    
    with tab3:
        st.subheader("💾 Información de Base de Datos")
        
        if db:
            st.success("✅ Conectado a MongoDB")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Base de datos:** {DATABASE_NAME}")
                st.write(f"**URI:** {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI}")
            
            with col2:
                total_usuarios = db[USUARIOS_COLLECTION].count_documents({})
                total_fichajes = db[FICHAJES_COLLECTION].count_documents({})
                
                st.metric("Total Usuarios", total_usuarios)
                st.metric("Total Fichajes", total_fichajes)
            
            st.markdown("---")
            st.subheader("📊 Estadísticas de Colecciones")
            
            # Información de colecciones
            colecciones = db.list_collection_names()
            st.write(f"**Colecciones disponibles:** {', '.join(colecciones)}")
        else:
            st.error("❌ No se puede conectar con la base de datos")

# ========== MAIN ==========
def main():
    """Función principal de la aplicación"""
    if not st.session_state.logged_in:
        mostrar_login()
    else:
        mostrar_dashboard()

if __name__ == "__main__":
    main()
