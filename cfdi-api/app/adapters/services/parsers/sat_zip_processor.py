from __future__ import annotations

import io
import logging
import zipfile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import ConceptoModel, FacturaModel, PagoModel, RetencionModel
from app.adapters.outbound.db.repositories.facturas import SqlFacturaRepository
from app.adapters.outbound.db.repositories.platform_rfcs import SqlPlatformRfcRepository
from app.adapters.outbound.db.repositories.retenciones import SqlRetencionRepository
from app.adapters.services.parsers.xml_parser import LocalXmlParser
from app.application.imports.facturas import (
    create_factura_from_parsed,
    create_retencion_from_parsed,
)
from app.ports.sat_zip_processor import SatZipProcessor

logger = logging.getLogger(__name__)


class LocalSatZipProcessor(SatZipProcessor):
    def process_zip(self, db: Session, zip_bytes: bytes) -> None:
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
