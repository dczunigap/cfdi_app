from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from starlette.responses import Response

from app.adapters.inbound.http.deps import get_db, get_required_rfc, require_user
from app.adapters.outbound.db.period_data import compute_period_data, month_options, pick_default_period
from app.application.reportes.periodo import (
    build_checklist,
    build_hoja_sat_text,
    calc_income_and_iva_sources,
)
from app.utils.money import format_money
from app.adapters.outbound.db.models import (
    DeclaracionModel,
    RegimenFiscalCatalogModel,
    RfcModel,
)
from app.adapters.outbound.db.repositories.declaracion_config import SqlDeclaracionConfigRepository
from app.adapters.services.parsers.pdf_parser import LocalPdfParser
from app.application.declaraciones.payload import build_declaracion_payload
from app.adapters.inbound.http.api.v1.routes.utils import (
    csv_response,
    declaracion_model_to_entity,
    text_response,
)
from app.adapters.inbound.http.api.v1.mappers import (
    declaracion_mode_to_payload,
    declaracion_pdf_to_payload,
    summary_details_to_payload,
    summary_to_payload,
)

router = APIRouter(tags=["reportes"], dependencies=[Depends(require_user)])
TIPO_DECL_MENSUAL = "MENSUAL"
TIPO_DECL_ANUAL = "ANUAL"


def _normalize_tipo_declaracion(value: str | None) -> str:
    normalized = (value or TIPO_DECL_MENSUAL).strip().upper()
    if normalized not in {TIPO_DECL_MENSUAL, TIPO_DECL_ANUAL}:
        raise HTTPException(status_code=400, detail="tipo_declaracion invalido. Use MENSUAL o ANUAL")
    return normalized


def _resolve_regimen_for_rfc(db: Session, rfc: str) -> RegimenFiscalCatalogModel:
    row = db.execute(
        select(RegimenFiscalCatalogModel)
        .select_from(RfcModel)
        .join(RegimenFiscalCatalogModel, RfcModel.regimen_fiscal_id == RegimenFiscalCatalogModel.id)
        .where(RfcModel.rfc == rfc)
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=400, detail="RFC no registrado o sin regimen fiscal")
    return row


def _load_config_for_rfc(
    db: Session,
    *,
    rfc: str,
    tipo_declaracion_clave: str,
    ejercicio: int | None = None,
) -> tuple[dict, set[str], RegimenFiscalCatalogModel]:
    regimen = _resolve_regimen_for_rfc(db, rfc)
    repo = SqlDeclaracionConfigRepository(db)
    config = repo.get_config(
        regimen_fiscal_clave=regimen.clave,
        tipo_declaracion_clave=tipo_declaracion_clave,
    )
    if not config or not bool(config.get("activo")):
        raise HTTPException(
            status_code=400,
            detail=(
                "No existe configuracion activa para "
                f"regimen {regimen.clave}, tipo {tipo_declaracion_clave} "
                f"(ejercicio solicitado: {ejercicio if ejercicio is not None else 'N/A'})"
            ),
        )
    usos = {
        str(item.get("clave") or "").strip().upper()
        for item in (config.get("usos_cfdi") or [])
        if str(item.get("clave") or "").strip()
    }
    if not usos:
        raise HTTPException(
            status_code=400,
            detail=(
                "La configuracion no tiene usos CFDI activos para "
                f"regimen {regimen.clave}, tipo {tipo_declaracion_clave}"
            ),
        )
    return config, usos, regimen


