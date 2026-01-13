from __future__ import annotations

from app.adapters.inbound.http.api.v1.schemas.facturas import (
    ConceptoResponse,
    FacturaDetailResponse,
    FacturaListResponse,
    PagoResponse,
)
from app.adapters.inbound.http.api.v1.schemas.declaraciones import (
    DeclaracionDetailResponse,
    DeclaracionListResponse,
)
from app.adapters.inbound.http.api.v1.schemas.retenciones import (
    RetencionDetailResponse,
    RetencionListResponse,
)
from app.application.facturas.dto import FacturaDetail
from app.application.declaraciones.dto import DeclaracionDetail
from app.application.retenciones.dto import RetencionDetail


def factura_list_to_dto(items) -> list[FacturaListResponse]:
    return [FacturaListResponse(**item.__dict__) for item in items]


def factura_detail_to_dto(result: FacturaDetail) -> FacturaDetailResponse:
    return FacturaDetailResponse(
        factura=FacturaListResponse(**result.factura.__dict__),
        conceptos=[ConceptoResponse(**c.__dict__) for c in result.conceptos],
        pagos=[PagoResponse(**p.__dict__) for p in result.pagos],
    )


def retencion_list_to_dto(items) -> list[RetencionListResponse]:
    return [RetencionListResponse(**item.__dict__) for item in items]


def retencion_detail_to_dto(result: RetencionDetail) -> RetencionDetailResponse:
    return RetencionDetailResponse(**result.__dict__)


def declaracion_list_to_dto(items) -> list[DeclaracionListResponse]:
    return [DeclaracionListResponse(**item.__dict__) for item in items]


def declaracion_detail_to_dto(result: DeclaracionDetail) -> DeclaracionDetailResponse:
    return DeclaracionDetailResponse(**result.__dict__)


def summary_to_payload(
    *,
    year: int,
    month: int,
    data: dict,
    iva_causado_sugerido: float,
    iva_acreditable_sugerido: float,
    iva_retenido_plat: float,
    iva_neto_sugerido: float,
) -> dict:
    return {
        "year": year,
        "month": month,
        "ingresos_total": data["ingresos_total"],
        "ingresos_base": data["ingresos_base"],
        "ingresos_trasl": data["ingresos_trasl"],
        "ingresos_ret": data["ingresos_ret"],
        "gastos_total": data["gastos_total"],
        "gastos_trasl": data["gastos_trasl"],
        "gastos_ret": data["gastos_ret"],
        "p_count": data["p_count"],
        "cash_in": data["cash_in"],
        "cash_out": data["cash_out"],
        "pagos_count": data["pagos_count"],
        "plat_ing_siva": data["plat_ing_siva"],
        "plat_iva_tras": data["plat_iva_tras"],
        "plat_iva_ret": data["plat_iva_ret"],
        "plat_isr_ret": data["plat_isr_ret"],
        "plat_comision": data["plat_comision"],
        "iva_causado_sugerido": iva_causado_sugerido,
        "iva_acreditable_sugerido": iva_acreditable_sugerido,
        "iva_retenido_plat": iva_retenido_plat,
        "iva_neto_sugerido": iva_neto_sugerido,
    }


def summary_details_to_payload(docs, pagos_rows) -> dict:
    docs_payload = [
        {
            "id": d.id,
            "fecha_emision": d.fecha_emision,
            "tipo_comprobante": d.tipo_comprobante,
            "naturaleza": d.naturaleza,
            "uuid": d.uuid,
            "emisor_rfc": d.emisor_rfc,
            "receptor_rfc": d.receptor_rfc,
            "uso_cfdi": d.uso_cfdi,
            "total": d.total,
            "moneda": d.moneda,
        }
        for d in docs
    ]

    pagos_payload = [
        {
            "factura_id": pago.factura_id,
            "fecha_pago": pago.fecha_pago,
            "monto": pago.monto,
            "moneda_p": pago.moneda_p,
            "forma_pago_p": pago.forma_pago_p,
            "naturaleza": naturaleza,
        }
        for pago, naturaleza in pagos_rows
    ]

    return {
        "docs": docs_payload,
        "pagos": pagos_payload,
    }


def import_xml_stats() -> dict:
    return {
        "cfdi_insertados": 0,
        "cfdi_duplicados": 0,
        "retenciones_insertadas": 0,
        "retenciones_duplicadas": 0,
        "errores": 0,
    }


def import_pdf_stats() -> dict:
    return {"insertados": 0, "duplicados": 0, "errores": 0}


def declaracion_pdf_to_payload(model) -> dict | None:
    if not model:
        return None
    return {
        "id": model.id,
        "rfc": model.rfc,
        "folio": model.folio,
        "fecha_presentacion": model.fecha_presentacion,
        "filename": model.filename,
        "original_name": model.original_name,
        "text_excerpt": model.text_excerpt,
    }


def declaracion_mode_to_payload(
    *,
    year: int,
    month: int,
    income_source: str | None,
    effective_income_source: str,
    mi_rfc: str | None,
    ingresos_total_sin_iva: float,
    plat_ing_siva: float,
    ingresos_base: float,
    isr_retenido: float,
    iva_retenido: float,
    iva_trasladado_total: float,
    iva_trasladado_seleccion: float,
    checks: list[dict],
    acuse_payload: dict | None,
    acuse_checks: list[dict],
    declaracion_pdf: dict | None,
    retenciones_count: int,
    docs_count: int,
    pagos_count: int,
) -> dict:
    return {
        "year": year,
        "month": month,
        "income_source": income_source,
        "effective_income_source": effective_income_source,
        "mi_rfc": mi_rfc,
        "ingresos_total_sin_iva": ingresos_total_sin_iva,
        "plat_ing_siva": plat_ing_siva,
        "ingresos_base": ingresos_base,
        "isr_retenido": isr_retenido,
        "iva_retenido": iva_retenido,
        "iva_trasladado_total": iva_trasladado_total,
        "iva_trasladado_seleccion": iva_trasladado_seleccion,
        "checks": checks,
        "acuse_payload": acuse_payload,
        "acuse_checks": acuse_checks,
        "declaracion_pdf": declaracion_pdf,
        "retenciones_count": retenciones_count,
        "docs_count": docs_count,
        "pagos_count": pagos_count,
    }
