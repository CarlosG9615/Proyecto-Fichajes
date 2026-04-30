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

    $telegramPath = Join-Path $PSScriptRoot "telegram_bot"
    if (-not (Test-Path $telegramPath)) {
        throw "No se encontró directorio telegram_bot"
    }

    $command = "Set-Location -Path '$telegramPath'; & '$pythonExe' bot.py"
    Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) | Out-Null
    Write-Step "Bot de Telegram iniciado"
}

function Start-Backend {
    param([string]$pythonExe)

    $backendPath = Join-Path $PSScriptRoot "fichajes_backpy"
    if (-not (Test-Path $backendPath)) {
        throw "No se encontró directorio fichajes_backpy"
    }

    $command = "Set-Location -Path '$backendPath'; & '$pythonExe' -m uvicorn main:app --reload --port 8000"
    Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) | Out-Null
    Write-Step "Backend FastAPI iniciado"
}

function Start-Frontend {
    param([string]$pythonExe)

    $streamlitPath = Join-Path $PSScriptRoot "streamlit_app"
    if (-not (Test-Path $streamlitPath)) {
        throw "No se encontró directorio streamlit_app"
    }

    $command = "Set-Location -Path '$streamlitPath'; & '$pythonExe' -m streamlit run app.py"
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
    & $pythonExe -m pip install --upgrade pip setuptools wheel
    & $pythonExe -m pip install -r .\fichajes_backpy\requirements.txt
    & $pythonExe -m pip install -r .\streamlit_app\requirements.txt
    & $pythonExe -m pip install -r .\telegram_bot\requirements.txt
    if (Test-Path ".\fichajes_frontpy\requirements.txt") {
        & $pythonExe -m pip install -r .\fichajes_frontpy\requirements.txt
    }
}

function Ensure-Admin {
    param([string]$pythonExe)

    Write-Step "Creando usuario administrador si no existe"
    & $pythonExe crear_admin.py --auto
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
