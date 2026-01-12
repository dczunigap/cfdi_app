from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import FacturaModel, PagoModel, RetencionModel
from app.utils.money import apply_sign_factor


def pick_default_period(db: Session) -> tuple[Optional[int], Optional[int]]:
    last_fact = db.execute(
        select(FacturaModel.year_emision, FacturaModel.month_emision)
        .where(FacturaModel.year_emision.isnot(None), FacturaModel.month_emision.isnot(None))
        .order_by(desc(FacturaModel.year_emision), desc(FacturaModel.month_emision))
        .limit(1)
    ).first()

    last_ret = db.execute(
        select(RetencionModel.ejercicio, RetencionModel.mes_fin)
        .where(RetencionModel.ejercicio.isnot(None), RetencionModel.mes_fin.isnot(None))
        .order_by(desc(RetencionModel.ejercicio), desc(RetencionModel.mes_fin))
        .limit(1)
    ).first()

    candidates: list[tuple[int, int]] = []
    if last_fact:
        candidates.append((int(last_fact[0]), int(last_fact[1])))
    if last_ret:
        candidates.append((int(last_ret[0]), int(last_ret[1])))

    return max(candidates) if candidates else (None, None)


def month_options(db: Session) -> list[tuple[int, int]]:
    m1 = db.execute(
        select(FacturaModel.year_emision, FacturaModel.month_emision)
        .where(FacturaModel.year_emision.isnot(None), FacturaModel.month_emision.isnot(None))
        .group_by(FacturaModel.year_emision, FacturaModel.month_emision)
    ).all()

    m2 = db.execute(
        select(RetencionModel.ejercicio, RetencionModel.mes_fin)
        .where(RetencionModel.ejercicio.isnot(None), RetencionModel.mes_fin.isnot(None))
        .group_by(RetencionModel.ejercicio, RetencionModel.mes_fin)
    ).all()

    return sorted({(int(y), int(m)) for (y, m) in (m1 + m2) if y and m}, reverse=True)


def _signed(value: Optional[float], tipo: Optional[str]) -> float:
    return apply_sign_factor(value, tipo)


def compute_period_data(db: Session, year: int, month: int) -> dict:
    docs = db.scalars(
        select(FacturaModel)
        .where(FacturaModel.year_emision == year, FacturaModel.month_emision == month)
        .order_by(desc(FacturaModel.fecha_emision).nullslast(), desc(FacturaModel.id))
    ).all()

    for d in docs:
        _ = d.pagos

    ingresos_total = ingresos_trasl = ingresos_ret = 0.0
    gastos_total = gastos_trasl = gastos_ret = 0.0
    ingresos_base = 0.0
    p_count = 0

    for d in docs:
        tipo = (d.tipo_comprobante or "").upper()
        if tipo == "P":
            p_count += 1
            continue

        base = float(d.subtotal or 0.0) - float(d.descuento or 0.0)

        if d.naturaleza == "ingreso":
            ingresos_total += _signed(d.total, tipo)
            ingresos_trasl += _signed(d.total_trasladados, tipo)
            ingresos_ret += _signed(d.total_retenidos, tipo)
            ingresos_base += _signed(base, tipo)
        elif d.naturaleza == "gasto":
            gastos_total += _signed(d.total, tipo)
            gastos_trasl += _signed(d.total_trasladados, tipo)
            gastos_ret += _signed(d.total_retenidos, tipo)

    pagos_rows = db.execute(
        select(PagoModel, FacturaModel.naturaleza)
        .join(FacturaModel, PagoModel.factura_id == FacturaModel.id)
        .where(PagoModel.year_pago == year, PagoModel.month_pago == month)
        .order_by(desc(PagoModel.fecha_pago).nullslast(), desc(PagoModel.id))
    ).all()

    cash_in = cash_out = 0.0
    pagos_count = 0
    for pago, nat in pagos_rows:
        pagos_count += 1
        monto = float(pago.monto or 0.0)
        if nat == "cobro":
            cash_in += monto
        elif nat == "pago":
            cash_out += monto

    ret_rows = db.scalars(
        select(RetencionModel)
        .where(
            RetencionModel.ejercicio == year,
            RetencionModel.mes_ini <= month,
            RetencionModel.mes_fin >= month,
        )
        .order_by(desc(RetencionModel.fecha_exp).nullslast(), desc(RetencionModel.id))
    ).all()

    plat_ing_siva = sum(float(r.mon_tot_serv_siva or 0.0) for r in ret_rows)
    plat_iva_tras = sum(float(r.total_iva_trasladado or 0.0) for r in ret_rows)
    plat_iva_ret = sum(float(r.total_iva_retenido or 0.0) for r in ret_rows)
    plat_isr_ret = sum(float(r.total_isr_retenido or 0.0) for r in ret_rows)
    plat_comision = sum(float(r.mon_total_por_uso_plataforma or 0.0) for r in ret_rows)

    return {
        "docs": docs,
        "pagos_rows": pagos_rows,
        "ret_rows": ret_rows,
        "ingresos_total": ingresos_total,
        "ingresos_base": ingresos_base,
        "ingresos_trasl": ingresos_trasl,
        "ingresos_ret": ingresos_ret,
        "gastos_total": gastos_total,
        "gastos_trasl": gastos_trasl,
        "gastos_ret": gastos_ret,
        "p_count": p_count,
        "cash_in": cash_in,
        "cash_out": cash_out,
        "pagos_count": pagos_count,
        "plat_ing_siva": plat_ing_siva,
        "plat_iva_tras": plat_iva_tras,
        "plat_iva_ret": plat_iva_ret,
        "plat_isr_ret": plat_isr_ret,
        "plat_comision": plat_comision,
    }
