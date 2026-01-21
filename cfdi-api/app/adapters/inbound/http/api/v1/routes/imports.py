from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db.repositories.declaraciones import SqlDeclaracionRepository
from app.adapters.outbound.db.repositories.facturas import SqlFacturaRepository
from app.adapters.outbound.db.repositories.platform_rfcs import SqlPlatformRfcRepository
from app.adapters.outbound.db.repositories.retenciones import SqlRetencionRepository
from app.adapters.outbound.db.models import (
    ConceptoModel,
    DeclaracionModel,
    FacturaModel,
    PagoModel,
    RetencionModel,
)
from app.adapters.outbound.files.pdf_storage import LocalPdfStorage
from app.adapters.services.parsers.pdf_parser import LocalPdfParser
from app.adapters.services.parsers.xml_parser import LocalXmlParser
from app.application.imports.facturas import (
    create_factura_from_parsed,
    create_retencion_from_parsed,
)
from app.adapters.inbound.http.api.v1.mappers import (
    import_pdf_stats,
    import_xml_stats,
)
from app.domain.declaraciones.entities import DeclaracionPDF
from app.utils.files import safe_pdf_filename, sha256_bytes

router = APIRouter(tags=["import"])


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
logger = logging.getLogger(__name__)


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


@router.post("/importar")
async def importar_xml(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    stats = import_xml_stats()

    factura_repo = SqlFacturaRepository(db)
    ret_repo = SqlRetencionRepository(db)
    platform_repo = SqlPlatformRfcRepository(db)
    parser = LocalXmlParser()

    for file in files:
        try:
            xml_bytes = await file.read()
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
                        stats["cfdi_actualizados"] += 1
                    else:
                        stats["cfdi_duplicados"] += 1
                    continue
                factura = create_factura_from_parsed(parsed)
                factura_repo.add_factura(factura)
                stats["cfdi_insertados"] += 1
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
                        stats["retenciones_actualizadas"] += 1
                    else:
                        stats["retenciones_duplicadas"] += 1
                    _upsert_platform_rfc(platform_repo, parsed)
                    continue
                retencion = create_retencion_from_parsed(parsed)
                ret_repo.add_retencion(retencion)
                _upsert_platform_rfc(platform_repo, parsed)
                stats["retenciones_insertadas"] += 1
            else:
                stats["errores"] += 1
        except Exception:
            db.rollback()
            logger.exception(
                "Error al importar XML (filename=%s)",
                getattr(file, "filename", None),
            )
            stats["errores"] += 1

    return stats


@router.post("/importar_pdf")
async def importar_pdf(
    files: list[UploadFile] = File(...),
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
):
    stats = import_pdf_stats()

    base_dir = Path(__file__).resolve().parents[7]
    storage = LocalPdfStorage(base_dir / "database" / "pdfs")
    parser = LocalPdfParser()
    repo = SqlDeclaracionRepository(db)

    for file in files:
        try:
            pdf_bytes = await file.read()
            sha = sha256_bytes(pdf_bytes)

            existing = db.execute(
                select(DeclaracionModel).where(DeclaracionModel.sha256 == sha)
            ).scalar_one_or_none()

            filename = safe_pdf_filename(sha, getattr(file, "filename", None))
            storage.save(filename, pdf_bytes)

            try:
                text, num_pages = parser.extract_text(
                    str(base_dir / "database" / "pdfs" / filename)
                )
            except Exception:
                text, num_pages = "", None

            try:
                summary = parser.parse_sat_summary(text or "")
            except Exception:
                summary = {}

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

            dec = DeclaracionPDF(
                year=int(y),
                month=int(mth),
                rfc=summary.get("rfc") if isinstance(summary, dict) else None,
                folio=summary.get("numero_operacion") if isinstance(summary, dict) else None,
                fecha_presentacion=summary.get("fecha_presentacion")
                if isinstance(summary, dict)
                else None,
                sha256=sha,
                filename=filename,
                original_name=getattr(file, "filename", None),
                num_pages=int(num_pages) if num_pages is not None else None,
                text_excerpt=text[:20000] if text else None,
            )
            if existing is not None:
                existing.year = dec.year
                existing.month = dec.month
                existing.rfc = dec.rfc
                existing.folio = dec.folio
                existing.fecha_presentacion = dec.fecha_presentacion
                existing.filename = dec.filename
                existing.original_name = dec.original_name
                existing.num_pages = dec.num_pages
                existing.text_excerpt = dec.text_excerpt
                db.commit()
                stats["actualizados"] += 1
            else:
                repo.add_declaracion(dec)
                stats["insertados"] += 1
        except Exception:
            db.rollback()
            stats["errores"] += 1

    return stats
