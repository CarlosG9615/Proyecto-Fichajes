# Sistema de Fichajes

Sistema de control de jornada con:

- Portal web de RRHH y empleados en Streamlit.
- Bot de Telegram para fichaje remoto.
- Backend FastAPI para API REST (opcional según uso).
- MongoDB como base de datos.

## Estructura relevante

```text
proyectoFichajes/
├── INICIO.ps1                  # Script maestro automatico
├── INICIO.cmd                  # Entrada recomendada (evita policy issues)
├── streamlit_app/              # Portal integrado principal
├── telegram_bot/               # Bot Telegram principal
├── fichajes_backpy/            # Backend FastAPI
└── fichajes_frontpy/           # Interfaces legacy/alternativas
```

## Requisitos

- Windows con PowerShell.
- Python 3.11+ recomendado.
- MongoDB levantado en localhost:27017.
- Entorno virtual `.venv` en la raiz.

## Instalacion inicial

Desde la raiz del proyecto:

```powershell
python -m pip install -r .\fichajes_backpy\requirements.txt
python -m pip install -r .\streamlit_app\requirements.txt
python -m pip install -r .\telegram_bot\requirements.txt
python -m pip install -r .\fichajes_frontpy\requirements.txt
```

## Configuracion

Crea un archivo `.env` en la raiz del proyecto.

## Si clonas el repositorio

Pasos recomendados para dejarlo listo y arrancar con `INICIO.cmd`:

1. Clona el repositorio y entra en la carpeta del proyecto.
2. Crea el entorno virtual en la raiz.
3. Activa el entorno virtual.
4. Crea `.env` a partir de `.env.example` y completa valores.
5. Asegura que MongoDB este levantado en `localhost:27017`.
6. Ejecuta `INICIO.cmd`.

Comandos ejemplo (PowerShell):

```powershell
git clone <url-del-repo>
cd proyectoFichajes
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
.\INICIO.cmd
```

Variables que debes completar en `.env` antes de usar el sistema:

- `MONGO_URI` y/o `MONGO_URL`
- `DATABASE_NAME`
- `SECRET_KEY`
- `TELEGRAM_TOKEN` (si se usara bot)
- `ALGORITHM` (algoritmo de encriptación)
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## Que archivos compartir (sin datos sensibles)

Para otra persona del equipo, comparte:

- Codigo del repositorio.
- `.env.example` con valores de ejemplo o placeholders.
- `README.md` y `QUICKSTART.md`.

No compartas por Git ni por chat:

- `.env`
- Tokens de Telegram
- `SECRET_KEY`
- Cualquier credencial real de MongoDB

## Arranque recomendado

### Opcion unica recomendada

```powershell
.\INICIO.cmd
```

Ese script ya hace todo en orden automáticamente:

1. Instala/actualiza dependencias.
2. Crea el usuario administrador inicial si no existe.
3. Arranca el bot de Telegram.
4. Arranca el backend.
5. Espera a que el backend responda.
6. Lanza el frontend al final.

Cuando termine, todo queda levantado.

Requisito previo: MongoDB debe estar levantado en `localhost:27017`.

Si prefieres PowerShell directo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\INICIO.ps1
```

## URLs por defecto

- Portal web: http://localhost:8501/Portal_RRHH
- Backend Swagger: http://localhost:8000/docs
- Backend health: http://localhost:8000/health

## Credenciales iniciales

En interfaces administrativas puede existir usuario inicial:

- Usuario: admin
- Password: admin123

Se recomienda cambiarla tras el primer acceso.

## Scripts activos

Arranque unico del sistema:

- `INICIO.ps1`
- `INICIO.cmd`

Los lanzadores secundarios fueron eliminados para evitar rutas de arranque duplicadas.

## Troubleshooting rapido

- Error de conexion MongoDB:

```powershell
Test-NetConnection localhost -Port 27017
```

- Error de modulos no instalados:

```powershell
python -m pip install -r .\streamlit_app\requirements.txt
python -m pip install -r .\fichajes_backpy\requirements.txt
python -m pip install -r .\telegram_bot\requirements.txt
python -m pip install -r .\fichajes_frontpy\requirements.txt
```

- Error de bcrypt en Windows:

```powershell
python -m pip install --upgrade --force-reinstall bcrypt==4.0.1 passlib==1.7.4
```

- Error de firma digital en PowerShell al arrancar backend:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\INICIO.ps1
```

## Notas

- Este repositorio mantiene componentes legacy en paralelo.
- El flujo recomendado actual es `streamlit_app + telegram_bot + fichajes_backpy`.
- Las contraseñas se almacenan hasheadas en MongoDB (`password_hash`), nunca en texto plano.
- Para puesta en produccion, configura `SECRET_KEY` robusta y credenciales seguras.
