from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, desc, and_
from sqlalchemy.orm import Session

from db import engine, SessionLocal
from models import Base, Factura, Concepto, Pago, RetencionPlataforma
from parser_xml import detect_xml_kind, parse_cfdi_40, parse_retenciones_plataforma

from config import MI_RFC


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Contabilidad CFDI (local)")


def money(value, currency: str | None = "MXN") -> str:
    """Formatea números con comas y 2 decimales: 1,000,000.00 MXN"""
    if value is None:
        return ""
    try:
        num = float(value)
    except Exception:
        return str(value)
    cur = (currency or "MXN").strip() or "MXN"
    return f"{num:,.2f} {cur}"


templates.env.filters["money"] = money


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    return SessionLocal()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, msg: str | None = None) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request, "mi_rfc": MI_RFC, "msg": msg})


@app.post("/importar")
async def importar(files: list[UploadFile] = File(...)):
    inserted = 0
    skipped = 0
    errors = 0

    inserted_ret = 0
    skipped_ret = 0

    db = get_db()
    try:
        for f in files:
            try:
                xml_bytes = await f.read()
                kind = detect_xml_kind(xml_bytes)

                if kind == "cfdi":
                    parsed = parse_cfdi_40(xml_bytes)
                    uuid = parsed.get("uuid")

                    if uuid:
                        exists = db.scalar(select(Factura.id).where(Factura.uuid == uuid))
                        if exists:
                            skipped += 1
                            continue

                    factura = Factura(
                        uuid=uuid,
                        version=parsed.get("version"),
                        tipo_comprobante=parsed.get("tipo_comprobante"),
                        fecha_emision=parsed.get("fecha_emision"),
                        year_emision=parsed.get("year_emision"),
                        month_emision=parsed.get("month_emision"),
                        naturaleza=parsed.get("naturaleza"),
                        emisor_rfc=parsed.get("emisor_rfc"),
                        emisor_nombre=parsed.get("emisor_nombre"),
                        receptor_rfc=parsed.get("receptor_rfc"),
                        receptor_nombre=parsed.get("receptor_nombre"),
                        uso_cfdi=parsed.get("uso_cfdi"),
                        moneda=parsed.get("moneda"),
                        metodo_pago=parsed.get("metodo_pago"),
                        forma_pago=parsed.get("forma_pago"),
                        subtotal=parsed.get("subtotal"),
                        descuento=parsed.get("descuento"),
                        total=parsed.get("total"),
                        total_trasladados=parsed.get("total_trasladados"),
                        total_retenidos=parsed.get("total_retenidos"),
                        xml_text=xml_bytes.decode("utf-8", errors="replace"),
                    )

                    for c in parsed.get("conceptos", []):
                        factura.conceptos.append(
                            Concepto(
                                clave_prod_serv=c.get("clave_prod_serv"),
                                cantidad=c.get("cantidad"),
                                clave_unidad=c.get("clave_unidad"),
                                descripcion=c.get("descripcion"),
                                valor_unitario=c.get("valor_unitario"),
                                importe=c.get("importe"),
                                objeto_imp=c.get("objeto_imp"),
                            )
                        )

                    for p in parsed.get("pagos", []):
                        factura.pagos.append(
                            Pago(
                                fecha_pago=p.get("fecha_pago"),
                                year_pago=p.get("year_pago"),
                                month_pago=p.get("month_pago"),
                                monto=p.get("monto"),
                                moneda_p=p.get("moneda_p"),
                                forma_pago_p=p.get("forma_pago_p"),
                            )
                        )

                    db.add(factura)
                    db.commit()
                    inserted += 1

                elif kind == "retenciones":
                    parsed = parse_retenciones_plataforma(xml_bytes)
                    uuid = parsed.get("uuid")

                    if uuid:
                        exists = db.scalar(select(RetencionPlataforma.id).where(RetencionPlataforma.uuid == uuid))
                        if exists:
                            skipped_ret += 1
                            continue

                    ret = RetencionPlataforma(
                        uuid=uuid,
                        version=parsed.get("version"),
                        fecha_exp=parsed.get("fecha_exp"),
                        ejercicio=parsed.get("ejercicio"),
                        mes_ini=parsed.get("mes_ini"),
                        mes_fin=parsed.get("mes_fin"),
                        emisor_rfc=parsed.get("emisor_rfc"),
                        emisor_nombre=parsed.get("emisor_nombre"),
                        receptor_rfc=parsed.get("receptor_rfc"),
                        receptor_nombre=parsed.get("receptor_nombre"),
                        monto_tot_operacion=parsed.get("monto_tot_operacion"),
                        monto_tot_grav=parsed.get("monto_tot_grav"),
                        monto_tot_exent=parsed.get("monto_tot_exent"),
                        monto_tot_ret=parsed.get("monto_tot_ret"),
                        periodicidad=parsed.get("periodicidad"),
                        num_serv=parsed.get("num_serv"),
                        mon_tot_serv_siva=parsed.get("mon_tot_serv_siva"),
                        total_iva_trasladado=parsed.get("total_iva_trasladado"),
                        total_iva_retenido=parsed.get("total_iva_retenido"),
                        total_isr_retenido=parsed.get("total_isr_retenido"),
                        dif_iva_entregado_prest_serv=parsed.get("dif_iva_entregado_prest_serv"),
                        mon_total_por_uso_plataforma=parsed.get("mon_total_por_uso_plataforma"),
                        xml_text=xml_bytes.decode("utf-8", errors="replace"),
                    )
                    db.add(ret)
                    db.commit()
                    inserted_ret += 1

                else:
                    # XML desconocido
                    errors += 1

            except Exception:
                db.rollback()
                errors += 1

    finally:
        db.close()

    msg = (
        f"CFDI: {inserted} insertados, {skipped} duplicados. "
        f"Retenciones: {inserted_ret} insertadas, {skipped_ret} duplicadas. "
        f"Errores: {errors}."
    )
    return RedirectResponse(url=f"/?msg={msg}", status_code=303)


