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

### Variables de entorno
- `SAT_CFDI_AUTH_URL` (default: `https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc`)
- `SAT_CFDI_SOLICITUD_URL` (default: `https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc`)
- `SAT_CFDI_VERIFICACION_URL` (default: `https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc`)
- `SAT_CFDI_DESCARGA_URL` (default: `https://cfdidescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc`)
- `SAT_RET_AUTH_URL` (default: `https://retendescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc`)
- `SAT_RET_SOLICITUD_URL` (default: `https://retendescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc`)
- `SAT_RET_VERIFICACION_URL` (default: `https://retendescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc`)
- `SAT_RET_DESCARGA_URL` (default: `https://retendescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc`)
- `SAT_CERT_PATH` (ruta al `.cer`)
- `SAT_KEY_PATH` (ruta al `.key`)
- `SAT_KEY_PASSWORD` (password de la llave `.key`)
- `SAT_TIMEOUT_SECONDS` (default: `30`)

Nota: Estas rutas WSDL estan actualizadas a la version 1.5 con fecha 1 de enero de 2026.

### Configuracion de RFC
El RFC principal se configura en `config.py` (variable `MI_RFC`).

### Credenciales SAT en BD
Se agrego el endpoint `POST /sat/credentials` para guardar `.cer` y `.key` por RFC.
Si existen credenciales en la BD para `MI_RFC`, el endpoint `POST /sat/auth`
las usa automaticamente. De lo contrario, usa `SAT_CERT_PATH` y `SAT_KEY_PATH`.

Endpoints adicionales:
- `POST /sat/credentials/delete` elimina credenciales por RFC.
- `POST /sat/descarga/flow` ejecuta el flujo completo (autenticacion, solicitud, verificacion y descarga opcional).
- `GET /sat/descarga/zip/{paquete_id}` descarga el zip directamente.
- `POST /sat/descarga/zip/save` descarga y guarda el zip en la BD.
- `GET /sat/descarga/zip/stored/{paquete_id}` descarga el zip guardado en BD.
- `GET /admin/sat` pantalla de administracion para credenciales.

Para el cifrado del password en BD se usa `SAT_PASSWORD_SECRET` en `config.py`.

### Ejecutar el proyecto con recarga automatica
```
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Descarga masiva SAT (SOAP)
Se agregaron utilidades para autenticacion, solicitud, verificacion y descarga.
Archivos relevantes:
- `sat_ws_security.py`
- `sat_xml_signature.py`
- `sat_descarga_requests.py`
- `sat_descarga_workflow.py`

Ejemplo de uso (flujo basico):
```python
from datetime import datetime

from sat_descarga_service import SatDescargaSoapService
from sat_descarga_workflow import SatDescargaWorkflow
from sat_descarga_requests import SolicitudDescargaParams
from sat_endpoints import SatEndpoints

endpoints = SatEndpoints.for_kind("cfdi")
service = SatDescargaSoapService(endpoints)
workflow = SatDescargaWorkflow.from_paths(
    service=service,
    cert_path="C:/ruta/fiel.cer",
    key_path="C:/ruta/fiel.key",
    key_password="mi_password",
)

token = workflow.autenticar()
params = SolicitudDescargaParams(
    rfc_solicitante="AAA010101AAA",
    rfc_emisor="AAA010101AAA",
    fecha_inicial=datetime(2026, 1, 1, 0, 0, 0),
    fecha_final=datetime(2026, 1, 31, 23, 59, 59),
    tipo_solicitud="CFDI",
)
id_solicitud = workflow.solicitar_descarga(params, access_token=token)
resultado = workflow.verificar_descarga(
    rfc_solicitante=params.rfc_solicitante,
    id_solicitud=id_solicitud,
    access_token=token,
)
for paquete in resultado.paquetes:
    zip_bytes = workflow.descargar_paquete(
        rfc_solicitante=params.rfc_solicitante,
        id_paquete=paquete,
        access_token=token,
    )
```
