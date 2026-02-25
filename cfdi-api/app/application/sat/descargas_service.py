from __future__ import annotations

import io
import logging
import zipfile
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import ConceptoModel, FacturaModel, PagoModel, RetencionModel
from app.adapters.outbound.db.repositories.facturas import SqlFacturaRepository
from app.adapters.outbound.db.repositories.platform_rfcs import SqlPlatformRfcRepository
from app.adapters.outbound.db.repositories.retenciones import SqlRetencionRepository
from app.adapters.outbound.files.storage_factory import build_storage
from app.adapters.services.parsers.xml_parser import LocalXmlParser
from app.application.imports.facturas import (
    create_factura_from_parsed,
    create_retencion_from_parsed,
)
from app.application.sat.dto import SolicitudDescargaParams, VerificacionResult
from app.domain.sat.entities import SatDescarga
from app.ports.sat_credentials_repo import SatCredentialsRepository
from app.ports.sat_crypto import SatCrypto
from app.ports.sat_descargas_repo import SatDescargasRepository
from app.ports.sat_gateway import SatGateway
from app.ports.sat_storage import SatStorage

logger = logging.getLogger(__name__)

STATUS_SOLICITADA = "SOLICITADA"
STATUS_EN_PROCESO = "EN_PROCESO"
STATUS_LISTA = "LISTA"
STATUS_DESCARGANDO = "DESCARGANDO"
STATUS_COMPLETADA = "COMPLETADA"
STATUS_SIN_RESULTADOS = "SIN_RESULTADOS"
STATUS_EXPIRADA = "EXPIRADA"
STATUS_ERROR = "ERROR"


def crear_solicitud_descarga(
    repo: SatDescargasRepository,
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    rfc: str,
    kind: str,
    params: SolicitudDescargaParams,
    soap_action: str | None = None,
    tag_name: str = "SolicitaDescargaEmitidos",
) -> SatDescarga:
    key_material, token = _authenticate(cred_repo, crypto, gateway, rfc, kind)
    solicitud = gateway.solicitar_descarga(
        kind=kind,
        key_material=key_material,
        params=params,
        access_token=token,
        soap_action=soap_action,
        tag_name=tag_name,
    )
    if not solicitud.id_solicitud:
        raise ValueError(solicitud.mensaje or "Respuesta sin IdSolicitud.")
    now = datetime.now(timezone.utc)
    return repo.create(
        rfc=rfc,
        kind=kind,
        tipo_solicitud=params.tipo_solicitud,
        anio_filtro=params.fecha_inicial.year if params.fecha_inicial else None,
        mes_filtro=params.fecha_inicial.month if params.fecha_inicial else None,
        id_solicitud=solicitud.id_solicitud,
        estado=STATUS_SOLICITADA,
        codigo_estado=solicitud.codigo_estado,
        mensaje_estado=solicitud.mensaje,
        paquetes=[],
        link_descarga=None,
        zip_path=None,
        attempts=0,
        next_check_at=now,
    )


def verificar_descarga(
    repo: SatDescargasRepository,
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    descarga_id: int,
    soap_action: str | None = None,
) -> SatDescarga | None:
    descarga = repo.get_by_id(descarga_id)
    if not descarga or not descarga.id_solicitud:
        return None

    key_material, token = _authenticate(cred_repo, crypto, gateway, descarga.rfc, descarga.kind)
    result = gateway.verificar_descarga(
        kind=descarga.kind,
        key_material=key_material,
        rfc_solicitante=descarga.rfc,
        id_solicitud=descarga.id_solicitud,
        access_token=token,
        soap_action=soap_action,
    )

    estado = _map_estado(result)
    attempts = descarga.attempts + 1 if estado in {STATUS_EN_PROCESO} else descarga.attempts
    next_check_at = _next_check_at(attempts) if estado == STATUS_EN_PROCESO else None
    link_descarga = descarga.link_descarga
    if estado == STATUS_LISTA:
        link_descarga = link_descarga or f"/api/v1/sat/descargas/{descarga.id}/zip"

    return repo.update(
        descarga.id,
        estado=estado,
        paquetes=result.paquetes or [],
        attempts=attempts,
        next_check_at=next_check_at,
        link_descarga=link_descarga,
        codigo_estado=result.codigo_estado,
        mensaje_estado=result.mensaje,
    )