@app.get("/facturas", response_class=HTMLResponse)
def listar_facturas(request: Request, tipo: str | None = None, naturaleza: str | None = None) -> HTMLResponse:
    db = get_db()
    try:
        q = select(Factura).order_by(desc(Factura.fecha_emision).nullslast(), desc(Factura.id)).limit(500)
        if tipo:
            q = q.where(Factura.tipo_comprobante == tipo.upper())
        if naturaleza:
            q = q.where(Factura.naturaleza == naturaleza.lower())
        facturas = db.scalars(q).all()
        return templates.TemplateResponse(
            "facturas.html",
            {
                "request": request,
                "facturas": facturas,
                "mi_rfc": MI_RFC,
                "tipo": tipo or "",
                "naturaleza": naturaleza or "",
            },
        )
    finally:
        db.close()


@app.get("/retenciones", response_class=HTMLResponse)
def listar_retenciones(request: Request, year: int | None = None, month: int | None = None) -> HTMLResponse:
    db = get_db()
    try:
        q = select(RetencionPlataforma).order_by(desc(RetencionPlataforma.fecha_exp).nullslast(), desc(RetencionPlataforma.id)).limit(300)
        if year is not None:
            q = q.where(RetencionPlataforma.ejercicio == year)
        if month is not None:
            # incluye rangos (MesIni..MesFin)
            q = q.where(and_(RetencionPlataforma.mes_ini <= month, RetencionPlataforma.mes_fin >= month))
        rows = db.scalars(q).all()
        return templates.TemplateResponse(
            "retenciones.html",
            {"request": request, "rows": rows, "mi_rfc": MI_RFC, "year": year, "month": month},
        )
    finally:
        db.close()


@app.get("/retenciones/{ret_id}", response_class=HTMLResponse)
def detalle_retencion(request: Request, ret_id: int) -> HTMLResponse:
    db = get_db()
    try:
        ret = db.get(RetencionPlataforma, ret_id)
        if not ret:
            return HTMLResponse("No encontrada", status_code=404)
        return templates.TemplateResponse("retencion_detalle.html", {"request": request, "ret": ret, "mi_rfc": MI_RFC})
    finally:
        db.close()


@app.get("/facturas/{factura_id}", response_class=HTMLResponse)
def detalle_factura(request: Request, factura_id: int) -> HTMLResponse:
    db = get_db()
    try:
        factura = db.get(Factura, factura_id)
        if not factura:
            return HTMLResponse("No encontrada", status_code=404)
        _ = factura.conceptos
        _ = factura.pagos
        return templates.TemplateResponse("detalle.html", {"request": request, "factura": factura, "mi_rfc": MI_RFC})
    finally:
        db.close()


def _signed(value, tipo: str | None):
    if value is None:
        return 0.0
    return float(value) * (-1.0 if (tipo or "").upper() == "E" else 1.0)


