"""
Portal de Empleados
Gestión de fichajes personal
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta, time
import pandas as pd
from bson import ObjectId

# Añadir el directorio padre al path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.auth import (
    inicializar_sesion, 
    autenticar_usuario, 
    login_usuario, 
    logout_usuario,
        requiere_autenticacion,
        password_cumple_politica,
        actualizar_password_usuario
)
from utils.database import (
    get_usuarios_collection,
    get_fichajes_collection
)
from utils.helpers import (
    formatear_fecha,
    formatear_fecha_corta,
    calcular_horas_trabajadas,
    obtener_saludo
)

# Configuración de la página
st.set_page_config(
    page_title="Portal Empleado",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar sesión
inicializar_sesion()

# Estilos CSS
st.markdown("""
<style>
    .fichaje-entrada {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .fichaje-salida {
        background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .fichaje-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .fichaje-time {
        font-size: 3rem;
        font-weight: bold;
    }
    .stat-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

def mostrar_login():
    """Página de login para empleados"""
    st.markdown("## 👤 Portal de Empleados")
    st.markdown("### Gestiona tus fichajes")
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
                        login_usuario(usuario)
                        st.session_state.password_change_required = bool(usuario.get("password_change_required", False))
                        st.success(f"✅ Bienvenido, {usuario.get('nombre_completo', username)}!")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
        
        st.info("💡 Todos los empleados pueden acceder a este portal para gestionar sus fichajes")

def registrar_fichaje(tipo: str, usuario_id: str):
    """Registra un fichaje de entrada o salida"""
    fichajes_col = get_fichajes_collection()
    
    # Verificar si ya hay un fichaje del mismo tipo hoy
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    ultimo_fichaje = fichajes_col.find_one(
        {"usuario_id": usuario_id},
        sort=[("timestamp", -1)]
    )
    
    # Validación: No puede haber dos entradas seguidas o dos salidas seguidas
    if ultimo_fichaje:
        ultimo_tipo = ultimo_fichaje.get("tipo")
        if ultimo_tipo == tipo:
            mensaje_tipo = "entrada" if tipo == "entrada" else "salida"
            st.error(f"❌ Ya registraste una {mensaje_tipo}. Debes registrar una {'salida' if tipo == 'entrada' else 'entrada'} primero.")
            return False
    
    # Registrar el fichaje
    nuevo_fichaje = {
        "usuario_id": usuario_id,
        "tipo": tipo,
        "timestamp": datetime.now(),
        "origen": "streamlit",
        "latitud": None,
        "longitud": None
    }
    
    try:
        fichajes_col.insert_one(nuevo_fichaje)
        return True
    except Exception as e:
        st.error(f"❌ Error al registrar fichaje: {str(e)}")
        return False

def mostrar_fichar():
    """Página principal para fichar entrada/salida"""
    st.title(f"⏰ {obtener_saludo()}, {st.session_state.usuario.get('nombre_completo')}")
    
    # Obtener último fichaje
    fichajes_col = get_fichajes_collection()
    ultimo_fichaje = fichajes_col.find_one(
        {"usuario_id": st.session_state.user_id},
        sort=[("timestamp", -1)]
    )
    
    # Mostrar hora actual
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Reloj actual
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        border-radius: 15px; color: white; margin-bottom: 2rem;'>
            <h2>🕐 {datetime.now().strftime('%H:%M:%S')}</h2>
            <p style='font-size: 1.2rem;'>{datetime.now().strftime('%A, %d de %B de %Y')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Estado actual
        if ultimo_fichaje:
            tipo_ultimo = ultimo_fichaje.get("tipo")
            timestamp_ultimo = ultimo_fichaje.get("timestamp")
            
            if tipo_ultimo == "entrada":
                st.success(f"✅ Última **ENTRADA** registrada: {formatear_fecha(timestamp_ultimo)}")
                siguiente_accion = "salida"
                color_btn = "🔴"
                texto_btn = "Registrar SALIDA"
            else:
                st.info(f"ℹ️ Última **SALIDA** registrada: {formatear_fecha(timestamp_ultimo)}")
                siguiente_accion = "entrada"
                color_btn = "🟢"
                texto_btn = "Registrar ENTRADA"
        else:
            st.info("ℹ️ No has registrado fichajes todavía")
            siguiente_accion = "entrada"
            color_btn = "🟢"
            texto_btn = "Registrar ENTRADA"
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón para fichar
        if st.button(f"{color_btn} {texto_btn}", use_container_width=True, type="primary", key="btn_fichar"):
            if registrar_fichaje(siguiente_accion, st.session_state.user_id):
                st.success(f"✅ {texto_btn} registrado exitosamente a las {datetime.now().strftime('%H:%M:%S')}")
                st.balloons()
                st.rerun()
    
    # Resumen de fichajes de hoy
    st.markdown("---")
    st.subheader("📋 Fichajes de Hoy")
    
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    fichajes_hoy = list(fichajes_col.find({
        "usuario_id": st.session_state.user_id,
        "timestamp": {"$gte": hoy_inicio, "$lte": hoy_fin}
    }).sort("timestamp", 1))
    
    if fichajes_hoy:
        col1, col2 = st.columns(2)
        
        with col1:
            entradas_hoy = [f for f in fichajes_hoy if f.get("tipo") == "entrada"]
            st.metric("🟢 Entradas", len(entradas_hoy))
            
            for entrada in entradas_hoy:
                st.success(f"⏰ {formatear_fecha(entrada.get('timestamp'))}")
        
        with col2:
            salidas_hoy = [f for f in fichajes_hoy if f.get("tipo") == "salida"]
            st.metric("🔴 Salidas", len(salidas_hoy))
            
            for salida in salidas_hoy:
                st.error(f"⏰ {formatear_fecha(salida.get('timestamp'))}")
        
        # Calcular horas trabajadas hoy
        if len(entradas_hoy) > 0 and len(salidas_hoy) > 0:
            total_horas = 0
            for i in range(min(len(entradas_hoy), len(salidas_hoy))):
                entrada_time = entradas_hoy[i].get("timestamp")
                salida_time = salidas_hoy[i].get("timestamp")
                if entrada_time and salida_time:
                    total_horas += calcular_horas_trabajadas(entrada_time, salida_time)
            
            st.info(f"⏱️ **Horas trabajadas hoy:** {total_horas:.2f} horas")
    else:
        st.info("ℹ️ No has registrado fichajes hoy")


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

def mostrar_historial():
    """Página de historial de fichajes"""
    st.title("📚 Historial de Fichajes")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("Desde", datetime.now() - timedelta(days=30))
    
    with col2:
        fecha_fin = st.date_input("Hasta", datetime.now())
    
    # Convertir a datetime
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    
    # Obtener fichajes
    fichajes_col = get_fichajes_collection()
    fichajes = list(fichajes_col.find({
        "usuario_id": st.session_state.user_id,
        "timestamp": {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
    }).sort("timestamp", -1))
    
    st.markdown(f"**Total de fichajes: {len(fichajes)}**")
    st.markdown("---")
    
    if fichajes:
        # Estadísticas del período
        col1, col2, col3 = st.columns(3)
        
        entradas = len([f for f in fichajes if f.get("tipo") == "entrada"])
        salidas = len([f for f in fichajes if f.get("tipo") == "salida"])
        
        # Calcular horas totales
        fichajes_por_dia = {}
        for fichaje in fichajes:
            fecha = fichaje.get("timestamp").date()
            if fecha not in fichajes_por_dia:
                fichajes_por_dia[fecha] = {"entradas": [], "salidas": []}
            
            if fichaje.get("tipo") == "entrada":
                fichajes_por_dia[fecha]["entradas"].append(fichaje.get("timestamp"))
            else:
                fichajes_por_dia[fecha]["salidas"].append(fichaje.get("timestamp"))
        
        total_horas = 0
        for fecha, data in fichajes_por_dia.items():
            for i in range(min(len(data["entradas"]), len(data["salidas"]))):
                total_horas += calcular_horas_trabajadas(data["entradas"][i], data["salidas"][i])
        
        with col1:
            st.metric("🟢 Entradas", entradas)
        
        with col2:
            st.metric("🔴 Salidas", salidas)
        
        with col3:
            st.metric("⏱️ Horas Totales", f"{total_horas:.2f}h")
        
        st.markdown("---")
        
        # Tabla de fichajes
        df = pd.DataFrame(fichajes)
        df["fecha"] = pd.to_datetime(df["timestamp"]).dt.strftime("%d/%m/%Y %H:%M:%S")
        df["tipo"] = df["tipo"].str.upper()
        df["origen"] = df["origen"].str.upper()
        
        columnas = ["fecha", "tipo", "origen"]
        df_display = df[columnas]
        df_display.columns = ["Fecha y Hora", "Tipo", "Origen"]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Gráfico de fichajes por día
        st.markdown("---")
        st.subheader("📊 Fichajes por Día")
        
        df_grafico = df.copy()
        df_grafico["solo_fecha"] = pd.to_datetime(df["timestamp"]).dt.date
        fichajes_por_dia_df = df_grafico.groupby("solo_fecha").size().reset_index(name="cantidad")
        
        st.bar_chart(fichajes_por_dia_df.set_index("solo_fecha"))
    else:
        st.info("ℹ️ No hay fichajes en el rango de fechas seleccionado")

def mostrar_estadisticas():
    """Página de estadísticas personales"""
    st.title("📊 Mis Estadísticas")
    
    fichajes_col = get_fichajes_collection()
    
    # Estadísticas generales
    total_fichajes = fichajes_col.count_documents({"usuario_id": st.session_state.user_id})
    
    # Fichajes este mes
    primer_dia_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fichajes_mes = fichajes_col.count_documents({
        "usuario_id": st.session_state.user_id,
        "timestamp": {"$gte": primer_dia_mes}
    })
    
    # Fichajes esta semana
    hoy = datetime.now()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    fichajes_semana = fichajes_col.count_documents({
        "usuario_id": st.session_state.user_id,
        "timestamp": {"$gte": inicio_semana}
    })
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Total Fichajes", total_fichajes)
    
    with col2:
        st.metric("📅 Este Mes", fichajes_mes)
    
    with col3:
        st.metric("📆 Esta Semana", fichajes_semana)
    
    st.markdown("---")
    
    # Promedio de horas por semana (últimas 4 semanas)
    st.subheader("⏱️ Horas Trabajadas - Últimas 4 Semanas")
    
    semanas_atras = []
    for i in range(4):
        inicio = inicio_semana - timedelta(weeks=i)
        fin = inicio + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        fichajes_semana_lista = list(fichajes_col.find({
            "usuario_id": st.session_state.user_id,
            "timestamp": {"$gte": inicio, "$lte": fin}
        }).sort("timestamp", 1))
        
        # Calcular horas
        entradas = [f.get("timestamp") for f in fichajes_semana_lista if f.get("tipo") == "entrada"]
        salidas = [f.get("timestamp") for f in fichajes_semana_lista if f.get("tipo") == "salida"]
        
        horas_semana = 0
        for j in range(min(len(entradas), len(salidas))):
            horas_semana += calcular_horas_trabajadas(entradas[j], salidas[j])
        
        semanas_atras.append({
            "semana": f"Semana {4-i}",
            "inicio": inicio.strftime("%d/%m"),
            "horas": round(horas_semana, 2)
        })
    
    df_semanas = pd.DataFrame(semanas_atras)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.bar_chart(df_semanas.set_index("semana")["horas"])
    
    with col2:
        st.dataframe(df_semanas, use_container_width=True, hide_index=True)
    
    # Información del usuario
    st.markdown("---")
    st.subheader("👤 Mi Información")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Nombre:** {st.session_state.usuario.get('nombre_completo')}")
        st.write(f"**Email:** {st.session_state.usuario.get('email')}")
        st.write(f"**Username:** {st.session_state.usuario.get('username')}")
    
    with col2:
        st.write(f"**Departamento:** {st.session_state.usuario.get('departamento')}")
        telegram = st.session_state.usuario.get('telegram_id')
        st.write(f"**Telegram:** {f'📱 Vinculado ({telegram})' if telegram else '❌ No vinculado'}")
        st.write(f"**Rol:** {'👑 Administrador' if st.session_state.usuario.get('rol') == 'admin' else '👤 Usuario'}")

def main():
    """Función principal"""
    # Verificar autenticación
    if not st.session_state.get('logged_in', False):
        mostrar_login()
        return

    if st.session_state.get("password_change_required", False):
        mostrar_cambio_password_obligatorio()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 {obtener_saludo()}")
        st.markdown(f"**{st.session_state.usuario.get('nombre_completo')}**")
        st.markdown(f"*{st.session_state.usuario.get('departamento')}*")
        st.markdown("---")
        
        # Menú de navegación
        menu = st.radio(
            "📋 Menú",
            ["⏰ Fichar", "📚 Historial", "📊 Estadísticas"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_usuario()
            st.rerun()
        
        if st.button("🏠 Ir a Inicio", use_container_width=True):
            st.switch_page("app.py")
    
    # Contenido según menú
    if menu == "⏰ Fichar":
        mostrar_fichar()
    elif menu == "📚 Historial":
        mostrar_historial()
    elif menu == "📊 Estadísticas":
        mostrar_estadisticas()

if __name__ == "__main__":
    main()
