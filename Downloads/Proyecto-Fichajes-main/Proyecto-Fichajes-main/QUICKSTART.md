# QUICKSTART

Arranque rapido del sistema en entorno local Windows.

## 1) Requisitos

- MongoDB ejecutandose en localhost:27017.
- Entorno virtual `.venv` creado en la raiz.

## 2) Instalar dependencias

Desde la raiz del proyecto:

```powershell
python -m pip install -r .\fichajes_backpy\requirements.txt
python -m pip install -r .\streamlit_app\requirements.txt
python -m pip install -r .\telegram_bot\requirements.txt
```

## 3) Arrancar todo

Opcion recomendada:

```powershell
.\INICIO.cmd
```

No hay lanzadores alternativos: el arranque soportado es solo por `INICIO.cmd` (o `INICIO.ps1` con bypass temporal).

Ese comando levanta automaticamente:

1. Dependencias
2. Usuario admin inicial (si no existe)
3. Bot de Telegram
4. Backend FastAPI
5. Frontend Streamlit

## 4) URLs

- Portal: http://localhost:8501/Portal_RRHH
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/health

## 5) Credenciales iniciales

- Usuario: admin
- Password: admin123

## 6) Problemas comunes

- MongoDB no responde:

```powershell
Test-NetConnection localhost -Port 27017
```

- Error de dependencias Python:

```powershell
python -m pip install -r .\fichajes_backpy\requirements.txt
python -m pip install -r .\streamlit_app\requirements.txt
python -m pip install -r .\telegram_bot\requirements.txt
```

- Error de bcrypt/passlib:

```powershell
python -m pip install --upgrade --force-reinstall bcrypt==4.0.1 passlib==1.7.4
```

- Bloqueo por policy de PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\INICIO.ps1
```
