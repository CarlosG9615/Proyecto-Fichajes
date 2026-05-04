# Script automático de arranque del Sistema de Fichajes
# Orden: dependencias -> admin -> bot -> backend -> frontend

function Write-Step($message) {
    Write-Host ""
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] $message" -ForegroundColor Cyan
}

function Get-PythonExecutable {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    return $null
}

function Start-TelegramBot {
    param([string]$pythonExe)

    $telegramPath = Join-Path $PSScriptRoot "src\telegram_bot"
    if (-not (Test-Path $telegramPath)) {
        throw "No se encontró directorio src\telegram_bot"
    }

    $command = "Set-Location -Path '$PSScriptRoot'; & '$pythonExe' -m telegram_bot.bot"
    Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) | Out-Null
    Write-Step "Bot de Telegram iniciado"
}

function Start-Backend {
    param([string]$pythonExe)

    $backendPath = Join-Path $PSScriptRoot "src\fichajes_backpy"
    if (-not (Test-Path $backendPath)) {
        throw "No se encontró directorio src\fichajes_backpy"
    }

    $command = "Set-Location -Path '$PSScriptRoot'; & '$pythonExe' -m uvicorn fichajes_backpy.main:app --reload --port 8000"
    Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) | Out-Null
    Write-Step "Backend FastAPI iniciado"
}

function Start-Frontend {
    param([string]$pythonExe)

    $streamlitPath = Join-Path $PSScriptRoot "src\streamlit_app"
    if (-not (Test-Path $streamlitPath)) {
        throw "No se encontró directorio src\streamlit_app"
    }

    $command = "Set-Location -Path '$PSScriptRoot'; & '$pythonExe' -m streamlit run src/streamlit_app/app.py"
    Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) | Out-Null
    Write-Step "Frontend Streamlit iniciado"
}

function Wait-ForPort($port, $timeoutSeconds = 90) {
    $elapsed = 0
    while ($elapsed -lt $timeoutSeconds) {
        try {
            $result = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
            if ($result.TcpTestSucceeded) {
                return $true
            }
        } catch {
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
    }
    return $false
}

function Ensure-MongoRunning {
    Write-Step "Comprobando MongoDB en puerto 27017"
    if (-not (Wait-ForPort -port 27017 -timeoutSeconds 20)) {
        Write-Host "MongoDB no está disponible en localhost:27017. Inícialo antes de arrancar el sistema." -ForegroundColor Red
        exit 1
    }
}

function Install-Dependencies {
    param([string]$pythonExe)

    Write-Step "Instalando dependencias"
    & $pythonExe -m pip install -e .
    & $pythonExe -m pip install --upgrade pip setuptools wheel
    & $pythonExe -m pip install -r .\src\fichajes_backpy\requirements.txt
    & $pythonExe -m pip install -r .\src\streamlit_app\requirements.txt
    & $pythonExe -m pip install -r .\src\telegram_bot\requirements.txt
}

function Ensure-Admin {
    param([string]$pythonExe)

    Write-Step "Creando usuario administrador si no existe"
    & $pythonExe src/scripts/crear_admin.py --auto
}

function Start-TestEnv {
    param([string]$pythonExe)

    $scriptPath = Join-Path $PSScriptRoot "src/scripts/crear_entorno_prueba.py"
    if (-not (Test-Path $scriptPath)) {
        Write-Host "No se encontró src/scripts/crear_entorno_prueba.py" -ForegroundColor Yellow
        return
    }

    Write-Step "Creando entorno de prueba (usuarios)..."
    & $pythonExe $scriptPath
    Write-Step "Entorno de prueba creado"
}

function Main {
    Clear-Host
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "         SISTEMA DE FICHAJES INTEGRADO - ARRANQUE AUTOMATICO    " -ForegroundColor White
    Write-Host "================================================================" -ForegroundColor Cyan

    $pythonExe = Get-PythonExecutable
    if (-not $pythonExe) {
        Write-Host "Python no esta instalado o no esta en el PATH" -ForegroundColor Red
        exit 1
    }

    Write-Step "Python detectado: $pythonExe"

    # Banner e información de entorno de prueba
    Write-Host "";
    Write-Host "PROYECTO BOT DE TELEGRAM POR : CARLOS, KIKE, VALENTINA Y ELENA" -ForegroundColor Green
    Write-Host "Creando un entorno de prueba..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Write-Host "Credenciales de prueba:" -ForegroundColor Yellow
    Write-Host "- Admin  / AdminPrueba1234!" -ForegroundColor Yellow
    Write-Host "- Usuario / UsuarioPrueba1234!" -ForegroundColor Yellow
    Write-Host ""
    $createTest = Read-Host "¿Crear entorno de prueba y volcar usuarios de prueba a MongoDB? (S/n)"
    if ($createTest -eq "S" -or $createTest -eq "s" -or $createTest -eq "") {
        Start-TestEnv -pythonExe $pythonExe
    } else {
        Write-Step "Omitiendo creación de entorno de prueba"
    }

    if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
        Write-Host "No se encontro .venv en la raiz. Debes crear el entorno antes de arrancar." -ForegroundColor Red
        exit 1
    }

    Install-Dependencies -pythonExe $pythonExe
    Ensure-MongoRunning
    Ensure-Admin -pythonExe $pythonExe

    Write-Step "Arrancando bot de Telegram"
    Start-TelegramBot -pythonExe $pythonExe

    Start-Sleep -Seconds 3
    Write-Step "Arrancando backend"
    Start-Backend -pythonExe $pythonExe

    Write-Step "Esperando backend en puerto 8000"
    if (-not (Wait-ForPort -port 8000 -timeoutSeconds 90)) {
        Write-Host "El backend no respondió a tiempo en el puerto 8000" -ForegroundColor Red
        exit 1
    }

    Write-Step "Arrancando frontend"
    Start-Frontend -pythonExe $pythonExe

    Write-Host ""
    Write-Host "Sistema iniciado correctamente." -ForegroundColor Green
    Write-Host "Frontend: http://localhost:8501/Portal_RRHH" -ForegroundColor Green
    Write-Host "Backend:   http://localhost:8000/docs" -ForegroundColor Green
    Write-Host ""
}

Main
