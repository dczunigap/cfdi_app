from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import DeclaracionModel, RegimenFiscalCatalogModel, RfcModel
from app.adapters.outbound.db.period_data import compute_period_data, month_options, pick_default_period
from app.adapters.outbound.db.repositories.declaracion_config import SqlDeclaracionConfigRepository
from app.adapters.services.parsers.pdf_parser import LocalPdfParser
from app.application.declaraciones.payload import build_declaracion_payload
from app.application.reportes.periodo import calc_income_and_iva_sources
from app.domain.declaraciones.entities import DeclaracionPDF

TIPO_DECL_MENSUAL = "MENSUAL"
TIPO_DECL_ANUAL = "ANUAL"


def declaracion_model_to_entity(model) -> DeclaracionPDF:
    return DeclaracionPDF(
        year=model.year,
        month=model.month,
        rfc=model.rfc,
        folio=model.folio,
        fecha_presentacion=model.fecha_presentacion,
        saldo_a_favor=model.saldo_a_favor,
        saldo_a_pagar=model.saldo_a_pagar,
        sha256=model.sha256,
        filename=model.filename,
        original_name=model.original_name,
        num_pages=model.num_pages,
        text_excerpt=model.text_excerpt,
        created_at=model.created_at,
    )


def normalize_tipo_declaracion(value: str | None) -> str:
    normalized = (value or TIPO_DECL_MENSUAL).strip().upper()
    if normalized not in {TIPO_DECL_MENSUAL, TIPO_DECL_ANUAL}:
        raise HTTPException(status_code=400, detail="tipo_declaracion invalido. Use MENSUAL o ANUAL")
    return normalized


def resolve_period_or_404(
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


def resolve_regimen_for_rfc(db: Session, rfc: str) -> RegimenFiscalCatalogModel:
    row = db.execute(
        select(RegimenFiscalCatalogModel)
        .select_from(RfcModel)
        .join(RegimenFiscalCatalogModel, RfcModel.regimen_fiscal_id == RegimenFiscalCatalogModel.id)
        .where(RfcModel.rfc == rfc)
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=400, detail="RFC no registrado o sin regimen fiscal")
    return row


def load_config_for_rfc(
    db: Session,
    *,
    rfc: str,
    tipo_declaracion_clave: str,
    ejercicio: int | None = None,
) -> tuple[dict, set[str], RegimenFiscalCatalogModel]:
    regimen = resolve_regimen_for_rfc(db, rfc)
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


def compute_year_data(
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


def previous_period(year: int, month: int) -> tuple[int, int]:
    if month <= 1:
        return year - 1, 12
    return year, month - 1


def fetch_saldos(db: Session, year: int, month: int, rfc: str | None) -> tuple[float, float]:
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


def fetch_saldos_acumulados_ejercicio(
    db: Session,
    *,
    year: int,
    month: int,
    rfc: str | None,
) -> tuple[float, float]:
    """
    Calcula el saldo disponible arrastrable dentro del mismo ejercicio antes del
    mes consultado, descontando meses previos con saldo a pagar.
    """
    if month <= 1:
        return 0.0, 0.0

    rfc_value = (rfc or "").strip()
    q = (
        select(DeclaracionModel)
        .where(
            DeclaracionModel.year == year,
            DeclaracionModel.month < month,
        )
        .order_by(
            asc(DeclaracionModel.month),
            desc(DeclaracionModel.fecha_presentacion).nullslast(),
            desc(DeclaracionModel.id),
        )
    )
    if rfc_value:
        q = q.where(DeclaracionModel.rfc == rfc_value)

    rows = db.execute(q).scalars().all()
    if not rows:
        return 0.0, 0.0

    latest_by_month: dict[int, DeclaracionModel] = {}
    for row in rows:
        row_month = int(row.month)
        if row_month not in latest_by_month:
            latest_by_month[row_month] = row

    saldo_disponible = 0.0
    saldo_a_pagar_ultimo = 0.0

    for current_month in sorted(latest_by_month):
        row = latest_by_month[current_month]
        try:
            saldo_favor_mes = float(row.saldo_a_favor) if row.saldo_a_favor is not None else 0.0
            saldo_pagar_mes = float(row.saldo_a_pagar) if row.saldo_a_pagar is not None else 0.0
            cantidad_cargo_mes = float(row.cantidad_a_cargo) if row.cantidad_a_cargo is not None else 0.0
        except Exception:
            saldo_favor_mes = 0.0
            saldo_pagar_mes = 0.0
            cantidad_cargo_mes = 0.0

        saldo_disponible += saldo_favor_mes
        saldo_disponible -= saldo_pagar_mes
        saldo_disponible -= cantidad_cargo_mes
        saldo_disponible = max(saldo_disponible, 0.0)
        saldo_a_pagar_ultimo = saldo_pagar_mes

    return saldo_disponible, saldo_a_pagar_ultimo


def get_latest_declaracion_pdf(db: Session, year: int, month: int):
    return db.execute(
        select(DeclaracionModel)
        .where(DeclaracionModel.year == year, DeclaracionModel.month == month)
        .order_by(desc(DeclaracionModel.fecha_presentacion).nullslast(), desc(DeclaracionModel.id))
        .limit(1)
    ).scalar_one_or_none()


def resolve_mi_rfc(x_rfc: str, declaracion_pdf, data: dict) -> str | None:
    mi_rfc = (x_rfc or "").strip() or None
    if not mi_rfc:
        mi_rfc = declaracion_pdf.rfc if declaracion_pdf and declaracion_pdf.rfc else None
    if not mi_rfc:
        ret_rows = data.get("ret_rows") or []
        mi_rfc = (ret_rows[0].receptor_rfc if ret_rows else None) or None
    return mi_rfc


def build_acuse_payload_and_checks(
    *,
    declaracion_pdf,
    year: int,
    month: int,
    mi_rfc: str | None,
    data: dict,
    ingresos_total_sin_iva: float,
    iva_trasladado_total: float,
) -> tuple[dict | None, list[dict]]:
    acuse_payload = None
    acuse_checks: list[dict] = []
    if not declaracion_pdf or not (declaracion_pdf.text_excerpt or "").strip():
        return acuse_payload, acuse_checks

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
    return acuse_payload, acuse_checks


def build_sat_report_csv(data: dict, year: int, month: int, income_source: str) -> str:
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
    return out.getvalue()
