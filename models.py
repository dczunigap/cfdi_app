from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identificación
    uuid: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)

    # CFDI
    version: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tipo_comprobante: Mapped[str | None] = mapped_column(String(5), index=True, nullable=True)  # I, E, P, T, N...
    fecha_emision: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)

    year_emision: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    month_emision: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)

    # Clasificación automática
    # ingreso / gasto / cobro (P emitido) / pago (P recibido) / otro
    naturaleza: Mapped[str | None] = mapped_column(String(12), index=True, nullable=True)

    emisor_rfc: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    emisor_nombre: Mapped[str | None] = mapped_column(String(300), nullable=True)

    receptor_rfc: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    receptor_nombre: Mapped[str | None] = mapped_column(String(300), nullable=True)
    uso_cfdi: Mapped[str | None] = mapped_column(String(10), nullable=True)

    moneda: Mapped[str | None] = mapped_column(String(10), nullable=True)
    metodo_pago: Mapped[str | None] = mapped_column(String(10), nullable=True)
    forma_pago: Mapped[str | None] = mapped_column(String(10), nullable=True)

    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    descuento: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    total: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)

    total_trasladados: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    total_retenidos: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)

    xml_text: Mapped[str] = mapped_column(Text, nullable=False)

    conceptos: Mapped[list["Concepto"]] = relationship(
        back_populates="factura",
        cascade="all, delete-orphan",
    )

    pagos: Mapped[list["Pago"]] = relationship(
        back_populates="factura",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("uuid", name="uq_facturas_uuid"),
    )


class Concepto(Base):
    __tablename__ = "conceptos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"), index=True)

    clave_prod_serv: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cantidad: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    clave_unidad: Mapped[str | None] = mapped_column(String(10), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    valor_unitario: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    importe: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)

    objeto_imp: Mapped[str | None] = mapped_column(String(5), nullable=True)

    factura: Mapped["Factura"] = relationship(back_populates="conceptos")


class Pago(Base):
    """Renglones del Complemento de Pagos (TipoDeComprobante='P')"""

    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"), index=True)

    fecha_pago: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    year_pago: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    month_pago: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)

    monto: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    moneda_p: Mapped[str | None] = mapped_column(String(10), nullable=True)
    forma_pago_p: Mapped[str | None] = mapped_column(String(10), nullable=True)

    factura: Mapped["Factura"] = relationship(back_populates="pagos")
