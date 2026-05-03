# Sistema de Fichajes

Sistema de control de jornada con tres componentes principales:

- `src/fichajes_backpy`: backend FastAPI y API REST.
- `src/streamlit_app`: portal web para RRHH y empleados.
- `src/telegram_bot`: bot de Telegram para fichaje remoto.

## Arquitectura general

El proyecto está organizado como un monorepo Python con instalación editable. La ejecución real parte de `INICIO.cmd`, que delega en `INICIO.ps1` y coordina el arranque del sistema completo.

El arranque sigue este orden:

1. Detecta el intérprete Python disponible.
2. Muestra el banner informativo del proyecto.
3. Ofrece crear el entorno de prueba con usuarios controlados.
4. Instala las dependencias del proyecto.
5. Inicializa el usuario administrador inicial si no existe.
6. Lanza el bot de Telegram.
7. Lanza el backend FastAPI.
8. Lanza el frontend Streamlit.

## Estructura relevante

```text
proyectoFichajes/
├── INICIO.cmd
├── INICIO.ps1
├── pyproject.toml
├── crear_admin.py
├── crear_entorno_prueba.py
├── pruebas_manuales/
└── src/
	├── fichajes_backpy/
	├── streamlit_app/
	└── telegram_bot/
```

## Configuración y datos

El sistema depende de un archivo `.env` en la raíz y de una instancia de MongoDB accesible en `localhost:27017`. Las credenciales, el nombre de base de datos y el token de Telegram se resuelven desde ese entorno.

## Flujo funcional

El backend expone la API para autenticación, usuarios, fichajes y vínculos con Telegram. El portal Streamlit consume la base de datos para la interfaz de RRHH y el portal de empleados. El bot de Telegram permite registrar entradas y salidas desde mensajería, vinculando cada cuenta de Telegram con un usuario del sistema.

## Utilidades manuales

Los scripts de `pruebas_manuales/` quedan reservados para comprobaciones puntuales y no forman parte del flujo normal de arranque.

## Notas

- Las contraseñas se almacenan hasheadas en MongoDB.
- La separación en `src/` evita imports frágiles y deja el proyecto listo para instalación editable.
- El proyecto conserva un flujo local completo para demostración y pruebas en entorno de profesor.
