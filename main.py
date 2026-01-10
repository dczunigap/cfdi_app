from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from db import engine, SessionLocal
from models import Base, Factura, Concepto, Pago
from parser_cfdi import parse_cfdi_40

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

    db = get_db()
    try:
        for f in files:
            try:
                xml_bytes = await f.read()
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

            except Exception:
                db.rollback()
                errors += 1

    finally:
        db.close()

    msg = f"Importación: {inserted} insertados, {skipped} duplicados omitidos, {errors} errores."
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


@app.get("/facturas/{factura_id}", response_class=HTMLResponse)
def detalle_factura(request: Request, factura_id: int) -> HTMLResponse:
    db = get_db()
    try:
        factura = db.get(Factura, factura_id)
        if not factura:
            return HTMLResponse("No encontrada", status_code=404)
        # fuerza carga de relaciones
        _ = factura.conceptos
        _ = factura.pagos
        return templates.TemplateResponse("detalle.html", {"request": request, "factura": factura, "mi_rfc": MI_RFC})
    finally:
        db.close()


def _signed(total, tipo: str | None):
    if total is None:
        return 0.0
    return float(total) * (-1.0 if (tipo or "").upper() == "E" else 1.0)


@app.get("/summary", response_class=HTMLResponse)
def resumen_mensual(request: Request, year: int | None = None, month: int | None = None) -> HTMLResponse:
    db = get_db()
    try:
        # Mes/año por defecto: el más reciente en facturas (por emisión)
        if year is None or month is None:
            last = db.execute(
                select(Factura.year_emision, Factura.month_emision)
                .where(Factura.year_emision.isnot(None), Factura.month_emision.isnot(None))
                .order_by(desc(Factura.year_emision), desc(Factura.month_emision))
                .limit(1)
            ).first()
            if last:
                year, month = int(last[0]), int(last[1])

        # Opciones para dropdown
        months = db.execute(
            select(Factura.year_emision, Factura.month_emision)
            .where(Factura.year_emision.isnot(None), Factura.month_emision.isnot(None))
            .group_by(Factura.year_emision, Factura.month_emision)
            .order_by(desc(Factura.year_emision), desc(Factura.month_emision))
        ).all()
        month_options = [(int(y), int(m)) for (y, m) in months if y and m]

        # Resumen por emisión (I/E)
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

        # Resumen de pagos por FechaPago (solo complementos P)
        pagos_rows = db.execute(
            select(Pago, Factura.naturaleza)
            .join(Factura, Pago.factura_id == Factura.id)
            .where(Pago.year_pago == year, Pago.month_pago == month)
            .order_by(desc(Pago.fecha_pago).nullslast(), desc(Pago.id))
        ).all()

        cash_in = 0.0   # cobros (P emitidos por ti)
        cash_out = 0.0  # pagos (P recibidos por ti)
        pagos_count = 0

        for pago, nat in pagos_rows:
            pagos_count += 1
            monto = float(pago.monto or 0.0)
            if nat == "cobro":
                cash_in += monto
            elif nat == "pago":
                cash_out += monto

        return templates.TemplateResponse(
            "summary.html",
            {
                "request": request,
                "mi_rfc": MI_RFC,
                "year": year,
                "month": month,
                "month_options": month_options,
                "ingresos_total": ingresos_total,
                "ingresos_trasl": ingresos_trasl,
                "ingresos_ret": ingresos_ret,
                "gastos_total": gastos_total,
                "gastos_trasl": gastos_trasl,
                "gastos_ret": gastos_ret,
                "p_count": p_count,
                "cash_in": cash_in,
                "cash_out": cash_out,
                "pagos_count": pagos_count,
                "docs": docs[:200],
                "pagos_rows": pagos_rows[:200],
            },
        )
    finally:
        db.close()
