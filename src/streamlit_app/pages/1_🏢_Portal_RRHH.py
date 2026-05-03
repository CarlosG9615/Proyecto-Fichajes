"""
Portal de Recursos Humanos
Acceso exclusivo para administradores
"""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from bson import ObjectId

from streamlit_app.utils.auth import (
    inicializar_sesion, 
    autenticar_usuario, 
    login_usuario, 
    logout_usuario,
    requiere_admin,
    hash_password,
    password_cumple_politica,
    actualizar_password_usuario
)
from streamlit_app.utils.database import (
    get_usuarios_collection,
    get_fichajes_collection
)
from streamlit_app.utils.helpers import (
    validar_email,
    validar_username,
    formatear_fecha,
    crear_dataframe_fichajes,
    obtener_saludo
)

# Configuración de la página
st.set_page_config(
    page_title="Portal RRHH",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar sesión
inicializar_sesion()

# Estilos CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

def mostrar_login():
    """Página de login para RRHH"""
    st.markdown("## 🏢 Portal de Recursos Humanos")
    st.markdown("### Acceso exclusivo para administradores")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔐 Iniciar Sesión")
            username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submit = st.form_submit_button("✅ Ingresar", use_container_width=True, type="primary")
            
            with col_btn2:
                volver = st.form_submit_button("🔙 Volver", use_container_width=True)
            
            if volver:
                st.switch_page("app.py")
            
            if submit:
                if not username or not password:
                    st.error("❌ Por favor, completa todos los campos")
                else:
                    usuario = autenticar_usuario(username, password)
                    
                    if usuario:
                        # Verificar que sea administrador
                        if usuario.get("rol") != "admin":
                            st.error("❌ No tienes permisos de administrador")
                        else:
                            login_usuario(usuario)
                            st.session_state.password_change_required = bool(usuario.get("password_change_required", False))
                            st.success(f"✅ Bienvenido, {usuario.get('nombre_completo', username)}!")
                            st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
        
        st.info("💡 Solo los usuarios con rol **administrador** pueden acceder a este portal")

def mostrar_dashboard():
    """Dashboard principal de RRHH"""
    st.title(f"🏠 {obtener_saludo()}, {st.session_state.usuario.get('nombre_completo', 'Administrador')}")
    
    # Estadísticas principales
    usuarios_col = get_usuarios_collection()
    fichajes_col = get_fichajes_collection()
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_usuarios = usuarios_col.count_documents({"activo": True})
    total_inactivos = usuarios_col.count_documents({"activo": False})
    
    # Fichajes de hoy
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fichajes_hoy = fichajes_col.count_documents({"timestamp": {"$gte": hoy_inicio}})
    
    # Usuarios con Telegram
    con_telegram = usuarios_col.count_documents({"telegram_id": {"$ne": None}})
    
    with col1:
        st.metric("👥 Usuarios Activos", total_usuarios)
    
    with col2:
        st.metric("⏰ Fichajes Hoy", fichajes_hoy)
    
    with col3:
        st.metric("📱 Con Telegram", con_telegram)
    
    with col4:
        st.metric("🚫 Inactivos", total_inactivos)
    
    st.markdown("---")
    
    # Últimos fichajes
    st.subheader("📋 Últimos Fichajes Registrados")
    
    ultimos_fichajes = list(fichajes_col.find().sort("timestamp", -1).limit(15))
    
    if ultimos_fichajes:
        # Enriquecer con datos de usuario
        for fichaje in ultimos_fichajes:
            fichaje["nombre"] = "Desconocido"
            fichaje["username"] = "N/A"
            user_id = fichaje.get("usuario_id")
            if user_id:
                try:
                    usuario = usuarios_col.find_one({"_id": ObjectId(user_id)})
                    if usuario:
                        fichaje["nombre"] = usuario.get("nombre_completo", "Desconocido")
                        fichaje["username"] = usuario.get("username", "N/A")
                    else:
                        fichaje["nombre"] = "Usuario eliminado"
                except Exception:
                    fichaje["nombre"] = "Usuario no válido"
        
        df = pd.DataFrame(ultimos_fichajes)
        
        if not df.empty:
            # Formatear columnas
            df["fecha"] = pd.to_datetime(df["timestamp"]).dt.strftime("%d/%m/%Y %H:%M:%S")
            df["tipo"] = df["tipo"].str.upper()
            df["nombre"] = df.get("nombre", pd.Series("Desconocido", index=df.index)).fillna("Desconocido")
            df["username"] = df.get("username", pd.Series("N/A", index=df.index)).fillna("N/A")
            
            # Seleccionar columnas para mostrar
            columnas_mostrar = ["fecha", "nombre", "username", "tipo"]
            df_display = df[columnas_mostrar]
            df_display.columns = ["Fecha y Hora", "Nombre", "Usuario", "Tipo"]
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No hay fichajes registrados todavía")

def mostrar_crear_usuario():
    """Página para crear nuevos usuarios"""
    st.title("➕ Crear Nuevo Usuario")
    
    with st.form("form_crear_usuario"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 Información Personal")
            username = st.text_input("Username *", placeholder="usuario123")
            nombre_completo = st.text_input("Nombre Completo *", placeholder="Juan Pérez García")
            email = st.text_input("Email *", placeholder="juan.perez@empresa.com")
            departamento = st.text_input("Departamento *", placeholder="IT, Ventas, RRHH...")
        
        with col2:
            st.markdown("### 🔐 Configuración de Acceso")
            password = st.text_input("Contraseña *", type="password", placeholder="Mínimo 12 caracteres, mayúscula, minúscula, número y símbolo")
            password_confirm = st.text_input("Confirmar Contraseña *", type="password")
            rol = st.selectbox("Rol *", ["user", "admin"], 
                             format_func=lambda x: "👤 Usuario" if x == "user" else "👑 Administrador")
            telegram_id = st.text_input("Telegram ID (opcional)", placeholder="123456789")
        
        st.markdown("---")
        
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        
        with col_btn2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        with col_btn3:
            submit = st.form_submit_button("✅ Crear Usuario", use_container_width=True, type="primary")
        
        if submit:
            # Validaciones
            errores = []
            
            if not all([username, nombre_completo, email, departamento, password, password_confirm]):
                errores.append("Todos los campos obligatorios (*) deben ser completados")
            
            if not validar_username(username):
                errores.append("El username debe tener entre 3-50 caracteres y solo letras, números y guión bajo")
            
            if not validar_email(email):
                errores.append("El formato del email no es válido")
            
            if len(password) < 12:
                errores.append("La contraseña debe tener al menos 12 caracteres")

            valida_password, errores_password = password_cumple_politica(password)
            if not valida_password:
                errores.extend(errores_password)
            
            if password != password_confirm:
                errores.append("Las contraseñas no coinciden")
            
            # Verificar si el username ya existe
            usuarios_col = get_usuarios_collection()
            if usuarios_col.find_one({"username": username}):
                errores.append(f"El username '{username}' ya está en uso")
            
            # Verificar si el email ya existe
            if usuarios_col.find_one({"email": email}):
                errores.append(f"El email '{email}' ya está registrado")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                # Crear usuario
                nuevo_usuario = {
                    "username": username,
                    "nombre_completo": nombre_completo,
                    "email": email,
                    "departamento": departamento,
                    "rol": rol,
                    "password_hash": hash_password(password),
                    "password_change_required": False,
                    "activo": True,
                    "telegram_id": int(telegram_id) if telegram_id else None,
                    "creado_en": datetime.now(),
                    "creado_por": st.session_state.user_id
                }
                
                try:
                    result = usuarios_col.insert_one(nuevo_usuario)
                    st.success(f"✅ Usuario '{username}' creado exitosamente!")
                    st.balloons()
                    
                    # Mostrar información del usuario creado
                    st.info(f"""
                    **Usuario creado:**
                    - Username: {username}
                    - Nombre: {nombre_completo}
                    - Email: {email}
                    - Rol: {'Administrador' if rol == 'admin' else 'Usuario'}
                    - Telegram: {'Vinculado' if telegram_id else 'No vinculado'}
                    """)
                except Exception as e:
                    st.error(f"❌ Error al crear usuario: {str(e)}")


def mostrar_cambio_password_obligatorio():
    """Solicita el cambio de contraseña antes de permitir el acceso completo."""
    st.title("🔒 Cambio obligatorio de contraseña")
    st.warning("Tu usuario debe actualizar la contraseña para cumplir con la política de seguridad.")
    st.markdown("La nueva contraseña debe tener al menos 12 caracteres, mayúsculas, minúsculas, números y símbolos.")

    with st.form("form_cambio_password_obligatorio"):
        nueva_password = st.text_input("Nueva contraseña *", type="password")
        confirmar_password = st.text_input("Confirmar nueva contraseña *", type="password")

        submit = st.form_submit_button("✅ Actualizar contraseña", use_container_width=True, type="primary")

        if submit:
            if not nueva_password or not confirmar_password:
                st.error("❌ Completa todos los campos")
                return

            if nueva_password != confirmar_password:
                st.error("❌ Las contraseñas no coinciden")
                return

            valida_password, errores_password = password_cumple_politica(nueva_password)
            if not valida_password:
                for error in errores_password:
                    st.error(f"❌ {error}")
                return

            ok, mensaje = actualizar_password_usuario(st.session_state.user_id, nueva_password)
            if ok:
                st.session_state.password_change_required = False
                if st.session_state.usuario is not None:
                    st.session_state.usuario["password_change_required"] = False
                st.success(mensaje)
                st.rerun()
            else:
                st.error(f"❌ {mensaje}")

def mostrar_lista_usuarios():
    """Página para listar y gestionar usuarios"""
    st.title("👥 Lista de Usuarios")
    
    # Filtros
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        filtro_activo = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"])
    
    with col_filtro2:
        filtro_rol = st.selectbox("Rol", ["Todos", "Administradores", "Usuarios"])
    
    with col_filtro3:
        filtro_telegram = st.selectbox("Telegram", ["Todos", "Con Telegram", "Sin Telegram"])
    
    # Construir query
    query = {}
    
    if filtro_activo == "Activos":
        query["activo"] = True
    elif filtro_activo == "Inactivos":
        query["activo"] = False
    
    if filtro_rol == "Administradores":
        query["rol"] = "admin"
    elif filtro_rol == "Usuarios":
        query["rol"] = "user"
    
    if filtro_telegram == "Con Telegram":
        query["telegram_id"] = {"$ne": None}
    elif filtro_telegram == "Sin Telegram":
        query["telegram_id"] = None
    
    # Obtener usuarios
    usuarios_col = get_usuarios_collection()
    usuarios = list(usuarios_col.find(query).sort("creado_en", -1))
    
    st.markdown(f"**Total de usuarios encontrados: {len(usuarios)}**")
    st.markdown("---")
    
    if usuarios:
        for usuario in usuarios:
            with st.expander(f"{'👑' if usuario.get('rol') == 'admin' else '👤'} {usuario.get('nombre_completo')} (@{usuario.get('username')})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Email:** {usuario.get('email')}")
                    st.write(f"**Departamento:** {usuario.get('departamento')}")
                    st.write(f"**Rol:** {'Administrador' if usuario.get('rol') == 'admin' else 'Usuario'}")
                
                with col2:
                    st.write(f"**Estado:** {'✅ Activo' if usuario.get('activo') else '❌ Inactivo'}")
                    telegram = usuario.get('telegram_id')
                    st.write(f"**Telegram:** {f'📱 {telegram}' if telegram else '❌ No vinculado'}")
                    creado = usuario.get('creado_en')
                    if creado:
                        st.write(f"**Creado:** {formatear_fecha(creado)}")
                
                with col3:
                    # Acciones
                    if usuario.get('activo'):
                        if st.button(f"🚫 Desactivar", key=f"desactivar_{usuario['_id']}"):
                            usuarios_col.update_one(
                                {"_id": usuario['_id']},
                                {"$set": {"activo": False}}
                            )
                            st.success("Usuario desactivado")
                            st.rerun()
                    else:
                        if st.button(f"✅ Activar", key=f"activar_{usuario['_id']}"):
                            usuarios_col.update_one(
                                {"_id": usuario['_id']},
                                {"$set": {"activo": True}}
                            )
                            st.success("Usuario activado")
                            st.rerun()
    else:
        st.info("ℹ️ No se encontraron usuarios con los filtros seleccionados")

def mostrar_reportes():
    """Página de reportes y estadísticas"""
    st.title("📊 Reportes y Estadísticas")
    
    usuarios_col = get_usuarios_collection()
    fichajes_col = get_fichajes_collection()
    
    # Selector de rango de fechas
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("Fecha Inicio", datetime.now() - timedelta(days=30))
    
    with col2:
        fecha_fin = st.date_input("Fecha Fin", datetime.now())
    
    # Convertir a datetime
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    
    st.markdown("---")
    
    # Estadísticas del período
    st.subheader(f"📈 Estadísticas del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}")
    
    fichajes_periodo = list(fichajes_col.find({
        "timestamp": {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
    }))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Fichajes", len(fichajes_periodo))
    
    with col2:
        entradas = len([f for f in fichajes_periodo if f.get("tipo") == "entrada"])
        st.metric("🟢 Entradas", entradas)
    
    with col3:
        salidas = len([f for f in fichajes_periodo if f.get("tipo") == "salida"])
        st.metric("🔴 Salidas", salidas)
    
    with col4:
        usuarios_ficharon = len(set([f.get("usuario_id") for f in fichajes_periodo if f.get("usuario_id")]))
        st.metric("👥 Usuarios Activos", usuarios_ficharon)
    
    # Gráfico de fichajes por día
    if fichajes_periodo:
        st.markdown("---")
        st.subheader("📊 Fichajes por Día")
        
        df = pd.DataFrame(fichajes_periodo)
        df["fecha"] = pd.to_datetime(df["timestamp"]).dt.date
        fichajes_por_dia = df.groupby("fecha").size().reset_index(name="cantidad")
        
        st.bar_chart(fichajes_por_dia.set_index("fecha"))
        
        # Tabla de fichajes
        st.markdown("---")
        st.subheader("📋 Detalle de Fichajes")
        
        # Enriquecer con datos de usuario
        for fichaje in fichajes_periodo:
            user_id = fichaje.get("usuario_id")
            if user_id:
                usuario = usuarios_col.find_one({"_id": ObjectId(user_id)})
                if usuario:
                    fichaje["nombre"] = usuario.get("nombre_completo", "Desconocido")
                    fichaje["username"] = usuario.get("username", "N/A")
        
        df_display = pd.DataFrame(fichajes_periodo)
        if not df_display.empty and "timestamp" in df_display.columns:
            df_display["fecha"] = pd.to_datetime(df_display["timestamp"]).dt.strftime("%d/%m/%Y %H:%M:%S")
            df_display["tipo"] = df_display["tipo"].str.upper()
            
            columnas = ["fecha", "nombre", "username", "tipo"]
            df_final = df_display[columnas]
            df_final.columns = ["Fecha y Hora", "Nombre", "Usuario", "Tipo"]
            
            st.dataframe(df_final, use_container_width=True, hide_index=True)

def main():
    """Función principal"""
    # Verificar autenticación
    if not st.session_state.get('logged_in', False):
        mostrar_login()
        return
    
    # Verificar que sea administrador
    if not requiere_admin():
        st.error("❌ No tienes permisos de administrador para acceder a este portal")
        if st.button("🔙 Volver"):
            st.switch_page("app.py")
        return

    if st.session_state.get("password_change_required", False):
        mostrar_cambio_password_obligatorio()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 {obtener_saludo()}")
        st.markdown(f"**{st.session_state.usuario.get('nombre_completo')}**")
        st.markdown(f"*{st.session_state.usuario.get('email')}*")
        st.markdown("---")
        
        # Menú de navegación
        menu = st.radio(
            "📋 Menú",
            ["🏠 Dashboard", "➕ Crear Usuario", "👥 Lista de Usuarios", "📊 Reportes"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_usuario()
            st.rerun()
        
        if st.button("🏠 Ir a Inicio", use_container_width=True):
            st.switch_page("app.py")
    
    # Contenido según menú
    if menu == "🏠 Dashboard":
        mostrar_dashboard()
    elif menu == "➕ Crear Usuario":
        mostrar_crear_usuario()
    elif menu == "👥 Lista de Usuarios":
        mostrar_lista_usuarios()
    elif menu == "📊 Reportes":
        mostrar_reportes()

if __name__ == "__main__":
    main()
