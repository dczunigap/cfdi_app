## Instalar el environment
```
py -m venv .venv
```

## Permisos para ejecucion en W11
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Activar el environment en W11
```
.\.venv\Scripts\Activate.ps1
```

## Instalar predependencias
```
pip install --upgrade pip setuptools wheel
```

## Instalar las dependencias del proyecto
```
pip install -r requirements.txt
```

## Ejecutar el proyecto con recarga automatica
```
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```