def _pick_default_period(db: Session) -> tuple[int | None, int | None]:
    last_fact = db.execute(
        select(Factura.year_emision, Factura.month_emision)
        .where(Factura.year_emision.isnot(None), Factura.month_emision.isnot(None))
        .order_by(desc(Factura.year_emision), desc(Factura.month_emision))
        .limit(1)
    ).first()

    last_ret = db.execute(
        select(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_fin)
        .where(RetencionPlataforma.ejercicio.isnot(None), RetencionPlataforma.mes_fin.isnot(None))
        .order_by(desc(RetencionPlataforma.ejercicio), desc(RetencionPlataforma.mes_fin))
        .limit(1)
    ).first()

    cand = []
    if last_fact:
        cand.append((int(last_fact[0]), int(last_fact[1])))
    if last_ret:
        cand.append((int(last_ret[0]), int(last_ret[1])))

    if not cand:
        return None, None
    return max(cand)


def _month_options(db: Session):
    m1 = db.execute(
        select(Factura.year_emision, Factura.month_emision)
        .where(Factura.year_emision.isnot(None), Factura.month_emision.isnot(None))
        .group_by(Factura.year_emision, Factura.month_emision)
    ).all()
    m2 = db.execute(
        select(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_fin)
        .where(RetencionPlataforma.ejercicio.isnot(None), RetencionPlataforma.mes_fin.isnot(None))
        .group_by(RetencionPlataforma.ejercicio, RetencionPlataforma.mes_fin)
    ).all()
    return sorted({(int(y), int(m)) for (y, m) in (m1 + m2) if y and m}, reverse=True)


