from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from starlette.responses import Response

from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db.period_data import compute_period_data, pick_default_period
from app.application.reportes.periodo import (
    build_checklist,
    build_hoja_sat_text,
    calc_income_and_iva_sources,
)
from app.utils.money import format_money
from app.adapters.outbound.db.models import DeclaracionModel
from app.adapters.services.parsers.pdf_parser import LocalPdfParser
from app.application.declaraciones.payload import build_declaracion_payload
from app.domain.declaraciones.entities import DeclaracionPDF

router = APIRouter(tags=["reportes"])


@router.get(
    "/summary",
    summary="Resumen mensual",
    description="Devuelve totales agregados del periodo.",
)
def summary(year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(get_db)):
    if year is None or month is None:
        year, month = pick_default_period(db)
    if year is None or month is None:
        raise HTTPException(status_code=404, detail="No hay datos para resumir")

    data = compute_period_data(db, year, month)
    iva_causado_sugerido = data["plat_iva_tras"] + data["ingresos_trasl"]
    iva_acreditable_sugerido = data["gastos_trasl"]
    iva_retenido_plat = data["plat_iva_ret"]
    iva_neto_sugerido = iva_causado_sugerido - iva_acreditable_sugerido - iva_retenido_plat

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


@router.get(
    "/summary/details",
    summary="Resumen mensual (detalle)",
    description="Devuelve listas acotadas de CFDI y pagos del periodo.",
)
def summary_details(year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(get_db)):
    if year is None or month is None:
        year, month = pick_default_period(db)
    if year is None or month is None:
        raise HTTPException(status_code=404, detail="No hay datos para resumir")

    data = compute_period_data(db, year, month)
    docs = data["docs"][:200]
    pagos_rows = data["pagos_rows"][:200]

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


