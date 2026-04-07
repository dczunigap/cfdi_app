from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.mappers import summary_details_to_payload, summary_to_payload
from app.adapters.inbound.http.deps import get_db, get_required_rfc
from app.adapters.outbound.db.period_data import compute_period_data
from app.application.reportes.service import (
    TIPO_DECL_ANUAL,
    TIPO_DECL_MENSUAL,
    compute_year_data,
    fetch_saldos_acumulados_ejercicio,
    get_latest_declaracion_pdf,
    load_config_for_rfc,
    normalize_tipo_declaracion,
    resolve_mi_rfc,
    resolve_period_or_404,
)

router = APIRouter()


@router.get(
    "/summary",
    summary="Resumen mensual",
    description="Devuelve totales agregados del periodo.",
)
def summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    tipo_declaracion: Optional[str] = "MENSUAL",
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
):
    tipo_decl = normalize_tipo_declaracion(tipo_declaracion)
    year, month = resolve_period_or_404(
        db,
        tipo_decl=tipo_decl,
        year=year,
        month=month,
    )

    _, usos_mensual, regimen = load_config_for_rfc(
        db,
        rfc=x_rfc,
        tipo_declaracion_clave=TIPO_DECL_MENSUAL,
        ejercicio=year,
    )

    if tipo_decl == TIPO_DECL_ANUAL:
        config_anual, usos_anual, _ = load_config_for_rfc(
            db,
            rfc=x_rfc,
            tipo_declaracion_clave=TIPO_DECL_ANUAL,
            ejercicio=year,
        )
        data_anual, periodos_incluidos = compute_year_data(
            db,
            year=year,
            mi_rfc=x_rfc,
            gasto_uso_cfdi_allowlist=usos_anual,
        )
        incluir_acumulado = bool(config_anual.get("incluir_acumulado_mensual_en_anual"))
        data_mensual_acumulado = None
        if incluir_acumulado:
            data_mensual_acumulado, _ = compute_year_data(
                db,
                year=year,
                mi_rfc=x_rfc,
                gasto_uso_cfdi_allowlist=usos_mensual,
            )

        iva_causado_sugerido = data_anual["plat_iva_tras"] + data_anual["ingresos_trasl"]
        iva_acreditable_anual_sugerido = data_anual["gastos_trasl"]
        iva_acreditable_mensual_acumulado_sugerido = (
            data_mensual_acumulado["gastos_trasl"] if data_mensual_acumulado else 0.0
        )
        iva_retenido_plat = data_anual["plat_iva_ret"]
        iva_neto_sugerido = (
            iva_causado_sugerido
            - (iva_acreditable_anual_sugerido + iva_acreditable_mensual_acumulado_sugerido)
            - iva_retenido_plat
        )
        return {
            "tipo_declaracion": TIPO_DECL_ANUAL,
            "year": year,
            "mi_rfc": x_rfc,
            "regimen_fiscal_clave": regimen.clave,
            "periodos_mensuales_incluidos": periodos_incluidos,
            "deducciones_anuales": {
                "usos_cfdi": sorted(usos_anual),
                "gastos_total": data_anual["gastos_total"],
                "gastos_trasl": data_anual["gastos_trasl"],
                "gastos_ret": data_anual["gastos_ret"],
            },
            "deducciones_mensuales_acumuladas": {
                "habilitado": incluir_acumulado,
                "usos_cfdi": sorted(usos_mensual) if incluir_acumulado else [],
                "gastos_total": float(data_mensual_acumulado["gastos_total"]) if data_mensual_acumulado else 0.0,
                "gastos_trasl": float(data_mensual_acumulado["gastos_trasl"]) if data_mensual_acumulado else 0.0,
                "gastos_ret": float(data_mensual_acumulado["gastos_ret"]) if data_mensual_acumulado else 0.0,
            },
            "ingresos_total": data_anual["ingresos_total"],
            "ingresos_base": data_anual["ingresos_base"],
            "ingresos_trasl": data_anual["ingresos_trasl"],
            "ingresos_ret": data_anual["ingresos_ret"],
            "plat_ing_siva": data_anual["plat_ing_siva"],
            "plat_iva_tras": data_anual["plat_iva_tras"],
            "plat_iva_ret": data_anual["plat_iva_ret"],
            "plat_isr_ret": data_anual["plat_isr_ret"],
            "plat_comision": data_anual["plat_comision"],
            "iva_causado_sugerido": iva_causado_sugerido,
            "iva_acreditable_sugerido": iva_acreditable_anual_sugerido
            + iva_acreditable_mensual_acumulado_sugerido,
            "iva_retenido_plat": iva_retenido_plat,
            "iva_neto_sugerido": iva_neto_sugerido,
        }

    data = compute_period_data(db, year, month, mi_rfc=x_rfc, gasto_uso_cfdi_allowlist=usos_mensual)
    iva_causado_sugerido = data["plat_iva_tras"] + data["ingresos_trasl"]
    iva_acreditable_sugerido = data["gastos_trasl"]
    iva_retenido_plat = data["plat_iva_ret"]
    iva_neto_sugerido = iva_causado_sugerido - iva_acreditable_sugerido - iva_retenido_plat
    declaracion_pdf = get_latest_declaracion_pdf(db, year, month)
    mi_rfc = resolve_mi_rfc(x_rfc, declaracion_pdf, data)

    saldo_a_favor_anterior, saldo_a_pagar_anterior = fetch_saldos_acumulados_ejercicio(
        db,
        year=year,
        month=month,
        rfc=mi_rfc,
    )

    return summary_to_payload(
        year=year,
        month=month,
        data=data,
        mi_rfc=mi_rfc,
        iva_causado_sugerido=iva_causado_sugerido,
        iva_acreditable_sugerido=iva_acreditable_sugerido,
        iva_retenido_plat=iva_retenido_plat,
        iva_neto_sugerido=iva_neto_sugerido,
        saldo_a_favor_anterior=saldo_a_favor_anterior,
        saldo_a_pagar_anterior=saldo_a_pagar_anterior,
    )


