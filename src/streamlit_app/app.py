"""
Sistema de Fichajes - Portal Principal
Punto de entrada principal para RRHH y Empleados
"""
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Fichajes",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos personalizados
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 3rem;
    }
    .portal-card {
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        transition: transform 0.3s;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .portal-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .rrhh-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .empleado-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    .portal-icon {
        font-size: 5rem;
        margin-bottom: 1rem;
    }
    .portal-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .portal-description {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Título principal
    st.markdown('<h1 class="main-title">🏢 Sistema de Fichajes</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Selecciona el portal al que deseas acceder</p>', unsafe_allow_html=True)
    
    # Crear dos columnas para los portales
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Portal RRHH
        st.markdown("""
        <div class="portal-card rrhh-card">
            <div class="portal-icon">👥</div>
            <div class="portal-title">Portal RRHH</div>
            <div class="portal-description">
                Gestión de empleados, creación de usuarios,<br>
                control de fichajes y reportes administrativos
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔐 Acceder a RRHH", key="btn_rrhh", use_container_width=True, type="primary"):
            st.switch_page("pages/1_🏢_Portal_RRHH.py")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Portal Empleado
        st.markdown("""
        <div class="portal-card empleado-card">
            <div class="portal-icon">👤</div>
            <div class="portal-title">Portal Empleado</div>
            <div class="portal-description">
                Registro de entrada/salida, consulta de fichajes<br>
                y gestión personal de horarios
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔐 Acceder como Empleado", key="btn_empleado", use_container_width=True, type="primary"):
            st.switch_page("pages/2_👤_Portal_Empleado.py")
    
    # Información adicional
    st.markdown("---")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.info("**📱 Telegram Bot**\n\nLos empleados pueden fichar mediante nuestro bot de Telegram")
    
    with col_info2:
        st.success("**🔒 Seguridad**\n\nTodos los accesos están protegidos con autenticación segura")
    
    with col_info3:
        st.warning("**⏰ Tiempo Real**\n\nLos fichajes se registran al instante en el sistema")

if __name__ == "__main__":
    main()