@router.get(
    "/declaracion",
    summary="Modo declaracion mensual",
    description="Devuelve datos de apoyo para capturar declaracion mensual.",
)
def declaracion_mode(
    year: Optional[int] = None,
    month: Optional[int] = None,
    income_source: Optional[str] = "auto",
    db: Session = Depends(get_db),
):
    if year is None or month is None:
        year, month = pick_default_period(db)
    if year is None or month is None:
        raise HTTPException(status_code=404, detail="No hay datos para resumir")

    data = compute_period_data(db, year, month)
    ingresos_total_sin_iva, iva_trasladado_sel, effective_income_source = calc_income_and_iva_sources(
        data, income_source
    )

    declaracion_pdf = db.execute(
        select(DeclaracionModel)
        .where(DeclaracionModel.year == year, DeclaracionModel.month == month)
        .order_by(desc(DeclaracionModel.fecha_presentacion).nullslast(), desc(DeclaracionModel.id))
        .limit(1)
    ).scalar_one_or_none()

    mi_rfc = declaracion_pdf.rfc if declaracion_pdf and declaracion_pdf.rfc else None
    if not mi_rfc:
        ret_rows = data.get("ret_rows") or []
        mi_rfc = (ret_rows[0].receptor_rfc if ret_rows else None) or None

    checks = build_checklist(
        data=data,
        mi_rfc=mi_rfc or "",
        income_source=income_source or "auto",
        effective_income_source=effective_income_source,
    )

    iva_trasladado_total = float(data.get("plat_iva_tras") or 0.0) + float(
        data.get("ingresos_trasl") or 0.0
    )

    acuse_payload = None
    acuse_checks: list[dict] = []
    if declaracion_pdf and (declaracion_pdf.text_excerpt or "").strip():
        dec_entity = DeclaracionPDF(
            year=declaracion_pdf.year,
            month=declaracion_pdf.month,
            rfc=declaracion_pdf.rfc,
            folio=declaracion_pdf.folio,
            fecha_presentacion=declaracion_pdf.fecha_presentacion,
            sha256=declaracion_pdf.sha256,
            filename=declaracion_pdf.filename,
            original_name=declaracion_pdf.original_name,
            num_pages=declaracion_pdf.num_pages,
            text_excerpt=declaracion_pdf.text_excerpt,
            created_at=declaracion_pdf.created_at,
        )
        parser = LocalPdfParser()
        acuse_payload = build_declaracion_payload(dec_entity, parser.parse_sat_summary)

        def to_float(value: object) -> float | None:
            try:
                return float(value) if value is not None else None
            except Exception:
                return None

        def build_amount_check(label: str, sat_val: object, app_val: object, note: str | None = None):
            sat = to_float(sat_val)
            app = to_float(app_val)
            if sat is None:
                return {
                    "status": "warn",
                    "label": label,
                    "sat": None,
                    "app": app,
                    "diff": None,
                    "note": note or "SAT sin dato en PDF.",
                }
            if app is None:
                return {
                    "status": "warn",
                    "label": label,
                    "sat": sat,
                    "app": None,
                    "diff": None,
                    "note": note or "App sin dato.",
                }
            diff = sat - app
            status = "ok" if abs(diff) <= 1.0 else "warn"
            return {
                "status": status,
                "label": label,
                "sat": sat,
                "app": app,
                "diff": diff,
                "note": note,
            }

        def build_text_check(label: str, sat_val: object, app_val: object, note: str | None = None):
            sat = (str(sat_val).strip() if sat_val is not None else "") or None
            app = (str(app_val).strip() if app_val is not None else "") or None
            if not sat:
                return {
                    "status": "warn",
                    "label": label,
                    "sat": None,
                    "app": app,
                    "diff": None,
                    "note": note or "SAT sin dato en PDF.",
                }
            status = "ok" if sat == app else "warn"
            return {
                "status": status,
                "label": label,
                "sat": sat,
                "app": app,
                "diff": None,
                "note": note,
            }

        periodo_app = f"{year}-{month:02d}"
        acuse_checks = [
            build_text_check("Periodo", acuse_payload.get("periodo"), periodo_app, "Revisa el periodo del PDF."),
            build_text_check("RFC", acuse_payload.get("rfc"), mi_rfc, "Revisa el RFC del contribuyente."),
            build_amount_check(
                "Ingresos sin IVA (SAT vs App)",
                acuse_payload.get("ingresos_totales_mes"),
                ingresos_total_sin_iva,
                "Revisa la fuente de ingresos seleccionada.",
            ),
            build_amount_check(
                "ISR retenido (SAT vs App)",
                acuse_payload.get("retenciones_plataformas"),
                data.get("plat_isr_ret"),
                "Revisa el XML de retenciones.",
            ),
            build_amount_check(
                "IVA trasladado (SAT vs App)",
                acuse_payload.get("iva_a_cargo_16"),
                iva_trasladado_total,
                "Revisa CFDI de ingresos y plataforma.",
            ),
            build_amount_check(
                "IVA acreditable (SAT vs App)",
                acuse_payload.get("iva_acreditable"),
                data.get("gastos_trasl"),
                "Revisa CFDI de gastos.",
            ),
            build_amount_check(
                "IVA retenido (SAT vs App)",
                acuse_payload.get("iva_retenido"),
                data.get("plat_iva_ret"),
                "Revisa retenciones de plataforma.",
            ),
        ]

    return {
        "year": year,
        "month": month,
        "income_source": income_source,
        "effective_income_source": effective_income_source,
        "mi_rfc": mi_rfc,
        "ingresos_total_sin_iva": ingresos_total_sin_iva,
        "plat_ing_siva": float(data.get("plat_ing_siva") or 0.0),
        "ingresos_base": float(data.get("ingresos_base") or 0.0),
        "isr_retenido": float(data.get("plat_isr_ret") or 0.0),
        "iva_retenido": float(data.get("plat_iva_ret") or 0.0),
        "iva_trasladado_total": iva_trasladado_total,
        "iva_trasladado_seleccion": iva_trasladado_sel,
        "checks": checks,
        "acuse_payload": acuse_payload,
        "acuse_checks": acuse_checks,
        "declaracion_pdf": (
            {
                "id": declaracion_pdf.id,
                "rfc": declaracion_pdf.rfc,
                "folio": declaracion_pdf.folio,
                "fecha_presentacion": declaracion_pdf.fecha_presentacion,
                "filename": declaracion_pdf.filename,
                "original_name": declaracion_pdf.original_name,
                "text_excerpt": declaracion_pdf.text_excerpt,
            }
            if declaracion_pdf
            else None
        ),
        "retenciones_count": len(data.get("ret_rows") or []),
        "docs_count": len(data.get("docs") or []),
        "pagos_count": int(data.get("pagos_count") or 0),
    }


@router.get(
    "/sat_hoja.txt",
    summary="Hoja SAT",
    description="Devuelve texto plano con hoja SAT del periodo.",
)
def sat_hoja_txt(
    year: Optional[int] = None,
    month: Optional[int] = None,
    income_source: str = "auto",
    db: Session = Depends(get_db),
) -> Response:
    if year is None or month is None:
        raise HTTPException(status_code=400, detail="year y month son requeridos")

    data = compute_period_data(db, year, month)
    hoja_text, effective = build_hoja_sat_text(year, month, income_source, data, format_money)
    return Response(
        content=hoja_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=hoja_sat_{year}_{month:02d}_{effective}.txt"},
    )


@router.get(
    "/sat_report.csv",
    summary="Reporte SAT CSV",
    description="Devuelve CSV de papel de trabajo mensual.",
)
def sat_report_csv(
    year: Optional[int] = None,
    month: Optional[int] = None,
    income_source: str = "auto",
    db: Session = Depends(get_db),
) -> Response:
    if year is None or month is None:
        raise HTTPException(status_code=400, detail="year y month son requeridos")

    data = compute_period_data(db, year, month)
    ingresos_total_sin_iva, iva_tras_total, _effective_income_source = calc_income_and_iva_sources(
        data, income_source
    )

    iva_causado = iva_tras_total
    iva_acreditable = data["gastos_trasl"]
    iva_neto = iva_causado - iva_acreditable - data["plat_iva_ret"]

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        [
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
        ]
    )
    w.writerow(
        [
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
        ]
    )

    return Response(
        content=out.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=sat_report_{year}_{month:02d}.csv"},
    )
