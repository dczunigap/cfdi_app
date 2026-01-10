# Administracion Contable SAT
Este proyecto permite realizar una administración contable básica para los usuarios que no realizan grandes cantidades de facturacion y gastos, que solo requieren presentar mensualmente sus declaraciones.

Inicialmente fue diseñado para presentar declaraciones bajo el esquema de Personas Fisicas con Actividad Empresarial por uso de Plataformas Tecnologicas, sin embargo tiene potencial para una administración básica de la contabilidad general.

Tiene 6 visores 
- CFDI (Clasificados)
- Retenciones
- Declaraciones
- Resumen Mensual
- Modo Declaración
- Declaraciones presentadas

Tiene 2 Modulos de importacion
- CFDI (XML's de facturas recibidas y emitidas, ademas de xml de retenciones)
- PDF de Declaraciones mensuales presentadas

---

#### Instalar el environment
```
py -m venv .venv
```

#### Permisos para ejecucion en W11
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

#### Activar el environment en W11
```
.\.venv\Scripts\Activate.ps1
```

#### Instalar predependencias
```
pip install --upgrade pip setuptools wheel
```

#### Instalar las dependencias del proyecto
```
pip install -r requirements.txt
```

### Ejecutar el proyecto con recarga automatica
```
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```