def descargar_y_procesar(
    repo: SatDescargasRepository,
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    storage: SatStorage | None,
    db: Session,
    descarga_id: int,
    soap_action: str | None = None,
) -> SatDescarga | None:
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        return None
    if not descarga.paquetes:
        return repo.update(descarga.id, estado=STATUS_SIN_RESULTADOS, next_check_at=None)

    repo.update(descarga.id, estado=STATUS_DESCARGANDO)

    key_material, token = _authenticate(cred_repo, crypto, gateway, descarga.rfc, descarga.kind)
    storage = storage or build_storage()
    last_zip_path: str | None = None

    for id_paquete in descarga.paquetes:
        descarga_result = gateway.descargar_paquete(
            kind=descarga.kind,
            key_material=key_material,
            rfc_solicitante=descarga.rfc,
            id_paquete=id_paquete,
            access_token=token,
            soap_action=soap_action,
        )
        if not descarga_result.zip_bytes:
            return repo.update(
                descarga.id,
                estado=STATUS_ERROR,
                codigo_estado=descarga_result.codigo_estado,
                mensaje_estado=descarga_result.mensaje,
            )
        last_zip_path = storage.save_zip(descarga.rfc, id_paquete, descarga_result.zip_bytes)
        _process_zip_xml(db, descarga_result.zip_bytes)

    return repo.update(
        descarga.id,
        estado=STATUS_COMPLETADA,
        zip_path=last_zip_path if len(descarga.paquetes) == 1 else descarga.zip_path,
    )


def _authenticate(
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    rfc: str,
    kind: str,
) -> tuple[object, str]:
    cred = cred_repo.get_by_rfc(rfc)
    if not cred:
        raise ValueError("RFC sin credenciales.")
    password = crypto.decrypt_text(cred.pfx_password_encrypted)
    pfx_bytes = crypto.decrypt_bytes(cred.pfx_encrypted)
    key_material = gateway.load_key_material(pfx_bytes, password)
    token = gateway.autenticar(kind=kind, key_material=key_material)
    return key_material, token


def _map_estado(result: VerificacionResult) -> str:
    estado_raw = (result.estado_solicitud or "").strip().upper()
    if result.paquetes:
        return STATUS_LISTA
    if estado_raw in {"1", "EN PROCESO", "EN_PROCESO"}:
        return STATUS_EN_PROCESO
    if estado_raw in {"2", "TERMINADA", "TERMINADO"}:
        return STATUS_SIN_RESULTADOS
    if estado_raw in {"3", "RECHAZADA", "RECHAZADO", "ERROR"}:
        return STATUS_ERROR
    if estado_raw in {"4", "VENCIDA", "EXPIRADA", "EXPIRADO"}:
        return STATUS_EXPIRADA
    return STATUS_EN_PROCESO


def _next_check_at(attempts: int) -> datetime:
    now = datetime.now(timezone.utc)
    if attempts <= 5:
        return now + timedelta(minutes=1)
    if attempts <= 12:
        return now + timedelta(minutes=5)
    if attempts <= 20:
        return now + timedelta(minutes=15)
    return now + timedelta(minutes=60)


def _process_zip_xml(db: Session, zip_bytes: bytes) -> None:
    parser = LocalXmlParser()
    factura_repo = SqlFacturaRepository(db)
    ret_repo = SqlRetencionRepository(db)
    platform_repo = SqlPlatformRfcRepository(db)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".xml"):
                continue
            try:
                xml_bytes = zf.read(name)
                kind = parser.detect_kind(xml_bytes)

                if kind == "cfdi":
                    parsed = parser.parse_cfdi(xml_bytes)
                    uuid = parsed.get("uuid")
                    parsed["xml_text"] = xml_bytes.decode("utf-8", errors="replace")
                    if uuid and factura_repo.exists_uuid(uuid):
                        model = db.execute(
                            select(FacturaModel).where(FacturaModel.uuid == uuid)
                        ).scalar_one_or_none()
                        if model is not None:
                            _update_factura_model(model, parsed)
                            db.commit()
                        continue
                    factura = create_factura_from_parsed(parsed)
                    factura_repo.add_factura(factura)
                elif kind == "retenciones":
                    parsed = parser.parse_retenciones(xml_bytes)
                    uuid = parsed.get("uuid")
                    parsed["xml_text"] = xml_bytes.decode("utf-8", errors="replace")
                    if uuid and ret_repo.exists_uuid(uuid):
                        model = db.execute(
                            select(RetencionModel).where(RetencionModel.uuid == uuid)
                        ).scalar_one_or_none()
                        if model is not None:
                            _update_retencion_model(model, parsed)
                            db.commit()
                        _upsert_platform_rfc(platform_repo, parsed)
                        continue
                    retencion = create_retencion_from_parsed(parsed)
                    ret_repo.add_retencion(retencion)
                    _upsert_platform_rfc(platform_repo, parsed)
            except Exception:
                db.rollback()
                logger.exception("Error al procesar XML en ZIP (name=%s)", name)