@router.get(
    "/summary/details",
    summary="Resumen mensual (detalle)",
    description="Devuelve listas acotadas de CFDI y pagos del periodo.",
)
def summary_details(
    year: Optional[int] = None,
    month: Optional[int] = None,
    tipo_declaracion: Optional[str] = "MENSUAL",
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
):
    tipo_decl = normalize_tipo_declaracion(tipo_declaracion)
    year, month = resolve_period_or_404(
        db,
        tipo_decl=tipo_decl,
        year=year,
        month=month,
    )

    if tipo_decl == TIPO_DECL_ANUAL:
        _, usos, regimen = load_config_for_rfc(
            db,
            rfc=x_rfc,
            tipo_declaracion_clave=TIPO_DECL_ANUAL,
            ejercicio=year,
        )
        data, periodos = compute_year_data(
            db,
            year=year,
            mi_rfc=x_rfc,
            gasto_uso_cfdi_allowlist=usos,
        )
        payload = summary_details_to_payload(data["docs"][:200], data["pagos_rows"][:200])
        payload["tipo_declaracion"] = TIPO_DECL_ANUAL
        payload["year"] = year
        payload["periodos_mensuales_incluidos"] = periodos
        payload["regimen_fiscal_clave"] = regimen.clave
        payload["usos_cfdi"] = sorted(usos)
        return payload

    _, usos, regimen = load_config_for_rfc(
        db,
        rfc=x_rfc,
        tipo_declaracion_clave=TIPO_DECL_MENSUAL,
        ejercicio=year,
    )
    data = compute_period_data(db, year, month, mi_rfc=x_rfc, gasto_uso_cfdi_allowlist=usos)
    payload = summary_details_to_payload(data["docs"][:200], data["pagos_rows"][:200])
    payload["tipo_declaracion"] = TIPO_DECL_MENSUAL
    payload["year"] = year
    payload["month"] = month
    payload["regimen_fiscal_clave"] = regimen.clave
    payload["usos_cfdi"] = sorted(usos)
    return payload