def _compute_year_data(
    db: Session,
    *,
    year: int,
    mi_rfc: str,
    gasto_uso_cfdi_allowlist: set[str] | None = None,
) -> tuple[dict, list[str]]:
    totals = {
        "ingresos_total": 0.0,
        "ingresos_base": 0.0,
        "ingresos_trasl": 0.0,
        "ingresos_ret": 0.0,
        "gastos_total": 0.0,
        "gastos_trasl": 0.0,
        "gastos_ret": 0.0,
        "p_count": 0,
        "cash_in": 0.0,
        "cash_out": 0.0,
        "pagos_count": 0,
        "plat_ing_siva": 0.0,
        "plat_iva_tras": 0.0,
        "plat_iva_ret": 0.0,
        "plat_isr_ret": 0.0,
        "plat_comision": 0.0,
        "docs": [],
        "pagos_rows": [],
        "ret_rows": [],
    }
    periods = [m for y, m in month_options(db) if y == year]
    for month in periods:
        data = compute_period_data(
            db,
            year,
            month,
            mi_rfc=mi_rfc,
            gasto_uso_cfdi_allowlist=gasto_uso_cfdi_allowlist,
        )
        for key in (
            "ingresos_total",
            "ingresos_base",
            "ingresos_trasl",
            "ingresos_ret",
            "gastos_total",
            "gastos_trasl",
            "gastos_ret",
            "cash_in",
            "cash_out",
            "plat_ing_siva",
            "plat_iva_tras",
            "plat_iva_ret",
            "plat_isr_ret",
            "plat_comision",
        ):
            totals[key] += float(data.get(key) or 0.0)
        totals["p_count"] += int(data.get("p_count") or 0)
        totals["pagos_count"] += int(data.get("pagos_count") or 0)
        totals["docs"].extend(data.get("docs") or [])
        totals["pagos_rows"].extend(data.get("pagos_rows") or [])
        totals["ret_rows"].extend(data.get("ret_rows") or [])
    return totals, [f"{year}-{m:02d}" for m in sorted(periods)]


def _resolve_period_or_404(
    db: Session,
    *,
    tipo_decl: str,
    year: int | None,
    month: int | None,
) -> tuple[int, int | None]:
    resolved_year = year
    resolved_month = month
    if resolved_year is None:
        resolved_year, default_month = pick_default_period(db)
        if tipo_decl == TIPO_DECL_MENSUAL and resolved_month is None:
            resolved_month = default_month
    elif tipo_decl == TIPO_DECL_MENSUAL and resolved_month is None:
        _, default_month = pick_default_period(db)
        resolved_month = default_month
    if resolved_year is None:
        raise HTTPException(status_code=404, detail="No hay datos para resumir")
    if tipo_decl == TIPO_DECL_MENSUAL and resolved_month is None:
        raise HTTPException(status_code=404, detail="No hay datos para resumir")
    return resolved_year, resolved_month


def _previous_period(year: int, month: int) -> tuple[int, int]:
    if month <= 1:
        return year - 1, 12
    return year, month - 1


