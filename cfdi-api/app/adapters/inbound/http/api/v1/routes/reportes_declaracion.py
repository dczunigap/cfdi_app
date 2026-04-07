from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.mappers import declaracion_mode_to_payload, declaracion_pdf_to_payload
from app.adapters.inbound.http.deps import get_db, get_required_rfc
from app.adapters.outbound.db.period_data import compute_period_data
from app.application.reportes.periodo import build_checklist, calc_income_and_iva_sources
from app.application.reportes.service import (
    TIPO_DECL_ANUAL,
    TIPO_DECL_MENSUAL,
    build_acuse_payload_and_checks,
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
    "/declaracion",
    summary="Modo declaracion mensual",
    description="Devuelve datos de apoyo para capturar declaracion mensual.",
)
def declaracion_mode(
    year: Optional[int] = None,
    month: Optional[int] = None,
    tipo_declaracion: Optional[str] = "MENSUAL",
    income_source: Optional[str] = "auto",
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
        config_anual, usos_anual, regimen = load_config_for_rfc(
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
        usos_mensual: set[str] = set()
        if incluir_acumulado:
            _, usos_mensual, _ = load_config_for_rfc(
                db,
                rfc=x_rfc,
                tipo_declaracion_clave=TIPO_DECL_MENSUAL,
                ejercicio=year,
            )
            data_mensual_acumulado, _ = compute_year_data(
                db,
                year=year,
                mi_rfc=x_rfc,
                gasto_uso_cfdi_allowlist=usos_mensual,
            )
        ingresos_total_sin_iva, iva_trasladado_sel, effective_income_source = calc_income_and_iva_sources(
            data_anual, income_source
        )
        iva_trasladado_total = float(data_anual.get("plat_iva_tras") or 0.0) + float(
            data_anual.get("ingresos_trasl") or 0.0
        )
        return {
            "tipo_declaracion": TIPO_DECL_ANUAL,
            "year": year,
            "periodos_mensuales_incluidos": periodos_incluidos,
            "mi_rfc": x_rfc,
            "regimen_fiscal_clave": regimen.clave,
            "income_source": income_source,
            "effective_income_source": effective_income_source,
            "ingresos_total_sin_iva": ingresos_total_sin_iva,
            "ingresos_base": float(
                (data_anual.get("ingresos_base") or 0.0) + (data_mensual_acumulado.get("ingresos_base") or 0.0)
                if data_mensual_acumulado
                else (data_anual.get("ingresos_base") or 0.0)
            ),
            "isr_retenido": float(data_anual.get("plat_isr_ret") or 0.0),
            "iva_retenido": float(data_anual.get("plat_iva_ret") or 0.0),
            "iva_acreditable": float(
                (data_anual.get("gastos_trasl") or 0.0) + (data_mensual_acumulado.get("gastos_trasl") or 0.0)
            ),
            "iva_trasladado_total": iva_trasladado_total,
            "iva_trasladado_seleccion": iva_trasladado_sel,
            "retenciones_count": len(data_anual.get("ret_rows") or []),
            "docs_count": len(data_anual.get("docs") or []),
            "pagos_count": int(data_anual.get("pagos_count") or 0),
            "deducciones_anuales": {
                "usos_cfdi": sorted(usos_anual),
                "gastos_total": float(data_anual.get("gastos_total") or 0.0),
                "gastos_trasl": float(data_anual.get("gastos_trasl") or 0.0),
                "gastos_ret": float(data_anual.get("gastos_ret") or 0.0),
            },
            "deducciones_mensuales_acumuladas": {
                "habilitado": incluir_acumulado,
                "usos_cfdi": sorted(usos_mensual) if incluir_acumulado else [],
                "gastos_total": float(data_mensual_acumulado.get("gastos_total") or 0.0)
                if data_mensual_acumulado
                else 0.0,
                "gastos_trasl": float(data_mensual_acumulado.get("gastos_trasl") or 0.0)
                if data_mensual_acumulado
                else 0.0,
                "gastos_ret": float(data_mensual_acumulado.get("gastos_ret") or 0.0)
                if data_mensual_acumulado
                else 0.0,
            },
            "checks": [],
            "acuse_payload": None,
            "acuse_checks": [],
            "declaracion_pdf": None,
            "mostrar_declaracion_presentada": False,
            "mostrar_conciliacion_acuse_sat": False,
        }

    _, usos_mensual, _ = load_config_for_rfc(
        db,
        rfc=x_rfc,
        tipo_declaracion_clave=TIPO_DECL_MENSUAL,
        ejercicio=year,
    )

    data = compute_period_data(db, year, month, mi_rfc=x_rfc, gasto_uso_cfdi_allowlist=usos_mensual)
    ingresos_total_sin_iva, iva_trasladado_sel, effective_income_source = calc_income_and_iva_sources(
        data, income_source
    )

    declaracion_pdf = get_latest_declaracion_pdf(db, year, month)
    mi_rfc = resolve_mi_rfc(x_rfc, declaracion_pdf, data)

    checks = build_checklist(
        data=data,
        mi_rfc=mi_rfc or "",
        income_source=income_source or "auto",
        effective_income_source=effective_income_source,
    )

    iva_trasladado_total = float(data.get("plat_iva_tras") or 0.0) + float(data.get("ingresos_trasl") or 0.0)

    acuse_payload, acuse_checks = build_acuse_payload_and_checks(
        declaracion_pdf=declaracion_pdf,
        year=year,
        month=month,
        mi_rfc=mi_rfc,
        data=data,
        ingresos_total_sin_iva=ingresos_total_sin_iva,
        iva_trasladado_total=iva_trasladado_total,
    )

    saldo_a_favor_anterior, saldo_a_pagar_anterior = fetch_saldos_acumulados_ejercicio(
        db,
        year=year,
        month=month,
        rfc=mi_rfc,
    )

    return declaracion_mode_to_payload(
        year=year,
        month=month,
        income_source=income_source,
        effective_income_source=effective_income_source,
        mi_rfc=mi_rfc,
        ingresos_total_sin_iva=ingresos_total_sin_iva,
        plat_ing_siva=float(data.get("plat_ing_siva") or 0.0),
        ingresos_base=float(data.get("ingresos_base") or 0.0),
        isr_retenido=float(data.get("plat_isr_ret") or 0.0),
        iva_retenido=float(data.get("plat_iva_ret") or 0.0),
        iva_acreditable=float(data.get("gastos_trasl") or 0.0),
        iva_trasladado_total=iva_trasladado_total,
        iva_trasladado_seleccion=iva_trasladado_sel,
        saldo_a_favor_anterior=saldo_a_favor_anterior,
        saldo_a_pagar_anterior=saldo_a_pagar_anterior,
        checks=checks,
        acuse_payload=acuse_payload,
        acuse_checks=acuse_checks,
        declaracion_pdf=declaracion_pdf_to_payload(declaracion_pdf),
        retenciones_count=len(data.get("ret_rows") or []),
        docs_count=len(data.get("docs") or []),
        pagos_count=int(data.get("pagos_count") or 0),
    )