def _compute_period_data(db: Session, year: int, month: int):
    # CFDI por emisión
    docs = db.scalars(
        select(Factura)
        .where(Factura.year_emision == year, Factura.month_emision == month)
        .order_by(desc(Factura.fecha_emision).nullslast(), desc(Factura.id))
    ).all()

    ingresos_total = ingresos_trasl = ingresos_ret = 0.0
    gastos_total = gastos_trasl = gastos_ret = 0.0
    ingresos_base = 0.0  # subtotal - descuento (aprox. sin IVA)
    p_count = 0

    # preload pagos relationship for P checks
    for d in docs:
        _ = d.pagos

    for d in docs:
        t = (d.tipo_comprobante or "").upper()
        if t == "P":
            p_count += 1
            continue

        base = float(d.subtotal or 0.0) - float(d.descuento or 0.0)

        if d.naturaleza == "ingreso":
            ingresos_total += _signed(d.total, t)
            ingresos_trasl += _signed(d.total_trasladados, t)
            ingresos_ret += _signed(d.total_retenidos, t)
            ingresos_base += _signed(base, t)
        elif d.naturaleza == "gasto":
            gastos_total += _signed(d.total, t)
            gastos_trasl += _signed(d.total_trasladados, t)
            gastos_ret += _signed(d.total_retenidos, t)

    # Pagos (P) por FechaPago
    pagos_rows = db.execute(
        select(Pago, Factura.naturaleza)
        .join(Factura, Pago.factura_id == Factura.id)
        .where(Pago.year_pago == year, Pago.month_pago == month)
        .order_by(desc(Pago.fecha_pago).nullslast(), desc(Pago.id))
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

    # Retenciones de plataformas por periodo
    ret_rows = db.scalars(
        select(RetencionPlataforma)
        .where(
            RetencionPlataforma.ejercicio == year,
            RetencionPlataforma.mes_ini <= month,
            RetencionPlataforma.mes_fin >= month,
        )
        .order_by(desc(RetencionPlataforma.fecha_exp).nullslast(), desc(RetencionPlataforma.id))
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


def _checklist(db: Session, year: int, month: int, data: dict, income_source: str, effective_income_source: str):
    checks = []

    ret_rows = data["ret_rows"]
    docs = data["docs"]

    # 1) Retenciones presentes
    if not ret_rows:
        checks.append({"level": "error", "title": "Falta XML de retenciones de plataformas", "detail": "Sin este XML, no podrás acreditar ISR/IVA retenido por Mercado Libre en el periodo."})
    else:
        checks.append({"level": "ok", "title": "Retenciones de plataformas encontradas", "detail": f"Se detectaron {len(ret_rows)} XML(s) de retenciones para el periodo."})

    # 2) Receptor RFC coincide con MI_RFC
    if ret_rows:
        recs = sorted({(r.receptor_rfc or '').upper() for r in ret_rows if (r.receptor_rfc or '').strip()})
        if recs and (MI_RFC or "").upper() not in recs:
            checks.append({"level": "warn", "title": "El RFC receptor en retenciones no coincide con tu MI_RFC", "detail": f"MI_RFC={MI_RFC}. Receptor(es) en XML: {', '.join(recs)}. Revisa que tu RFC esté bien en config.py y en Mercado Libre."})
        else:
            checks.append({"level": "ok", "title": "RFC receptor en retenciones coincide", "detail": "El RFC del receptor en retenciones coincide con tu configuración o no viene informado."})

    # 3) Periodo mensual
    bad_ranges = [r for r in ret_rows if (r.mes_ini or 0) != (r.mes_fin or 0)]
    if bad_ranges:
        checks.append({"level": "warn", "title": "Retención con rango de meses", "detail": "Hay XML(s) donde MesIni != MesFin. Para la declaración mensual asegúrate de asignarlo al mes correcto."})

    # 4) Timbrado fuera del mes (normal)
    off_month = []
    for r in ret_rows:
        if r.fecha_exp and (r.fecha_exp.year != year or r.fecha_exp.month != month):
            off_month.append(r)
    if off_month:
        checks.append({"level": "info", "title": "Retenciones timbradas fuera del mes", "detail": "Es común que el XML se timbre en el mes siguiente. Usa el Periodo (Ejercicio/Mes) del XML, no la FechaExp."})

    # 5) UsoCFDI faltante en gastos
    missing_uso = [d for d in docs if d.naturaleza == "gasto" and not (d.uso_cfdi or "").strip() and (d.tipo_comprobante or "").upper() != "P"]
    if missing_uso:
        checks.append({"level": "warn", "title": "Hay gastos sin UsoCFDI", "detail": f"{len(missing_uso)} CFDI de gasto no traen UsoCFDI (o no se pudo leer). Revisa esos XML."})
    else:
        checks.append({"level": "ok", "title": "UsoCFDI en gastos", "detail": "Tus CFDI de gastos del mes traen UsoCFDI o no hay gastos importados."})

    # 6) Gastos inexistentes
    gastos_count = sum(1 for d in docs if d.naturaleza == "gasto" and (d.tipo_comprobante or "").upper() != "P")
    if gastos_count == 0:
        checks.append({"level": "warn", "title": "No hay CFDI de gastos en el periodo", "detail": "Dijiste que tienes gasolina/telefonía/mantenimiento. Si no los importas, no podrás acreditar IVA ni deducirlos."})

    # 7) Control de doble conteo (plataforma + CFDI ingresos)
    ingresos_count = sum(1 for d in docs if d.naturaleza == "ingreso" and (d.tipo_comprobante or "").upper() != "P")
    if ret_rows and ingresos_count > 0 and data["ingresos_base"] > 0:
        if effective_income_source in ["plataforma", "cfdi"]:
            checks.append({
                "level": "info",
                "title": "Doble fuente detectada (evitando doble conteo)",
                "detail": f"Se detectaron ingresos por plataforma y CFDI de ingreso. Para evitar doble conteo, la declaración está usando: {effective_income_source.upper()} (selector: {income_source})."
            })
        else:
            checks.append({
                "level": "warn",
                "title": "Posible doble conteo de ingresos",
                "detail": "Estás sumando ingresos por plataforma (retenciones) y CFDI de ingreso en el mismo mes. Solo hazlo si esos CFDI son ventas fuera de Mercado Libre."
            })

# 8) CFDI tipo P sin nodos Pago
    p_no_pagos = [d for d in docs if (d.tipo_comprobante or "").upper() == "P" and len(d.pagos) == 0]
    if p_no_pagos:
        checks.append({"level": "warn", "title": "CFDI tipo P sin renglones <Pago>", "detail": f"{len(p_no_pagos)} CFDI tipo P del mes no tienen nodos de Pago detectables. Puede ser XML incompleto o con un namespace distinto."})

    # 9) Moneda distinta de MXN
    other_cur = sorted({(d.moneda or "").upper() for d in docs if (d.moneda or "").strip() and (d.moneda or "").upper() != "MXN"})
    if other_cur:
        checks.append({"level": "info", "title": "Moneda distinta de MXN", "detail": f"Se detectaron CFDI en moneda: {', '.join(other_cur)}. Para la declaración debes convertir a MXN con tipo de cambio aplicable."})

    return checks


@app.get("/summary", response_class=HTMLResponse)
def resumen_mensual(request: Request, year: int | None = None, month: int | None = None) -> HTMLResponse:
    db = get_db()
    try:
        if year is None or month is None:
            year, month = _pick_default_period(db)

        month_options = _month_options(db)
        if year is None or month is None:
            return templates.TemplateResponse("empty.html", {"request": request, "mi_rfc": MI_RFC})

        data = _compute_period_data(db, year, month)

        # Papel de trabajo sugerido (IVA)
        iva_causado_sugerido = data["plat_iva_tras"] + data["ingresos_trasl"]
        iva_acreditable_sugerido = data["gastos_trasl"]
        iva_retenido_plat = data["plat_iva_ret"]
        iva_neto_sugerido = iva_causado_sugerido - iva_acreditable_sugerido - iva_retenido_plat

        return templates.TemplateResponse(
            "summary.html",
            {
                "request": request,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "month_options": month_options,
                **data,
                "iva_causado_sugerido": iva_causado_sugerido,
                "iva_acreditable_sugerido": iva_acreditable_sugerido,
                "iva_retenido_plat": iva_retenido_plat,
                "iva_neto_sugerido": iva_neto_sugerido,
            },
        )
    finally:
        db.close()


@app.get("/declaracion", response_class=HTMLResponse)
def modo_declaracion(request: Request, year: int | None = None, month: int | None = None, income_source: str = "auto") -> HTMLResponse:
    """Modo declaración (sin coeficiente): ingresos + retenciones + checklist."""
    db = get_db()
    try:
        if year is None or month is None:
            year, month = _pick_default_period(db)

        month_options = _month_options(db)
        if year is None or month is None:
            return templates.TemplateResponse("empty.html", {"request": request, "mi_rfc": MI_RFC})

        data = _compute_period_data(db, year, month)

        # “Ingresos para capturar” (sin IVA)
        # En tu caso (Mercado Libre), es común que:
        # - Retenciones (Plataformas) y CFDI de ingreso representen las MISMAS ventas.
        # Para evitar doble conteo, aquí eliges la fuente.
        income_source = (income_source or "auto").lower().strip()
        plat = float(data["plat_ing_siva"] or 0.0)
        cfdi_base = float(data["ingresos_base"] or 0.0)

        effective_income_source = "plataforma"
        if income_source == "plataforma":
            ingresos_total_sin_iva = plat
            effective_income_source = "plataforma"
        elif income_source == "cfdi":
            ingresos_total_sin_iva = cfdi_base
            effective_income_source = "cfdi"
        elif income_source == "ambos":
            ingresos_total_sin_iva = plat + cfdi_base
            effective_income_source = "ambos"
        else:
            # auto: si hay retenciones del mes, usa plataforma (evita doble conteo).
            if plat > 0:
                ingresos_total_sin_iva = plat
                effective_income_source = "plataforma"
            else:
                ingresos_total_sin_iva = cfdi_base
                effective_income_source = "cfdi"

# Retenciones para acreditar (principalmente plataforma)
        isr_retenido = data["plat_isr_ret"]
        iva_retenido = data["plat_iva_ret"]

        # IVA trasladado del periodo (plataforma + CFDI)
        iva_trasladado_total = data["plat_iva_tras"] + data["ingresos_trasl"]
        checks = _checklist(db, year, month, data, income_source=income_source, effective_income_source=effective_income_source)

        return templates.TemplateResponse(
            "declaracion.html",
            {
                "request": request,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "month_options": month_options,
                **data,
                "ingresos_total_sin_iva": ingresos_total_sin_iva,
                "isr_retenido": isr_retenido,
                "iva_retenido": iva_retenido,
                "iva_trasladado_total": iva_trasladado_total,
                "income_source": income_source,
                "effective_income_source": effective_income_source,
                "checks": checks,
            },
        )
    finally:
        db.close()


@app.get("/sat_report.csv")
def sat_report_csv(year: int, month: int, income_source: str = "auto"):
    """CSV de papel de trabajo mensual (ingresos + retenciones + IVA)"""
    db = get_db()
    try:
        data = _compute_period_data(db, year, month)

        income_source = (income_source or "auto").lower().strip()
        plat = float(data["plat_ing_siva"] or 0.0)
        cfdi_base = float(data["ingresos_base"] or 0.0)
        if income_source == "plataforma":
            ingresos_total_sin_iva = plat
        elif income_source == "cfdi":
            ingresos_total_sin_iva = cfdi_base
        elif income_source == "ambos":
            ingresos_total_sin_iva = plat + cfdi_base
        else:
            ingresos_total_sin_iva = plat if plat > 0 else cfdi_base
        iva_tras_total = data["plat_iva_tras"] + data["ingresos_trasl"]

        iva_causado = iva_tras_total
        iva_acreditable = data["gastos_trasl"]
        iva_neto = iva_causado - iva_acreditable - data["plat_iva_ret"]

        import csv, io
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow([
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
        ])
        w.writerow([
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
        ])

        return Response(
            content=out.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=sat_report_{year}_{month:02d}.csv"},
        )
    finally:
        db.close()