def _update_factura_model(model: FacturaModel, parsed: dict) -> None:
    model.uuid = parsed.get("uuid")
    model.version = parsed.get("version")
    model.tipo_comprobante = parsed.get("tipo_comprobante")
    model.fecha_emision = parsed.get("fecha_emision")
    model.year_emision = parsed.get("year_emision")
    model.month_emision = parsed.get("month_emision")
    model.naturaleza = parsed.get("naturaleza")
    model.emisor_rfc = parsed.get("emisor_rfc")
    model.emisor_nombre = parsed.get("emisor_nombre")
    model.receptor_rfc = parsed.get("receptor_rfc")
    model.receptor_nombre = parsed.get("receptor_nombre")
    model.uso_cfdi = parsed.get("uso_cfdi")
    model.moneda = parsed.get("moneda")
    model.metodo_pago = parsed.get("metodo_pago")
    model.forma_pago = parsed.get("forma_pago")
    model.subtotal = parsed.get("subtotal")
    model.descuento = parsed.get("descuento")
    model.total = parsed.get("total")
    model.total_trasladados = parsed.get("total_trasladados")
    model.total_retenidos = parsed.get("total_retenidos")
    model.xml_text = parsed.get("xml_text", "")

    model.conceptos = [
        ConceptoModel(
            clave_prod_serv=c.get("clave_prod_serv"),
            cantidad=c.get("cantidad"),
            clave_unidad=c.get("clave_unidad"),
            descripcion=c.get("descripcion"),
            valor_unitario=c.get("valor_unitario"),
            importe=c.get("importe"),
            objeto_imp=c.get("objeto_imp"),
        )
        for c in parsed.get("conceptos", [])
    ]
    model.pagos = [
        PagoModel(
            fecha_pago=p.get("fecha_pago"),
            year_pago=p.get("year_pago"),
            month_pago=p.get("month_pago"),
            monto=p.get("monto"),
            moneda_p=p.get("moneda_p"),
            forma_pago_p=p.get("forma_pago_p"),
        )
        for p in parsed.get("pagos", [])
    ]


def _update_retencion_model(model: RetencionModel, parsed: dict) -> None:
    model.uuid = parsed.get("uuid")
    model.version = parsed.get("version")
    model.fecha_exp = parsed.get("fecha_exp")
    model.ejercicio = parsed.get("ejercicio")
    model.mes_ini = parsed.get("mes_ini")
    model.mes_fin = parsed.get("mes_fin")
    model.emisor_rfc = parsed.get("emisor_rfc")
    model.emisor_nombre = parsed.get("emisor_nombre")
    model.receptor_rfc = parsed.get("receptor_rfc")
    model.receptor_nombre = parsed.get("receptor_nombre")
    model.monto_tot_operacion = parsed.get("monto_tot_operacion")
    model.monto_tot_grav = parsed.get("monto_tot_grav")
    model.monto_tot_exent = parsed.get("monto_tot_exent")
    model.monto_tot_ret = parsed.get("monto_tot_ret")
    model.periodicidad = parsed.get("periodicidad")
    model.num_serv = parsed.get("num_serv")
    model.mon_tot_serv_siva = parsed.get("mon_tot_serv_siva")
    model.total_iva_trasladado = parsed.get("total_iva_trasladado")
    model.total_iva_retenido = parsed.get("total_iva_retenido")
    model.total_isr_retenido = parsed.get("total_isr_retenido")
    model.dif_iva_entregado_prest_serv = parsed.get("dif_iva_entregado_prest_serv")
    model.mon_total_por_uso_plataforma = parsed.get("mon_total_por_uso_plataforma")
    model.xml_text = parsed.get("xml_text", "")


def _normalize_rfc(value: str | None) -> str:
    return (value or "").strip().upper()


def _upsert_platform_rfc(repo: SqlPlatformRfcRepository, parsed: dict) -> None:
    rfc = _normalize_rfc(parsed.get("emisor_rfc"))
    if not rfc:
        return
    existing = repo.get_by_rfc(rfc)
    if existing:
        return
    nombre = (parsed.get("emisor_nombre") or "").strip() or None
    repo.add(rfc=rfc, nombre=nombre)