def _fetch_saldos(
    db: Session, year: int, month: int, rfc: str | None
) -> tuple[float, float]:
    q = (
        select(DeclaracionModel)
        .where(DeclaracionModel.year == year, DeclaracionModel.month == month)
        .order_by(desc(DeclaracionModel.fecha_presentacion).nullslast(), desc(DeclaracionModel.id))
        .limit(1)
    )
    rfc_value = (rfc or "").strip()
    if rfc_value:
        q = q.where(DeclaracionModel.rfc == rfc_value)
    row = db.execute(q).scalar_one_or_none()
    if not row:
        return 0.0, 0.0
    try:
        saldo_a_favor = float(row.saldo_a_favor) if row.saldo_a_favor is not None else 0.0
        saldo_a_pagar = float(row.saldo_a_pagar) if row.saldo_a_pagar is not None else 0.0
        return saldo_a_favor, saldo_a_pagar
    except Exception:
        return 0.0, 0.0


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
    tipo_decl = _normalize_tipo_declaracion(tipo_declaracion)
    year, month = _resolve_period_or_404(
        db,
        tipo_decl=tipo_decl,
        year=year,
        month=month,
    )

    _, usos_mensual, regimen = _load_config_for_rfc(
        db,
        rfc=x_rfc,
        tipo_declaracion_clave=TIPO_DECL_MENSUAL,
        ejercicio=year,
    )

    if tipo_decl == TIPO_DECL_ANUAL:
        config_anual, usos_anual, _ = _load_config_for_rfc(
            db,
            rfc=x_rfc,
            tipo_declaracion_clave=TIPO_DECL_ANUAL,
            ejercicio=year,
        )
        data_anual, periodos_incluidos = _compute_year_data(
            db,
            year=year,
            mi_rfc=x_rfc,
            gasto_uso_cfdi_allowlist=usos_anual,
        )
        incluir_acumulado = bool(config_anual.get("incluir_acumulado_mensual_en_anual"))
        data_mensual_acumulado = None
        if incluir_acumulado:
            data_mensual_acumulado, _ = _compute_year_data(
                db,
                year=year,
                mi_rfc=x_rfc,
                gasto_uso_cfdi_allowlist=usos_mensual,
            )

        iva_causado_sugerido = data_anual["plat_iva_tras"] + data_anual["ingresos_trasl"]
        iva_acreditable_anual_sugerido = data_anual["gastos_trasl"]
        iva_acreditable_mensual_acumulado_sugerido = data_mensual_acumulado["gastos_trasl"] if data_mensual_acumulado else 0.0
        iva_retenido_plat = data_anual["plat_iva_ret"]
        iva_neto_sugerido = iva_causado_sugerido - (iva_acreditable_anual_sugerido + iva_acreditable_mensual_acumulado_sugerido) - iva_retenido_plat
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
            "iva_acreditable_sugerido": (iva_acreditable_anual_sugerido + iva_acreditable_mensual_acumulado_sugerido),
            "iva_retenido_plat": iva_retenido_plat,
            "iva_neto_sugerido": iva_neto_sugerido,
        }

    data = compute_period_data(db, year, month, mi_rfc=x_rfc, gasto_uso_cfdi_allowlist=usos_mensual)
    iva_causado_sugerido = data["plat_iva_tras"] + data["ingresos_trasl"]
    iva_acreditable_sugerido = data["gastos_trasl"]
    iva_retenido_plat = data["plat_iva_ret"]
    iva_neto_sugerido = iva_causado_sugerido - iva_acreditable_sugerido - iva_retenido_plat
    declaracion_pdf = db.execute(
        select(DeclaracionModel)
        .where(DeclaracionModel.year == year, DeclaracionModel.month == month)
        .order_by(desc(DeclaracionModel.fecha_presentacion).nullslast(), desc(DeclaracionModel.id))
        .limit(1)
    ).scalar_one_or_none()
    mi_rfc = (x_rfc or "").strip() or None
    if not mi_rfc:
        mi_rfc = declaracion_pdf.rfc if declaracion_pdf and declaracion_pdf.rfc else None
    if not mi_rfc:
        ret_rows = data.get("ret_rows") or []
        mi_rfc = (ret_rows[0].receptor_rfc if ret_rows else None) or None

    prev_year, prev_month = _previous_period(year, month)
    saldo_a_favor_anterior, saldo_a_pagar_anterior = _fetch_saldos(
        db, prev_year, prev_month, mi_rfc
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
    tipo_decl = _normalize_tipo_declaracion(tipo_declaracion)
    year, month = _resolve_period_or_404(
        db,
        tipo_decl=tipo_decl,
        year=year,
        month=month,
    )

    if tipo_decl == TIPO_DECL_ANUAL:
        _, usos, regimen = _load_config_for_rfc(
            db,
            rfc=x_rfc,
            tipo_declaracion_clave=TIPO_DECL_ANUAL,
            ejercicio=year,
        )
        data, periodos = _compute_year_data(
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

    _, usos, regimen = _load_config_for_rfc(
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
    tipo_decl = _normalize_tipo_declaracion(tipo_declaracion)
    year, month = _resolve_period_or_404(
        db,
        tipo_decl=tipo_decl,
        year=year,
        month=month,
    )

    if tipo_decl == TIPO_DECL_ANUAL:
        config_anual, usos_anual, regimen = _load_config_for_rfc(
            db,
            rfc=x_rfc,
            tipo_declaracion_clave=TIPO_DECL_ANUAL,
            ejercicio=year,
        )
        data_anual, periodos_incluidos = _compute_year_data(
            db,
            year=year,
            mi_rfc=x_rfc,
            gasto_uso_cfdi_allowlist=usos_anual,
        )
        incluir_acumulado = bool(config_anual.get("incluir_acumulado_mensual_en_anual"))
        data_mensual_acumulado = None
        usos_mensual: set[str] = set()
        if incluir_acumulado:
            _, usos_mensual, _ = _load_config_for_rfc(
                db,
                rfc=x_rfc,
                tipo_declaracion_clave=TIPO_DECL_MENSUAL,
                ejercicio=year,
            )
            data_mensual_acumulado, _ = _compute_year_data(
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
            "ingresos_base": float((data_anual.get("ingresos_base") or 0.0) + (data_mensual_acumulado.get("ingresos_base") or 0.0) if data_mensual_acumulado else (data_anual.get("ingresos_base") or 0.0)),
            "isr_retenido": float(data_anual.get("plat_isr_ret") or 0.0),
            "iva_retenido": float(data_anual.get("plat_iva_ret") or 0.0),
            "iva_acreditable": float((data_anual.get("gastos_trasl") or 0.0) + (data_mensual_acumulado.get("gastos_trasl") or 0.0)),
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

    _, usos_mensual, _ = _load_config_for_rfc(
        db,
        rfc=x_rfc,
        tipo_declaracion_clave=TIPO_DECL_MENSUAL,
        ejercicio=year,
    )

    data = compute_period_data(db, year, month, mi_rfc=x_rfc, gasto_uso_cfdi_allowlist=usos_mensual)
    ingresos_total_sin_iva, iva_trasladado_sel, effective_income_source = calc_income_and_iva_sources(
        data, income_source
    )

    declaracion_pdf = db.execute(
        select(DeclaracionModel)
        .where(DeclaracionModel.year == year, DeclaracionModel.month == month)
        .order_by(desc(DeclaracionModel.fecha_presentacion).nullslast(), desc(DeclaracionModel.id))
        .limit(1)
    ).scalar_one_or_none()

    mi_rfc = (x_rfc or "").strip() or None
    if not mi_rfc:
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
        dec_entity = declaracion_model_to_entity(declaracion_pdf)
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

    prev_year, prev_month = _previous_period(year, month)
    saldo_a_favor_anterior, saldo_a_pagar_anterior = _fetch_saldos(
        db, prev_year, prev_month, mi_rfc
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


@router.get(
    "/sat_hoja.txt",
    summary="Hoja SAT",
    description="Devuelve texto plano con hoja SAT del periodo.",
)
def sat_hoja_txt(
    year: Optional[int] = None,
    month: Optional[int] = None,
    income_source: str = "auto",
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> Response:
    if year is None or month is None:
        raise HTTPException(status_code=400, detail="year y month son requeridos")

    data = compute_period_data(db, year, month, mi_rfc=x_rfc)
    hoja_text, effective = build_hoja_sat_text(year, month, income_source, data, format_money)
    return text_response(
        hoja_text,
        filename=f"hoja_sat_{year}_{month:02d}_{effective}.txt",
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
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> Response:
    if year is None or month is None:
        raise HTTPException(status_code=400, detail="year y month son requeridos")

    data = compute_period_data(db, year, month, mi_rfc=x_rfc)
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

    return csv_response(
        out.getvalue(),
        filename=f"sat_report_{year}_{month:02d}.csv",
    )
