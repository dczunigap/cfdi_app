from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db.period_data import compute_period_data, pick_default_period
from app.application.reportes.periodo import build_hoja_sat_text, calc_income_and_iva_sources
from app.utils.money import format_money

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
