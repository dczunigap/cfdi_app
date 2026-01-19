"""API FastAPI para gestión de CFDI e impuestos (México)."""

from __future__ import annotations

import base64
import calendar
import io
import re
import time
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import zipfile

from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from sqlalchemy import select, desc, and_
from sqlalchemy.orm import Session

from db import engine, SessionLocal, PDF_DIR, ZIP_DIR
from models import (
    Base,
    Factura,
    Concepto,
    Pago,
    RetencionPlataforma,
    DeclaracionPDF,
    SatCredential,
    SatPackage,
    SatCfdiZip,
)
from parser_xml import detect_xml_kind, parse_cfdi_40, parse_retenciones_plataforma
from parser_pdf import extract_pdf_text, parse_sat_declaracion_summary
from config import MI_RFC
from sat_crypto import decrypt_password, encrypt_password
from sat_descarga_service import SatDescargaSoapService
from sat_descarga_workflow import SatDescargaWorkflow
from sat_descarga_requests import SolicitudDescargaParams
from sat_actions import (
    SOAP_CFDI_ACTION_AUTENTICA,
    SOAP_CFDI_ACTION_SOLICITA_EMITIDOS,
    SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS,
)
from sat_ws_security import load_sat_key_material_from_bytes
from sat_endpoints import SatEndpoints
from utils import (
    sha256_bytes,
    safe_pdf_filename,
    json_default_encoder,
    format_money,
    serialize_to_json,
    apply_sign_factor,
)

# Configuración base de FastAPI
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Contabilidad CFDI (local)")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("cfdi_app")

# Registrar filtro personalizado para templates Jinja2
templates.env.filters["money"] = format_money


