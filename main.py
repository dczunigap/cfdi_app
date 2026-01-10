from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session

from db import engine, SessionLocal
from models import Base, Factura, Concepto, Pago, RetencionPlataforma
from parser_xml import detect_xml_kind, parse_cfdi_40, parse_retenciones_plataforma

from config import MI_RFC


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Contabilidad CFDI (local)")


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


def _signed(total, tipo: str | None):
    if total is None:
        return 0.0
    return float(total) * (-1.0 if (tipo or "").upper() == "E" else 1.0)


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


@app.get("/summary", response_class=HTMLResponse)
def resumen_mensual(request: Request, year: int | None = None, month: int | None = None) -> HTMLResponse:
    db = get_db()
    try:
        if year is None or month is None:
            year, month = _pick_default_period(db)

        # Opciones para dropdown (union de meses de CFDI y retenciones)
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
        month_options = sorted({(int(y), int(m)) for (y, m) in (m1 + m2) if y and m}, reverse=True)

        # CFDI del mes por EMISIÓN (I/E/P)
        docs = db.scalars(
            select(Factura)
            .where(Factura.year_emision == year, Factura.month_emision == month)
            .order_by(desc(Factura.fecha_emision).nullslast(), desc(Factura.id))
        ).all()

        ingresos_total = 0.0
        ingresos_trasl = 0.0
        ingresos_ret = 0.0

        gastos_total = 0.0
        gastos_trasl = 0.0
        gastos_ret = 0.0

        p_count = 0

        for d in docs:
            t = (d.tipo_comprobante or "").upper()
            if t == "P":
                p_count += 1
                continue

            if d.naturaleza == "ingreso":
                ingresos_total += _signed(d.total, t)
                ingresos_trasl += _signed(d.total_trasladados, t)
                ingresos_ret += _signed(d.total_retenidos, t)
            elif d.naturaleza == "gasto":
                gastos_total += _signed(d.total, t)
                gastos_trasl += _signed(d.total_trasladados, t)
                gastos_ret += _signed(d.total_retenidos, t)

        # Pagos del mes por FechaPago (solo complementos P)
        pagos_rows = db.execute(
            select(Pago, Factura.naturaleza)
            .join(Factura, Pago.factura_id == Factura.id)
            .where(Pago.year_pago == year, Pago.month_pago == month)
            .order_by(desc(Pago.fecha_pago).nullslast(), desc(Pago.id))
        ).all()

        cash_in = 0.0
        cash_out = 0.0
        pagos_count = 0

        for pago, nat in pagos_rows:
            pagos_count += 1
            monto = float(pago.monto or 0.0)
            if nat == "cobro":
                cash_in += monto
            elif nat == "pago":
                cash_out += monto

        # Retenciones (Plataformas) del periodo (ejercicio/mes)
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

        # “Sugeridos” para declaración (papel de trabajo)
        # Importante: evita doble conteo. Se muestran separados.
        iva_causado_sugerido = plat_iva_tras + ingresos_trasl
        iva_acreditable_sugerido = gastos_trasl
        iva_retenido_plat = plat_iva_ret
        iva_neto_sugerido = iva_causado_sugerido - iva_acreditable_sugerido - iva_retenido_plat

        isr_retenido_plat = plat_isr_ret

        return templates.TemplateResponse(
            "summary.html",
            {
                "request": request,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "month_options": month_options,
                # CFDI emisión
                "ingresos_total": ingresos_total,
                "ingresos_trasl": ingresos_trasl,
                "ingresos_ret": ingresos_ret,
                "gastos_total": gastos_total,
                "gastos_trasl": gastos_trasl,
                "gastos_ret": gastos_ret,
                "p_count": p_count,
                # P pagos
                "cash_in": cash_in,
                "cash_out": cash_out,
                "pagos_count": pagos_count,
                "docs": docs[:200],
                "pagos_rows": pagos_rows[:200],
                # Retenciones
                "ret_rows": ret_rows,
                "plat_ing_siva": plat_ing_siva,
                "plat_iva_tras": plat_iva_tras,
                "plat_iva_ret": plat_iva_ret,
                "plat_isr_ret": plat_isr_ret,
                "plat_comision": plat_comision,
                # SAT sugeridos
                "iva_causado_sugerido": iva_causado_sugerido,
                "iva_acreditable_sugerido": iva_acreditable_sugerido,
                "iva_retenido_plat": iva_retenido_plat,
                "iva_neto_sugerido": iva_neto_sugerido,
                "isr_retenido_plat": isr_retenido_plat,
            },
        )
    finally:
        db.close()


@app.get("/sat_report.csv")
def sat_report_csv(year: int, month: int):
    """Exporta un CSV con un papel de trabajo mensual (IVA/ISR) basado en CFDI + Retenciones."""
    db = get_db()
    try:
        # Retenciones del periodo
        ret_rows = db.scalars(
            select(RetencionPlataforma)
            .where(
                RetencionPlataforma.ejercicio == year,
                RetencionPlataforma.mes_ini <= month,
                RetencionPlataforma.mes_fin >= month,
            )
        ).all()

        plat_ing_siva = sum(float(r.mon_tot_serv_siva or 0.0) for r in ret_rows)
        plat_iva_tras = sum(float(r.total_iva_trasladado or 0.0) for r in ret_rows)
        plat_iva_ret = sum(float(r.total_iva_retenido or 0.0) for r in ret_rows)
        plat_isr_ret = sum(float(r.total_isr_retenido or 0.0) for r in ret_rows)

        # CFDI I/E del mes (excluye P)
        docs = db.scalars(
            select(Factura)
            .where(Factura.year_emision == year, Factura.month_emision == month)
        ).all()

        ingresos_trasl = 0.0
        gastos_trasl = 0.0
        ingresos_total = 0.0
        gastos_total = 0.0

        for d in docs:
            t = (d.tipo_comprobante or "").upper()
            if t == "P":
                continue
            if d.naturaleza == "ingreso":
                ingresos_total += _signed(d.total, t)
                ingresos_trasl += _signed(d.total_trasladados, t)
            elif d.naturaleza == "gasto":
                gastos_total += _signed(d.total, t)
                gastos_trasl += _signed(d.total_trasladados, t)

        iva_causado = plat_iva_tras + ingresos_trasl
        iva_acreditable = gastos_trasl
        iva_neto = iva_causado - iva_acreditable - plat_iva_ret

        import csv, io
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["periodo", "plat_ingresos_sin_iva", "plat_iva_trasladado", "plat_iva_retenido", "plat_isr_retenido",
                    "cfdi_ingresos_total", "cfdi_iva_trasladado", "cfdi_gastos_total", "cfdi_iva_acreditable",
                    "iva_causado_sugerido", "iva_acreditable_sugerido", "iva_retenido_plataforma", "iva_neto_sugerido"])
        w.writerow([f"{year}-{month:02d}", f"{plat_ing_siva:.2f}", f"{plat_iva_tras:.2f}", f"{plat_iva_ret:.2f}", f"{plat_isr_ret:.2f}",
                    f"{ingresos_total:.2f}", f"{ingresos_trasl:.2f}", f"{gastos_total:.2f}", f"{gastos_trasl:.2f}",
                    f"{iva_causado:.2f}", f"{iva_acreditable:.2f}", f"{plat_iva_ret:.2f}", f"{iva_neto:.2f}"])

        return Response(
            content=out.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=sat_report_{year}_{month:02d}.csv"},
        )
    finally:
        db.close()
