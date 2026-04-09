Param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000
)

if (-Not (Test-Path -Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Error "No se encontró el entorno virtual en .\.venv\Scripts\Activate.ps1. Ejecuta primero 'py -m venv .venv' y 'pip install -r requirements.txt'."
    exit 1
}

Write-Host "Activando entorno virtual..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Iniciando uvicorn app.main:app en http://${BindHost}:${Port} con reload y debug..."
py -m uvicorn app.main:app --reload --log-level debug --host $BindHost --port $Port