@app.on_event("startup")
def on_startup() -> None:
    """Inicializa la base de datos al arrancar la aplicación."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Factory para obtener sesión de base de datos."""
    return SessionLocal()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, msg: Optional[str] = None) -> HTMLResponse:
    """Página de inicio de la aplicación."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "mi_rfc": MI_RFC, "msg": msg},
    )


class SatAuthRequest(BaseModel):
    kind: str = "cfdi"
    soap_action: Optional[str] = None
    to_url: Optional[str] = None
    action: Optional[str] = None


class SatDescargaFlowRequest(BaseModel):
    kind: str = "cfdi"
    rfc_solicitante: Optional[str] = None
    fecha_inicial: str
    fecha_final: str
    tipo_solicitud: str = "CFDI"
    rfc_emisor: Optional[str] = None
    rfc_receptores: list[str] = []
    poll_attempts: int = 10
    poll_seconds: int = 10
    download: bool = False


@app.post("/sat/auth")
def sat_auth(payload: SatAuthRequest) -> dict:
    endpoints = SatEndpoints.for_kind(payload.kind)
    service = SatDescargaSoapService(endpoints)
    with SessionLocal() as db:
        credentials = _get_sat_credentials(db, MI_RFC)
        if credentials and _credentials_ready(credentials):
            password = decrypt_password(credentials.key_password)
            logger.debug(
                "SAT auth usando credenciales BD rfc=%s cert=%s key=%s password=%s",
                MI_RFC,
                bool(credentials.cert_der),
                bool(credentials.key_der),
                bool(password),
            )
            key_material = load_sat_key_material_from_bytes(
                credentials.cert_der,
                credentials.key_der,
                password,
            )
            workflow = SatDescargaWorkflow(service=service, key_material=key_material)
        else:
            raise HTTPException(
                status_code=400,
                detail="No hay credenciales validas en BD para este RFC.",
            )
    token = workflow.autenticar(
        soap_action=payload.soap_action,
        to_url=payload.to_url,
        action=payload.action,
    )
    return {"token": token}


@app.post("/sat/credentials")
async def sat_credentials(
    rfc: Optional[str] = Form(None),
    key_password: Optional[str] = Form(None),
    cert_file: UploadFile = File(...),
    key_file: UploadFile = File(...),
) -> dict:
    rfc_value = (rfc or MI_RFC).strip()
    cert_bytes = await cert_file.read()
    key_bytes = await key_file.read()
    if not cert_bytes or not key_bytes:
        raise HTTPException(status_code=400, detail="Archivos .cer y .key son requeridos.")
    encrypted_password = encrypt_password(key_password)
    with SessionLocal() as db:
        existing = _get_sat_credentials(db, rfc_value)
        if existing:
            existing.cert_der = cert_bytes
            existing.key_der = key_bytes
            existing.key_password = encrypted_password
        else:
            db.add(
                SatCredential(
                    rfc=rfc_value,
                    cert_der=cert_bytes,
                    key_der=key_bytes,
                    key_password=encrypted_password,
                )
            )
        db.commit()
    return {"status": "ok", "rfc": rfc_value}


@app.post("/sat/credentials/delete")
def sat_credentials_delete() -> dict:
    rfc_value = MI_RFC.strip()
    with SessionLocal() as db:
        existing = _get_sat_credentials(db, rfc_value)
        if not existing:
            raise HTTPException(status_code=404, detail="RFC sin credenciales.")
        existing.cert_der = b""
        existing.key_der = b""
        existing.key_password = None
        db.commit()
    return {"status": "cleared", "rfc": rfc_value}


@app.get("/admin/sat", response_class=HTMLResponse)
def admin_sat(request: Request) -> HTMLResponse:
    with SessionLocal() as db:
        creds = db.query(SatCredential).order_by(SatCredential.rfc.asc()).all()
        packages = db.query(SatPackage).order_by(SatPackage.created_at.desc()).limit(20).all()
    return templates.TemplateResponse(
        "admin_sat.html",
        {
            "request": request,
            "mi_rfc": MI_RFC,
            "creds": creds,
            "packages": packages,
        },
    )


@app.post("/sat/descarga/flow")
def sat_descarga_flow(payload: SatDescargaFlowRequest) -> dict:
    endpoints = SatEndpoints.for_kind(payload.kind)
    service = SatDescargaSoapService(endpoints)
    with SessionLocal() as db:
        credentials = _get_sat_credentials(db, payload.rfc_solicitante or MI_RFC)
        if not credentials or not _credentials_ready(credentials):
            raise HTTPException(status_code=404, detail="No hay credenciales para el RFC.")
        password = decrypt_password(credentials.key_password)
        key_material = load_sat_key_material_from_bytes(
            credentials.cert_der,
            credentials.key_der,
            password,
        )
        workflow = SatDescargaWorkflow(service=service, key_material=key_material)

    token = workflow.autenticar(
        soap_action=SOAP_CFDI_ACTION_AUTENTICA,
        to_url=endpoints.auth_url,
        action=SOAP_CFDI_ACTION_AUTENTICA,
    )
    try:
        fecha_inicial = datetime.fromisoformat(payload.fecha_inicial)
        fecha_final = datetime.fromisoformat(payload.fecha_final)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Formato de fecha invalido.") from exc
    params = SolicitudDescargaParams(
        rfc_solicitante=payload.rfc_solicitante or MI_RFC,
        rfc_emisor=payload.rfc_emisor,
        fecha_inicial=fecha_inicial,
        fecha_final=fecha_final,
        tipo_solicitud=payload.tipo_solicitud,
        rfc_receptores=payload.rfc_receptores or [],
    )
    id_solicitud = workflow.solicitar_descarga(params, access_token=token)

    result = None
    for _ in range(max(1, payload.poll_attempts)):
        result = workflow.verificar_descarga(
            rfc_solicitante=params.rfc_solicitante,
            id_solicitud=id_solicitud,
            access_token=token,
        )
        if result.estado_solicitud == "3":
            break
        time.sleep(max(0, payload.poll_seconds))

    response = {
        "id_solicitud": id_solicitud,
        "estado_solicitud": result.estado_solicitud if result else None,
        "codigo_estado": result.codigo_estado if result else None,
        "mensaje": result.mensaje if result else None,
        "paquetes": result.paquetes if result else [],
    }
    if payload.download and result and result.paquetes:
        paquetes = []
        for paquete_id in result.paquetes:
            zip_bytes = workflow.descargar_paquete(
                rfc_solicitante=params.rfc_solicitante,
                id_paquete=paquete_id,
                access_token=token,
            )
            paquetes.append(
                {
                    "id_paquete": paquete_id,
                    "zip_base64": base64.b64encode(zip_bytes).decode("ascii"),
                }
            )
        response["descargas"] = paquetes
    return response


@app.get("/sat/descarga/zip/{paquete_id}")
def sat_descarga_zip(paquete_id: str, kind: str = "cfdi", rfc: Optional[str] = None) -> Response:
    endpoints = SatEndpoints.for_kind(kind)
    service = SatDescargaSoapService(endpoints)
    rfc_value = (rfc or MI_RFC).strip()
    with SessionLocal() as db:
        credentials = _get_sat_credentials(db, rfc_value)
        if not credentials or not _credentials_ready(credentials):
            raise HTTPException(status_code=404, detail="No hay credenciales para el RFC.")
        password = decrypt_password(credentials.key_password)
        key_material = load_sat_key_material_from_bytes(
            credentials.cert_der,
            credentials.key_der,
            password,
        )
        workflow = SatDescargaWorkflow(service=service, key_material=key_material)
    token = workflow.autenticar(
        soap_action=SOAP_CFDI_ACTION_AUTENTICA,
        to_url=endpoints.auth_url,
        action=SOAP_CFDI_ACTION_AUTENTICA,
    )
    zip_bytes = workflow.descargar_paquete(
        rfc_solicitante=rfc_value,
        id_paquete=paquete_id,
        access_token=token,
    )
    headers = {"Content-Disposition": f'attachment; filename="{paquete_id}.zip"'}
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)


@app.post("/sat/descarga/zip/save")
def sat_descarga_zip_save(
    paquete_id: str = Form(...),
    kind: str = Form("cfdi"),
    rfc: Optional[str] = Form(None),
) -> dict:
    endpoints = SatEndpoints.for_kind(kind)
    service = SatDescargaSoapService(endpoints)
    rfc_value = (rfc or MI_RFC).strip()
    with SessionLocal() as db:
        credentials = _get_sat_credentials(db, rfc_value)
        if not credentials or not _credentials_ready(credentials):
            raise HTTPException(status_code=404, detail="No hay credenciales para el RFC.")
        password = decrypt_password(credentials.key_password)
        key_material = load_sat_key_material_from_bytes(
            credentials.cert_der,
            credentials.key_der,
            password,
        )
        workflow = SatDescargaWorkflow(service=service, key_material=key_material)
        token = workflow.autenticar(
            soap_action=SOAP_CFDI_ACTION_AUTENTICA,
            to_url=endpoints.auth_url,
            action=SOAP_CFDI_ACTION_AUTENTICA,
        )
        zip_bytes = workflow.descargar_paquete(
            rfc_solicitante=rfc_value,
            id_paquete=paquete_id,
            access_token=token,
        )
        existing = (
            db.query(SatPackage)
            .filter(SatPackage.rfc == rfc_value, SatPackage.paquete_id == paquete_id)
            .one_or_none()
        )
        if existing:
            existing.zip_data = zip_bytes
        else:
            db.add(
                SatPackage(
                    rfc=rfc_value,
                    paquete_id=paquete_id,
                    zip_data=zip_bytes,
                )
            )
        db.commit()
    return {"status": "stored", "rfc": rfc_value, "paquete_id": paquete_id, "bytes": len(zip_bytes)}


@app.get("/sat/descarga/zip/stored/{paquete_id}")
def sat_descarga_zip_stored(paquete_id: str, rfc: Optional[str] = None) -> Response:
    rfc_value = (rfc or MI_RFC).strip()
    with SessionLocal() as db:
        stored = (
            db.query(SatPackage)
            .filter(SatPackage.rfc == rfc_value, SatPackage.paquete_id == paquete_id)
            .one_or_none()
        )
        if not stored:
            raise HTTPException(status_code=404, detail="Paquete no encontrado en BD.")
        zip_bytes = stored.zip_data
    headers = {"Content-Disposition": f'attachment; filename="{paquete_id}.zip"'}
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)


def _get_sat_credentials(db: Session, rfc: str) -> SatCredential | None:
    return db.query(SatCredential).filter(SatCredential.rfc == rfc).one_or_none()


def _credentials_ready(credentials: SatCredential) -> bool:
    return bool(credentials.cert_der) and bool(credentials.key_der)


def _password_ready(credentials: SatCredential) -> bool:
    return bool(credentials.key_password)


def _sat_wait_until(db: Session, rfc: str, year: int, month: int) -> Optional[datetime]:
    cutoff = datetime.utcnow() - timedelta(hours=48)
    recent = (
        db.query(SatCfdiZip)
        .filter(
            SatCfdiZip.rfc == rfc,
            SatCfdiZip.year == year,
            SatCfdiZip.month == month,
            SatCfdiZip.created_at >= cutoff,
        )
        .order_by(SatCfdiZip.created_at.desc())
        .first()
    )
    if not recent:
        return None
    return recent.created_at + timedelta(hours=48)


def _build_period_range(year: int, month: int) -> tuple[datetime, datetime]:
    last_day = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, 0, 0, 0)
    end = datetime(year, month, last_day, 23, 59, 59)
    return start, end


def _zip_storage_path(rfc: str, year: int, month: int, tipo: str, paquete_id: str) -> Path:
    safe_rfc = re.sub(r"[^A-Z0-9]", "", rfc.upper())
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{safe_rfc}_{year}{month:02d}_{tipo}_{paquete_id}_{stamp}.zip"
    return ZIP_DIR / filename


def _import_cfdi_xml_bytes(db: Session, xml_bytes: bytes, stats: dict) -> None:
    kind = detect_xml_kind(xml_bytes)
    if kind != "cfdi":
        stats["omitidos"] += 1
        return
    parsed = parse_cfdi_40(xml_bytes)
    uuid = parsed.get("uuid")
    if uuid:
        exists = db.scalar(select(Factura.id).where(Factura.uuid == uuid))
        if exists:
            stats["duplicados"] += 1
            return
    parsed["xml_text"] = xml_bytes.decode("utf-8", errors="replace")
    factura = _create_factura_from_parsed(parsed)
    db.add(factura)
    db.commit()
    stats["insertados"] += 1


# ============================================================================
# Funciones auxiliares internas
# ============================================================================


def _create_factura_from_parsed(parsed: dict) -> Factura:
    """Crea objeto Factura desde datos parseados de CFDI."""
    factura = Factura(
        uuid=parsed.get("uuid"),
        version=parsed.get("version"),
        tipo_comprobante=parsed.get("tipo_comprobante"),
        fecha_emision=parsed.get("fecha_emision"),
        year_emision=parsed.get("year_emision"),
        month_emision=parsed.get("month_emision"),
        naturaleza=parsed.get("naturaleza"),
        emisor_rfc=parsed.get("emisor_rfc"),
        emisor_nombre=parsed.get("emisor_nombre"),
        receptor_rfc=parsed.get("receptor_rfc"),
        receptor_nombre=parsed.get("receptor_nombre"),
        uso_cfdi=parsed.get("uso_cfdi"),
        moneda=parsed.get("moneda"),
        metodo_pago=parsed.get("metodo_pago"),
        forma_pago=parsed.get("forma_pago"),
        subtotal=parsed.get("subtotal"),
        descuento=parsed.get("descuento"),
        total=parsed.get("total"),
        total_trasladados=parsed.get("total_trasladados"),
        total_retenidos=parsed.get("total_retenidos"),
        xml_text=parsed.get("xml_text", ""),
    )
    
    # Agregar conceptos
    for c in parsed.get("conceptos", []):
        factura.conceptos.append(
            Concepto(
                clave_prod_serv=c.get("clave_prod_serv"),
                cantidad=c.get("cantidad"),
                clave_unidad=c.get("clave_unidad"),
                descripcion=c.get("descripcion"),
                valor_unitario=c.get("valor_unitario"),
                importe=c.get("importe"),
                objeto_imp=c.get("objeto_imp"),
            )
        )
    
    # Agregar pagos (solo si tipo=P)
    for p in parsed.get("pagos", []):
        factura.pagos.append(
            Pago(
                fecha_pago=p.get("fecha_pago"),
                year_pago=p.get("year_pago"),
                month_pago=p.get("month_pago"),
                monto=p.get("monto"),
                moneda_p=p.get("moneda_p"),
                forma_pago_p=p.get("forma_pago_p"),
            )
        )
    
    return factura


def _create_retencion_from_parsed(parsed: dict) -> RetencionPlataforma:
    """Crea objeto RetencionPlataforma desde datos parseados."""
    return RetencionPlataforma(
        uuid=parsed.get("uuid"),
        version=parsed.get("version"),
        fecha_exp=parsed.get("fecha_exp"),
        ejercicio=parsed.get("ejercicio"),
        mes_ini=parsed.get("mes_ini"),
        mes_fin=parsed.get("mes_fin"),
        emisor_rfc=parsed.get("emisor_rfc"),
        emisor_nombre=parsed.get("emisor_nombre"),
        receptor_rfc=parsed.get("receptor_rfc"),
        receptor_nombre=parsed.get("receptor_nombre"),
        monto_tot_operacion=parsed.get("monto_tot_operacion"),
        monto_tot_grav=parsed.get("monto_tot_grav"),
        monto_tot_exent=parsed.get("monto_tot_exent"),
        monto_tot_ret=parsed.get("monto_tot_ret"),
        periodicidad=parsed.get("periodicidad"),
        num_serv=parsed.get("num_serv"),
        mon_tot_serv_siva=parsed.get("mon_tot_serv_siva"),
        total_iva_trasladado=parsed.get("total_iva_trasladado"),
        total_iva_retenido=parsed.get("total_iva_retenido"),
        total_isr_retenido=parsed.get("total_isr_retenido"),
        dif_iva_entregado_prest_serv=parsed.get("dif_iva_entregado_prest_serv"),
        mon_total_por_uso_plataforma=parsed.get("mon_total_por_uso_plataforma"),
        xml_text=parsed.get("xml_text", ""),
    )


@app.post("/importar")
async def importar(files: list[UploadFile] = File(...)):
    """Importa archivos XML (CFDI y retenciones de plataforma)."""
    stats = {
        "cfdi_insertados": 0,
        "cfdi_duplicados": 0,
        "retenciones_insertadas": 0,
        "retenciones_duplicadas": 0,
        "errores": 0,
    }

    db = get_db()
    try:
        for file in files:
            try:
                xml_bytes = await file.read()
                kind = detect_xml_kind(xml_bytes)

                if kind == "cfdi":
                    parsed = parse_cfdi_40(xml_bytes)
                    uuid = parsed.get("uuid")

                    if uuid:
                        exists = db.scalar(select(Factura.id).where(Factura.uuid == uuid))
                        if exists:
                            stats["cfdi_duplicados"] += 1
                            continue

                    # Agregar XML_text al parsed dict
                    parsed["xml_text"] = xml_bytes.decode("utf-8", errors="replace")
                    factura = _create_factura_from_parsed(parsed)
                    
                    db.add(factura)
                    db.commit()
                    stats["cfdi_insertados"] += 1

                elif kind == "retenciones":
                    parsed = parse_retenciones_plataforma(xml_bytes)
                    uuid = parsed.get("uuid")

                    if uuid:
                        exists = db.scalar(select(RetencionPlataforma.id).where(RetencionPlataforma.uuid == uuid))
                        if exists:
                            stats["retenciones_duplicadas"] += 1
                            continue

                    parsed["xml_text"] = xml_bytes.decode("utf-8", errors="replace")
                    ret = _create_retencion_from_parsed(parsed)
                    
                    db.add(ret)
                    db.commit()
                    stats["retenciones_insertadas"] += 1

                else:
                    stats["errores"] += 1

            except Exception as e:
                db.rollback()
                stats["errores"] += 1

    finally:
        db.close()

    msg = (
        f"CFDI: {stats['cfdi_insertados']} insertados, {stats['cfdi_duplicados']} duplicados. "
        f"Retenciones: {stats['retenciones_insertadas']} insertadas, {stats['retenciones_duplicadas']} duplicadas. "
        f"Errores: {stats['errores']}."
    )
    return RedirectResponse(url=f"/?msg={msg}", status_code=303)

@app.post("/importar_pdf")
async def importar_pdf(
    files: list[UploadFile] = File(...),
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    """Importa PDFs de acuse/declaración SAT."""
    stats = {"insertados": 0, "duplicados": 0, "errores": 0}
    db = get_db()

    try:
        for file in files:
            try:
                pdf_bytes = await file.read()
                sha = sha256_bytes(pdf_bytes)

                # Verificar duplicados
                exists = db.scalar(select(DeclaracionPDF.id).where(DeclaracionPDF.sha256 == sha))
                if exists:
                    stats["duplicados"] += 1
                    continue

                # Guardar PDF en disco
                filename = safe_pdf_filename(sha, getattr(file, "filename", None))
                pdf_path = PDF_DIR / filename
                pdf_path.write_bytes(pdf_bytes)

                # Extraer texto del PDF
                text, num_pages = "", None
                try:
                    text, num_pages = extract_pdf_text(str(pdf_path))
                except Exception:
                    text, num_pages = "", None

                # Parsear resumen del acuse
                summary = {}
                try:
                    summary = parse_sat_declaracion_summary(text or "")
                except Exception:
                    summary = {}

                # Determinar periodo
                y, mth = year, month
                per = summary.get("periodo") if isinstance(summary, dict) else None

                if (not y or not mth) and per and "-" in per:
                    try:
                        y = int(per.split("-")[0])
                        mth = int(per.split("-")[1])
                    except Exception:
                        pass

                if not y or not mth:
                    now = datetime.now()
                    y = y or now.year
                    mth = mth or now.month

                # Crear registro
                rec = DeclaracionPDF(
                    year=int(y),
                    month=int(mth),
                    rfc=summary.get("rfc") if isinstance(summary, dict) else None,
                    folio=summary.get("numero_operacion") if isinstance(summary, dict) else None,
                    fecha_presentacion=summary.get("fecha_presentacion") if isinstance(summary, dict) else None,
                    sha256=sha,
                    filename=filename,
                    original_name=getattr(file, "filename", None),
                    num_pages=int(num_pages) if num_pages is not None else None,
                    text_excerpt=text[:20000] if text else None,
                )
                db.add(rec)
                db.commit()
                stats["insertados"] += 1

            except Exception:
                db.rollback()
                stats["errores"] += 1

    finally:
        db.close()

    msg = f"PDF: {stats['insertados']} importados, {stats['duplicados']} duplicados. Errores: {stats['errores']}."
    return RedirectResponse(url=f"/?msg={msg}", status_code=303)


@app.get("/declaraciones", response_class=HTMLResponse)
def listar_declaraciones(
    request: Request,
    period: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> HTMLResponse:
    """Lista declaraciones PDF importadas con filtros opcionales."""
    db = get_db()
    try:
        # Obtener periodos disponibles
        opts_raw = db.execute(
            select(DeclaracionPDF.year, DeclaracionPDF.month)
            .where(DeclaracionPDF.year.isnot(None), DeclaracionPDF.month.isnot(None))
            .group_by(DeclaracionPDF.year, DeclaracionPDF.month)
        ).all()

        uniq = {(int(y), int(m)) for (y, m) in opts_raw if y and m}
        period_options = [f"{y}-{m:02d}" for (y, m) in sorted(uniq, reverse=True)]

        selected_period = (period or "").strip()
        if selected_period and re.match(r"^\d{4}-\d{2}$", selected_period):
            try:
                year = int(selected_period.split("-")[0])
                month = int(selected_period.split("-")[1])
            except Exception:
                pass

        q = select(DeclaracionPDF).order_by(
            desc(DeclaracionPDF.year),
            desc(DeclaracionPDF.month),
            desc(DeclaracionPDF.created_at),
        )
        if year is not None:
            q = q.where(DeclaracionPDF.year == year)
        if month is not None:
            q = q.where(DeclaracionPDF.month == month)

        rows = db.scalars(q).all()
        return templates.TemplateResponse(
            "declaraciones.html",
            {
                "request": request,
                "rows": rows,
                "year": year,
                "month": month,
                "period_options": period_options,
                "selected_period": selected_period,
                "mi_rfc": MI_RFC,
            },
        )
    finally:
        db.close()


def _build_declaracion_payload(dec: DeclaracionPDF) -> dict:
    """Construye el payload JSON para un PDF de declaración."""
    parsed = {}
    try:
        parsed = parse_sat_declaracion_summary(dec.text_excerpt or "")
    except Exception:
        parsed = {}

    def _dt_iso(v) -> Optional[str]:
        try:
            return v.isoformat() if v else None
        except Exception:
            return None

    return {
        "periodo": (parsed.get("periodo") if isinstance(parsed, dict) else None)
        or f"{dec.year}-{dec.month:02d}",
        "rfc": (parsed.get("rfc") if isinstance(parsed, dict) else None) or dec.rfc,
        "nombre": (parsed.get("nombre") if isinstance(parsed, dict) else None),
        "tipo_declaracion": (parsed.get("tipo_declaracion") if isinstance(parsed, dict) else None),
        "periodo_mes": (parsed.get("periodo_mes") if isinstance(parsed, dict) else None),
        "ejercicio": (parsed.get("ejercicio") if isinstance(parsed, dict) else None),
        "numero_operacion": (parsed.get("numero_operacion") if isinstance(parsed, dict) else None)
        or (dec.folio or None),
        "fecha_presentacion": _dt_iso(dec.fecha_presentacion)
        or _dt_iso(parsed.get("fecha_presentacion") if isinstance(parsed, dict) else None),
        "linea_captura": (parsed.get("linea_captura") if isinstance(parsed, dict) else None),
        "secciones": (parsed.get("secciones") if isinstance(parsed, dict) else None) or [],
        "isr": (parsed.get("isr") if isinstance(parsed, dict) else None),
        "iva": (parsed.get("iva") if isinstance(parsed, dict) else None),
        "ingresos_totales_mes": (parsed.get("ingresos_totales_mes") if isinstance(parsed, dict) else None),
        "isr_causado": (parsed.get("isr_causado") if isinstance(parsed, dict) else None),
        "retenciones_plataformas": (parsed.get("retenciones_plataformas") if isinstance(parsed, dict) else None),
        "iva_tasa": (parsed.get("iva_tasa") if isinstance(parsed, dict) else None),
        "iva_a_cargo_16": (parsed.get("iva_a_cargo_16") if isinstance(parsed, dict) else None),
        "iva_acreditable": (parsed.get("iva_acreditable") if isinstance(parsed, dict) else None),
        "iva_retenido": (parsed.get("iva_retenido") if isinstance(parsed, dict) else None),
        "num_pages": dec.num_pages,
        "archivo": dec.original_name or dec.filename,
        "sha256": dec.sha256,
        "tiene_texto_extraible": bool((dec.text_excerpt or "").strip()),
    }


@app.get("/declaraciones/{dec_id}", response_class=HTMLResponse)
def detalle_declaracion(request: Request, dec_id: int) -> HTMLResponse:
    """Detalle de una declaración PDF importada."""
    db = get_db()
    try:
        dec = db.get(DeclaracionPDF, dec_id)
        if not dec:
            return HTMLResponse("No encontrada", status_code=404)

        resumen: list[str] = []
        if dec.rfc:
            resumen.append(f"RFC: {dec.rfc}")
        if dec.fecha_presentacion:
            resumen.append(f"Fecha presentación: {dec.fecha_presentacion.date().isoformat()}")
        if dec.folio:
            resumen.append(f"Número de operación: {dec.folio}")
        if dec.num_pages is not None:
            resumen.append(f"Páginas: {dec.num_pages}")
        if not dec.text_excerpt:
            resumen.append("No se pudo extraer texto (posible PDF escaneado).")

        payload = _build_declaracion_payload(dec)
        resumen_json = serialize_to_json(payload)

        return templates.TemplateResponse(
            "declaracion_pdf_detalle.html",
            {
                "request": request,
                "dec": dec,
                "resumen": resumen,
                "resumen_json": resumen_json,
                "mi_rfc": MI_RFC,
                "payload": payload,
            },
        )
    finally:
        db.close()

@app.get("/declaraciones/{dec_id}/archivo.pdf")
def descargar_declaracion_pdf(dec_id: int):
    db = get_db()
    try:
        dec = db.get(DeclaracionPDF, dec_id)
        if not dec:
            return Response(content="No encontrada", status_code=404)
        pdf_path = (PDF_DIR / dec.filename)
        if not pdf_path.exists():
            return Response(content="Archivo PDF no encontrado en disco", status_code=404)
        return Response(
            content=pdf_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={dec.filename}"},
        )
    finally:
        db.close()



@app.get("/declaraciones/{dec_id}/resumen.json")
def declaracion_pdf_resumen_json(dec_id: int):
    """Exporta el resumen de una declaración como JSON."""
    db = get_db()
    try:
        dec = db.get(DeclaracionPDF, dec_id)
        if not dec:
            return Response(content="No encontrada", status_code=404)

        payload = _build_declaracion_payload(dec)
        return Response(
            content=serialize_to_json(payload),
            media_type="application/json; charset=utf-8",
        )
    finally:
        db.close()



@app.get("/facturas", response_class=HTMLResponse)
def listar_facturas(
    request: Request,
    year: Optional[str] = None,
    month: Optional[str] = None,
    tipo: Optional[str] = None,
    naturaleza: Optional[str] = None,
    msg: Optional[str] = None,
) -> HTMLResponse:
    """Lista CFDI de facturas con filtros opcionales."""
    db = get_db()
    try:
        month_options = _month_options(db)
        year_options = sorted({y for (y, _) in month_options}, reverse=True)

        year_i = int(year) if year and year.isdigit() else None
        month_i = int(month) if month and month.isdigit() else None

        months_for_year = (
            sorted({m for (y, m) in month_options if y == year_i})
            if year_i is not None
            else sorted({m for (_, m) in month_options})
        )

        q = select(Factura).order_by(desc(Factura.fecha_emision).nullslast(), desc(Factura.id))
        if year_i is not None:
            q = q.where(Factura.year_emision == year_i)
        if month_i is not None:
            q = q.where(Factura.month_emision == month_i)
        if tipo:
            q = q.where(Factura.tipo_comprobante == tipo.upper())
        if naturaleza:
            q = q.where(Factura.naturaleza == naturaleza.lower())

        facturas = db.scalars(q.limit(500)).all()

        sat_creds = _get_sat_credentials(db, MI_RFC)
        sat_ready = bool(sat_creds) and _credentials_ready(sat_creds) and _password_ready(sat_creds)

        sat_zips_q = db.query(SatCfdiZip).filter(SatCfdiZip.rfc == MI_RFC)
        if year_i is not None:
            sat_zips_q = sat_zips_q.filter(SatCfdiZip.year == year_i)
        if month_i is not None:
            sat_zips_q = sat_zips_q.filter(SatCfdiZip.month == month_i)
        sat_zips_raw = sat_zips_q.order_by(SatCfdiZip.created_at.desc()).all()
        now_utc = datetime.utcnow()
        sat_zips = [
            {
                "row": row,
                "can_delete": row.created_at + timedelta(hours=48) <= now_utc,
            }
            for row in sat_zips_raw
        ]

        wait_until = None
        if year_i is not None and month_i is not None:
            wait_until = _sat_wait_until(db, MI_RFC, year_i, month_i)
        return templates.TemplateResponse(
            "facturas.html",
            {
                "request": request,
                "facturas": facturas,
                "mi_rfc": MI_RFC,
                "tipo": tipo or "",
                "naturaleza": naturaleza or "",
                "year": year_i,
                "month": month_i,
                "year_options": year_options,
                "months_for_year": months_for_year,
                "sat_ready": sat_ready,
                "sat_zips": sat_zips,
                "sat_wait_until": wait_until,
                "msg": msg,
            },
        )
    finally:
        db.close()


@app.post("/facturas/sat_import")
def facturas_sat_import(
    year: str = Form(...),
    month: str = Form(...),
) -> Response:
    if not (year.isdigit() and month.isdigit()):
        return RedirectResponse(
            url=f"/facturas?msg=Selecciona+ano+y+mes+validos&year={year}&month={month}",
            status_code=303,
        )
    year_i = int(year)
    month_i = int(month)
    if month_i < 1 or month_i > 12:
        return RedirectResponse(
            url=f"/facturas?msg=Mes+invalido&year={year_i}&month={month_i}",
            status_code=303,
        )

    with SessionLocal() as db:
        try:
            def _stage(label: str, fn):
                try:
                    return fn()
                except Exception as exc:
                    raise RuntimeError(f"{label}: {exc}") from exc

            credentials = _get_sat_credentials(db, MI_RFC)
            if not credentials or not _credentials_ready(credentials) or not _password_ready(credentials):
                return RedirectResponse(
                    url=(
                        "/facturas?msg=Configura+credenciales+SAT+con+password"
                        f"&year={year_i}&month={month_i}"
                    ),
                    status_code=303,
                )

            wait_until = _sat_wait_until(db, MI_RFC, year_i, month_i)
            if wait_until and wait_until > datetime.utcnow():
                msg = f"Ya existe una descarga reciente. Espera hasta {wait_until.isoformat()}."
                return RedirectResponse(
                    url=f"/facturas?msg={msg}&year={year_i}&month={month_i}",
                    status_code=303,
                )

            password = decrypt_password(credentials.key_password)
            key_material = load_sat_key_material_from_bytes(
                credentials.cert_der,
                credentials.key_der,
                password,
            )
            endpoints = SatEndpoints.for_kind("cfdi")
            service = SatDescargaSoapService(endpoints)
            workflow = SatDescargaWorkflow(service=service, key_material=key_material)

            token = _stage(
                "Autenticacion",
                lambda: workflow.autenticar(
                    soap_action=SOAP_CFDI_ACTION_AUTENTICA,
                    to_url=endpoints.auth_url,
                    action=SOAP_CFDI_ACTION_AUTENTICA,
                ),
            )
            fecha_inicial, fecha_final = _build_period_range(year_i, month_i)

            stats = {"insertados": 0, "duplicados": 0, "omitidos": 0}
            paquetes_guardados = 0

            for tipo in ["emitidos", "recibidos"]:
                tag_name = "SolicitaDescargaEmitidos" if tipo == "emitidos" else "SolicitaDescargaRecibidos"
                soap_action = (
                    SOAP_CFDI_ACTION_SOLICITA_EMITIDOS
                    if tipo == "emitidos"
                    else SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS
                )
                params = SolicitudDescargaParams(
                    rfc_solicitante=MI_RFC,
                    rfc_emisor=MI_RFC if tipo == "emitidos" else None,
                    rfc_receptor=MI_RFC if tipo == "recibidos" else None,
                    fecha_inicial=fecha_inicial,
                    fecha_final=fecha_final,
                    tipo_solicitud="CFDI",
                    estado_comprobante="Vigente",
                    rfc_a_cuenta_terceros="",
                )
                solicitud_id = _stage(
                    f"Solicitud {tipo}",
                    lambda: workflow.solicitar_descarga(
                        params, access_token=token, soap_action=soap_action, tag_name=tag_name
                    ),
                )

                result = None
                for _ in range(10):
                    result = _stage(
                        f"Verificacion {tipo}",
                        lambda: workflow.verificar_descarga(
                            rfc_solicitante=MI_RFC,
                            id_solicitud=solicitud_id,
                            access_token=token,
                        ),
                    )
                    if result.estado_solicitud == "3":
                        break
                    time.sleep(10)

                if not result or result.estado_solicitud != "3":
                    continue

            for paquete_id in result.paquetes:
                zip_bytes = _stage(
                    f"Descarga {tipo}",
                    lambda: workflow.descargar_paquete(
                        rfc_solicitante=MI_RFC,
                        id_paquete=paquete_id,
                        access_token=token,
                    ),
                )
                zip_path = _zip_storage_path(MI_RFC, year_i, month_i, tipo, paquete_id)
                zip_path.write_bytes(zip_bytes)

                existing = (
                    db.query(SatCfdiZip)
                    .filter(SatCfdiZip.rfc == MI_RFC, SatCfdiZip.paquete_id == paquete_id)
                    .one_or_none()
                )
                if existing:
                    existing.zip_filename = zip_path.name
                else:
                    db.add(
                        SatCfdiZip(
                            rfc=MI_RFC,
                            year=year_i,
                            month=month_i,
                            tipo=tipo,
                            solicitud_id=solicitud_id,
                            paquete_id=paquete_id,
                            zip_filename=zip_path.name,
                        )
                    )
                db.commit()
                paquetes_guardados += 1

                with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                    for name in zf.namelist():
                        if not name.lower().endswith(".xml"):
                            continue
                        _import_cfdi_xml_bytes(db, zf.read(name), stats)

            msg = (
                f"SAT: {paquetes_guardados} zip guardados. "
                f"XML insertados: {stats['insertados']}, duplicados: {stats['duplicados']}, "
                f"omitidos: {stats['omitidos']}."
            )
            return RedirectResponse(
                url=f"/facturas?year={year_i}&month={month_i}&msg={msg}",
                status_code=303,
            )
        except Exception as exc:
            msg = str(exc)[:400].replace(" ", "+")
            return RedirectResponse(
                url=f"/facturas?msg=Error+SAT:+{msg}&year={year_i}&month={month_i}",
                status_code=303,
            )


@app.get("/facturas/sat_zips/{zip_id}")
def facturas_sat_zip_download(zip_id: int) -> Response:
    with SessionLocal() as db:
        row = db.get(SatCfdiZip, zip_id)
        if not row or row.rfc != MI_RFC:
            raise HTTPException(status_code=404, detail="Zip no encontrado.")
        zip_path = ZIP_DIR / row.zip_filename
        if not zip_path.exists():
            raise HTTPException(status_code=404, detail="Archivo zip no encontrado.")
        data = zip_path.read_bytes()
    headers = {"Content-Disposition": f'attachment; filename="{row.zip_filename}"'}
    return Response(content=data, media_type="application/zip", headers=headers)


@app.post("/facturas/sat_zips/{zip_id}/delete")
def facturas_sat_zip_delete(zip_id: int) -> Response:
    with SessionLocal() as db:
        row = db.get(SatCfdiZip, zip_id)
        if not row or row.rfc != MI_RFC:
            return RedirectResponse(url="/facturas?msg=Zip+no+encontrado", status_code=303)
        if row.created_at + timedelta(hours=48) > datetime.utcnow():
            return RedirectResponse(
                url="/facturas?msg=No+puedes+eliminar+antes+de+48h", status_code=303
            )
        zip_path = ZIP_DIR / row.zip_filename
        db.delete(row)
        db.commit()
    if zip_path.exists():
        zip_path.unlink()
    return RedirectResponse(url="/facturas?msg=Zip+eliminado", status_code=303)



@app.get("/retenciones", response_class=HTMLResponse)
def listar_retenciones(
    request: Request,
    period: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> HTMLResponse:
    """Lista retenciones de plataforma con filtros opcionales."""
    db = get_db()
    try:
        # Obtener periodos disponibles
        opts_raw = db.execute(
            select(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_ini, RetencionPlataforma.mes_fin)
            .where(
                RetencionPlataforma.ejercicio.isnot(None),
                RetencionPlataforma.mes_fin.isnot(None),
            )
            .group_by(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_ini, RetencionPlataforma.mes_fin)
        ).all()

        periods: set[tuple[int, int]] = set()
        for y, mi, mf in opts_raw:
            if not y or not mf:
                continue
            y_i = int(y)
            mi_i = int(mi or mf)
            mf_i = int(mf)
            if mi_i <= mf_i:
                for mm in range(mi_i, mf_i + 1):
                    periods.add((y_i, int(mm)))
            else:
                periods.add((y_i, mf_i))

        period_options = [f"{y}-{m:02d}" for (y, m) in sorted(periods, reverse=True)]

        selected_period = (period or "").strip()
        if selected_period and re.match(r"^\d{4}-\d{2}$", selected_period):
            try:
                year = int(selected_period.split("-")[0])
                month = int(selected_period.split("-")[1])
            except Exception:
                pass

        q = (
            select(RetencionPlataforma)
            .order_by(
                desc(RetencionPlataforma.ejercicio),
                desc(RetencionPlataforma.mes_fin),
                desc(RetencionPlataforma.fecha_exp).nullslast(),
                desc(RetencionPlataforma.id),
            )
            .limit(300)
        )
        if year is not None:
            q = q.where(RetencionPlataforma.ejercicio == year)
        if month is not None:
            q = q.where(and_(RetencionPlataforma.mes_ini <= month, RetencionPlataforma.mes_fin >= month))

        rows = db.scalars(q).all()
        return templates.TemplateResponse(
            "retenciones.html",
            {
                "request": request,
                "rows": rows,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "period_options": period_options,
                "selected_period": selected_period,
            },
        )
    finally:
        db.close()


@app.get("/retenciones/{ret_id}", response_class=HTMLResponse)
def detalle_retencion(request: Request, ret_id: int) -> HTMLResponse:
    db = get_db()
    try:
        ret = db.get(RetencionPlataforma, ret_id)
        if not ret:
            return HTMLResponse("No encontrada", status_code=404)
        return templates.TemplateResponse("retencion_detalle.html", {"request": request, "ret": ret, "mi_rfc": MI_RFC})
    finally:
        db.close()


@app.get("/facturas/{factura_id}", response_class=HTMLResponse)
def detalle_factura(request: Request, factura_id: int) -> HTMLResponse:
    db = get_db()
    try:
        factura = db.get(Factura, factura_id)
        if not factura:
            return HTMLResponse("No encontrada", status_code=404)
        _ = factura.conceptos
        _ = factura.pagos
        return templates.TemplateResponse("detalle.html", {"request": request, "factura": factura, "mi_rfc": MI_RFC})
    finally:
        db.close()


def _signed(value: Optional[float], tipo: Optional[str]) -> float:
    """Aplica factor de signo: tipo 'E' (egreso) multiplica por -1."""
    return apply_sign_factor(value, tipo)


def _pick_default_period(db: Session) -> tuple[Optional[int], Optional[int]]:
    """Obtiene el periodo más reciente con datos (facturas o retenciones)."""
    last_fact = db.execute(
        select(Factura.year_emision, Factura.month_emision)
        .where(Factura.year_emision.isnot(None), Factura.month_emision.isnot(None))
        .order_by(desc(Factura.year_emision), desc(Factura.month_emision))
        .limit(1)
    ).first()

    last_ret = db.execute(
        select(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_fin)
        .where(RetencionPlataforma.ejercicio.isnot(None), RetencionPlataforma.mes_fin.isnot(None))
        .order_by(desc(RetencionPlataforma.ejercicio), desc(RetencionPlataforma.mes_fin))
        .limit(1)
    ).first()

    candidates = []
    if last_fact:
        candidates.append((int(last_fact[0]), int(last_fact[1])))
    if last_ret:
        candidates.append((int(last_ret[0]), int(last_ret[1])))

    return max(candidates) if candidates else (None, None)


def _month_options(db: Session) -> list[tuple[int, int]]:
    """Obtiene lista de periodos disponibles (año, mes) ordenados descendentemente."""
    m1 = db.execute(
        select(Factura.year_emision, Factura.month_emision)
        .where(Factura.year_emision.isnot(None), Factura.month_emision.isnot(None))
        .group_by(Factura.year_emision, Factura.month_emision)
    ).all()

    m2 = db.execute(
        select(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_fin)
        .where(RetencionPlataforma.ejercicio.isnot(None), RetencionPlataforma.mes_fin.isnot(None))
        .group_by(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_fin)
    ).all()

    return sorted({(int(y), int(m)) for (y, m) in (m1 + m2) if y and m}, reverse=True)


def _compute_period_data(db: Session, year: int, month: int) -> dict:
    """
    Calcula todos los datos agregados de un periodo para reportes.
    
    Returns:
        Dict con ingresos, gastos, retenciones, IVA, etc.
    """
    # CFDI por emisión
    docs = db.scalars(
        select(Factura)
        .where(Factura.year_emision == year, Factura.month_emision == month)
        .order_by(desc(Factura.fecha_emision).nullslast(), desc(Factura.id))
    ).all()

    # Precargar relaciones
    for d in docs:
        _ = d.pagos

    # Inicializar acumuladores
    ingresos_total = ingresos_trasl = ingresos_ret = 0.0
    gastos_total = gastos_trasl = gastos_ret = 0.0
    ingresos_base = 0.0
    p_count = 0

    # Procesar CFDI de ingresos y gastos (excluyendo tipo P)
    for d in docs:
        tipo = (d.tipo_comprobante or "").upper()
        if tipo == "P":
            p_count += 1
            continue

        base = float(d.subtotal or 0.0) - float(d.descuento or 0.0)

        if d.naturaleza == "ingreso":
            ingresos_total += _signed(d.total, tipo)
            ingresos_trasl += _signed(d.total_trasladados, tipo)
            ingresos_ret += _signed(d.total_retenidos, tipo)
            ingresos_base += _signed(base, tipo)
        elif d.naturaleza == "gasto":
            gastos_total += _signed(d.total, tipo)
            gastos_trasl += _signed(d.total_trasladados, tipo)
            gastos_ret += _signed(d.total_retenidos, tipo)

    # Pagos (tipo P) por FechaPago
    pagos_rows = db.execute(
        select(Pago, Factura.naturaleza)
        .join(Factura, Pago.factura_id == Factura.id)
        .where(Pago.year_pago == year, Pago.month_pago == month)
        .order_by(desc(Pago.fecha_pago).nullslast(), desc(Pago.id))
    ).all()

    cash_in = cash_out = 0.0
    pagos_count = 0
    for pago, nat in pagos_rows:
        pagos_count += 1
        monto = float(pago.monto or 0.0)
        if nat == "cobro":
            cash_in += monto
        elif nat == "pago":
            cash_out += monto

    # Retenciones de plataformas
    ret_rows = db.scalars(
        select(RetencionPlataforma)
        .where(
            RetencionPlataforma.ejercicio == year,
            RetencionPlataforma.mes_ini <= month,
            RetencionPlataforma.mes_fin >= month,
        )
        .order_by(desc(RetencionPlataforma.fecha_exp).nullslast(), desc(RetencionPlataforma.id))
    ).all()

    plat_ing_siva = sum(float(r.mon_tot_serv_siva or 0.0) for r in ret_rows)
    plat_iva_tras = sum(float(r.total_iva_trasladado or 0.0) for r in ret_rows)
    plat_iva_ret = sum(float(r.total_iva_retenido or 0.0) for r in ret_rows)
    plat_isr_ret = sum(float(r.total_isr_retenido or 0.0) for r in ret_rows)
    plat_comision = sum(float(r.mon_total_por_uso_plataforma or 0.0) for r in ret_rows)

    return {
        "docs": docs,
        "pagos_rows": pagos_rows,
        "ret_rows": ret_rows,
        "ingresos_total": ingresos_total,
        "ingresos_base": ingresos_base,
        "ingresos_trasl": ingresos_trasl,
        "ingresos_ret": ingresos_ret,
        "gastos_total": gastos_total,
        "gastos_trasl": gastos_trasl,
        "gastos_ret": gastos_ret,
        "p_count": p_count,
        "cash_in": cash_in,
        "cash_out": cash_out,
        "pagos_count": pagos_count,
        "plat_ing_siva": plat_ing_siva,
        "plat_iva_tras": plat_iva_tras,
        "plat_iva_ret": plat_iva_ret,
        "plat_isr_ret": plat_isr_ret,
        "plat_comision": plat_comision,
    }


def _calc_income_and_iva_sources(
    data: dict, income_source: Optional[str]
) -> tuple[float, float, str]:
    """
    Calcula ingresos e IVA evitando doble conteo (plataforma vs CFDI).

    Returns:
        (ingresos_sin_iva, iva_trasladado, effective_source)
    """
    income_source = (income_source or "auto").lower().strip()

    plat_income = float(data.get("plat_ing_siva") or 0.0)
    cfdi_income = float(data.get("ingresos_base") or 0.0)

    plat_iva_tras = float(data.get("plat_iva_tras") or 0.0)
    cfdi_iva_tras = float(data.get("ingresos_trasl") or 0.0)

    if income_source == "plataforma":
        return plat_income, plat_iva_tras, "plataforma"
    elif income_source == "cfdi":
        return cfdi_income, cfdi_iva_tras, "cfdi"
    elif income_source == "ambos":
        return plat_income + cfdi_income, plat_iva_tras + cfdi_iva_tras, "ambos"
    else:
        # auto: preferir plataforma si existen datos para evitar doble conteo
        if plat_income > 0 or plat_iva_tras > 0:
            return plat_income, plat_iva_tras, "plataforma"
        else:
            return cfdi_income, cfdi_iva_tras, "cfdi"


def _build_hoja_sat_text(
    year: int, month: int, income_source: Optional[str], data: dict
) -> tuple[str, str]:
    """
    Construye texto de hoja SAT para copiar/pegar a la declaración.

    Returns:
        (texto_hoja_sat, effective_source_usado)
    """
    ingresos_sin_iva, iva_trasladado, effective = _calc_income_and_iva_sources(data, income_source)

    isr_retenido = float(data.get("plat_isr_ret") or 0.0)
    iva_retenido = float(data.get("plat_iva_ret") or 0.0)
    iva_acreditable = float(data.get("gastos_trasl") or 0.0)

    iva_neto_sugerido = iva_trasladado - iva_acreditable - iva_retenido

    def fmt(x: float) -> str:
        return format_money(x)

    text = "\n".join([
        f"PERIODO: {year}-{month:02d}",
        f"FUENTE_INGRESOS: {effective.upper()} (selector: {income_source})",
        "",
        "ISR (Pago provisional)",
        f"- Ingresos del periodo (sin IVA): {fmt(ingresos_sin_iva)}",
        f"- ISR retenido (plataforma): {fmt(isr_retenido)}",
        "",
        "IVA (Mensual)",
        f"- IVA trasladado del periodo: {fmt(iva_trasladado)}",
        f"- IVA retenido (plataforma): {fmt(iva_retenido)}",
        f"- IVA acreditable (gastos CFDI): {fmt(iva_acreditable)}",
        "",
        "CONTROLES",
        f"- IVA neto sugerido: {fmt(iva_neto_sugerido)}",
        "",
        "NOTAS",
        "- Si CFDI de ingreso = mismas ventas de plataforma, evita sumarlas.",
    ])
    return text, effective



def _checklist(
    db: Session, year: int, month: int, data: dict, income_source: str, effective_income_source: str
) -> list[dict]:
    """
    Genera checklist de validaciones para el periodo.

    Returns:
        Lista de dicts con {"level", "title", "detail"}
    """
    checks = []
    ret_rows = data["ret_rows"]
    docs = data["docs"]

    # 1. Retenciones presentes
    if not ret_rows:
        checks.append({
            "level": "error",
            "title": "Falta XML de retenciones de plataformas",
            "detail": "Sin este XML, no podrás acreditar ISR/IVA retenido.",
        })
    else:
        checks.append({
            "level": "ok",
            "title": "Retenciones de plataformas encontradas",
            "detail": f"Se detectaron {len(ret_rows)} XML(s) de retenciones.",
        })

    # 2. RFC receptor coincide
    if ret_rows:
        receivers = sorted({(r.receptor_rfc or "").upper() for r in ret_rows if r.receptor_rfc})
        if receivers and (MI_RFC or "").upper() not in receivers:
            checks.append({
                "level": "warn",
                "title": "RFC receptor no coincide",
                "detail": f"Receptores en XML: {', '.join(receivers)}",
            })
        else:
            checks.append({
                "level": "ok",
                "title": "RFC receptor coincide",
                "detail": "El RFC del receptor coincide con tu configuración.",
            })

    # 3. Periodo mensual
    bad_ranges = [r for r in ret_rows if (r.mes_ini or 0) != (r.mes_fin or 0)]
    if bad_ranges:
        checks.append({
            "level": "warn",
            "title": "Retención con rango de meses",
            "detail": "Hay XML donde MesIni != MesFin.",
        })

    # 4. Gastos con UsoCFDI
    missing_uso = [
        d for d in docs
        if d.naturaleza == "gasto"
        and not (d.uso_cfdi or "").strip()
        and (d.tipo_comprobante or "").upper() != "P"
    ]
    if missing_uso:
        checks.append({
            "level": "warn",
            "title": f"Hay {len(missing_uso)} gastos sin UsoCFDI",
            "detail": "Revisa esos XML para completar el campo.",
        })
    else:
        checks.append({
            "level": "ok",
            "title": "UsoCFDI en gastos",
            "detail": "Tus CFDI de gastos traen UsoCFDI o no hay gastos.",
        })

    # 5. Gastos ausentes
    gastos_count = sum(1 for d in docs if d.naturaleza == "gasto" and (d.tipo_comprobante or "").upper() != "P")
    if gastos_count == 0:
        checks.append({
            "level": "warn",
            "title": "No hay CFDI de gastos",
            "detail": "Sin gastos no podrás acreditar IVA ni deducirlos.",
        })

    # 6. Control de doble conteo
    ingresos_count = sum(
        1 for d in docs if d.naturaleza == "ingreso" and (d.tipo_comprobante or "").upper() != "P"
    )
    if ret_rows and ingresos_count > 0 and data["ingresos_base"] > 0:
        if effective_income_source in ["plataforma", "cfdi"]:
            checks.append({
                "level": "info",
                "title": "Doble fuente detectada",
                "detail": f"Usando: {effective_income_source.upper()}",
            })

    # 7. CFDI tipo P sin pagos
    p_no_pagos = [d for d in docs if (d.tipo_comprobante or "").upper() == "P" and len(d.pagos) == 0]
    if p_no_pagos:
        checks.append({
            "level": "warn",
            "title": f"{len(p_no_pagos)} CFDI tipo P sin renglones <Pago>",
            "detail": "Puede ser XML incompleto o namespace distinto.",
        })

    # 8. Moneda no MXN
    other_cur = sorted(
        {(d.moneda or "").upper() for d in docs if d.moneda and (d.moneda or "").upper() != "MXN"}
    )
    if other_cur:
        checks.append({
            "level": "info",
            "title": f"Moneda distinta: {', '.join(other_cur)}",
            "detail": "Debes convertir a MXN con tipo de cambio.",
        })

    return checks


@app.get("/summary", response_class=HTMLResponse)
def resumen_mensual(
    request: Request,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> HTMLResponse:
    """Resumen de ingresos, gastos, retenciones e IVA de un periodo."""
    db = get_db()
    try:
        if year is None or month is None:
            year, month = _pick_default_period(db)

        if year is None or month is None:
            return templates.TemplateResponse("empty.html", {"request": request, "mi_rfc": MI_RFC})

        month_options = _month_options(db)
        year_options = sorted({y for (y, _) in month_options}, reverse=True)
        months_for_year = sorted({m for (y, m) in month_options if y == year})

        data = _compute_period_data(db, year, month)

        # Cálculos de IVA sugerido
        iva_causado_sugerido = data["plat_iva_tras"] + data["ingresos_trasl"]
        iva_acreditable_sugerido = data["gastos_trasl"]
        iva_retenido_plat = data["plat_iva_ret"]
        iva_neto_sugerido = iva_causado_sugerido - iva_acreditable_sugerido - iva_retenido_plat

        return templates.TemplateResponse(
            "summary.html",
            {
                "request": request,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "month_options": month_options,
                "year_options": year_options,
                "months_for_year": months_for_year,
                **data,
                "iva_causado_sugerido": iva_causado_sugerido,
                "iva_acreditable_sugerido": iva_acreditable_sugerido,
                "iva_retenido_plat": iva_retenido_plat,
                "iva_neto_sugerido": iva_neto_sugerido,
            },
        )
    finally:
        db.close()


@app.get("/declaracion", response_class=HTMLResponse)
def modo_declaracion(
    request: Request,
    year: Optional[int] = None,
    month: Optional[int] = None,
    income_source: str = "auto",
) -> HTMLResponse:
    """
    Modo declaración: ingresos, retenciones, IVA sin coeficiente.
    
    Args:
        income_source: "auto"|"plataforma"|"cfdi"|"ambos" - evita doble conteo
    """
    db = get_db()
    try:
        if year is None or month is None:
            year, month = _pick_default_period(db)

        if year is None or month is None:
            return templates.TemplateResponse("empty.html", {"request": request, "mi_rfc": MI_RFC})

        month_options = _month_options(db)
        year_options = sorted({y for (y, _) in month_options}, reverse=True)
        months_for_year = sorted({m for (y, m) in month_options if y == year})

        data = _compute_period_data(db, year, month)

        # Calcular ingresos e IVA evitando doble conteo
        ingresos_total_sin_iva, iva_trasladado_total, effective_income_source = (
            _calc_income_and_iva_sources(data, income_source)
        )

        isr_retenido = float(data.get("plat_isr_ret") or 0.0)
        iva_retenido = float(data.get("plat_iva_ret") or 0.0)

        checks = _checklist(db, year, month, data, income_source, effective_income_source)

        # Obtener declaración PDF si existe
        declaracion_pdf = db.scalars(
            select(DeclaracionPDF)
            .where(DeclaracionPDF.year == year, DeclaracionPDF.month == month)
            .order_by(desc(DeclaracionPDF.created_at))
            .limit(1)
        ).first()

        acuse_payload = None
        acuse_checks: list[dict] = []
        if declaracion_pdf and (declaracion_pdf.text_excerpt or "").strip():
            try:
                acuse_payload = parse_sat_declaracion_summary(declaracion_pdf.text_excerpt or "")
            except Exception:
                pass

        return templates.TemplateResponse(
            "declaracion.html",
            {
                "request": request,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "month_options": month_options,
                "year_options": year_options,
                "months_for_year": months_for_year,
                "income_source": income_source,
                "effective_income_source": effective_income_source,
                **data,
                "ingresos_total_sin_iva": ingresos_total_sin_iva,
                "isr_retenido": isr_retenido,
                "iva_retenido": iva_retenido,
                "iva_trasladado_total": iva_trasladado_total,
                "checks": checks,
                "declaracion_pdf": declaracion_pdf,
                "acuse_payload": acuse_payload,
                "acuse_checks": acuse_checks,
            },
        )
    finally:
        db.close()
@app.get("/sat_hoja.txt")
def sat_hoja_txt(year: int, month: int, income_source: str = "auto"):
    """Exporta hoja SAT como texto plano."""
    db = get_db()
    try:
        data = _compute_period_data(db, year, month)
        hoja_text, effective = _build_hoja_sat_text(year, month, income_source, data)
        return Response(
            content=hoja_text,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=hoja_sat_{year}_{month:02d}_{effective}.txt"},
        )
    finally:
        db.close()


@app.get("/sat_hoja", response_class=HTMLResponse)
def sat_hoja_view(
    request: Request,
    year: int,
    month: int,
    income_source: str = "auto",
) -> HTMLResponse:
    """Vista HTML de hoja SAT con texto para copiar/pegar."""
    db = get_db()
    try:
        data = _compute_period_data(db, year, month)
        hoja_text, effective = _build_hoja_sat_text(year, month, income_source, data)
        return templates.TemplateResponse(
            "sat_hoja.html",
            {
                "request": request,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "income_source": income_source,
                "effective_income_source": effective,
                "hoja_text": hoja_text,
            },
        )
    finally:
        db.close()


@app.get("/sat_report.csv")
def sat_report_csv(year: int, month: int, income_source: str = "auto"):
    """Genera CSV de papel de trabajo mensual."""
    db = get_db()
    try:
        data = _compute_period_data(db, year, month)

        ingresos_total_sin_iva, iva_tras_total, effective_income_source = (
            _calc_income_and_iva_sources(data, income_source)
        )

        iva_causado = iva_tras_total
        iva_acreditable = data["gastos_trasl"]
        iva_neto = iva_causado - iva_acreditable - data["plat_iva_ret"]

        import csv
        import io

        out = io.StringIO()
        w = csv.writer(out)
        w.writerow([
            "periodo",
            "ingresos_plataforma_sin_iva",
            "ingresos_cfdi_sin_iva_aprox",
            "ingresos_total_sin_iva",
            "isr_retenido_plataforma",
            "iva_trasladado_plataforma",
            "iva_retenido_plataforma",
            "iva_trasladado_cfdi",
            "iva_acreditable_gastos_cfdi",
            "iva_neto_sugerido",
            "fuente_ingresos",
        ])
        w.writerow([
            f"{year}-{month:02d}",
            f"{data['plat_ing_siva']:.2f}",
            f"{data['ingresos_base']:.2f}",
            f"{ingresos_total_sin_iva:.2f}",
            f"{data['plat_isr_ret']:.2f}",
            f"{data['plat_iva_tras']:.2f}",
            f"{data['plat_iva_ret']:.2f}",
            f"{data['ingresos_trasl']:.2f}",
            f"{data['gastos_trasl']:.2f}",
            f"{iva_neto:.2f}",
            income_source,
        ])

        return Response(
            content=out.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=sat_report_{year}_{month:02d}.csv"},
        )
    finally:
        db.close()
