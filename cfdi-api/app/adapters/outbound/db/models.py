from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, Numeric, String, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapters.outbound.db.session import Base


class FacturaModel(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    version: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tipo_comprobante: Mapped[str | None] = mapped_column(String(5), index=True, nullable=True)
    fecha_emision: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    year_emision: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    month_emision: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
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

    conceptos: Mapped[list["ConceptoModel"]] = relationship(
        back_populates="factura",
        cascade="all, delete-orphan",
    )
    pagos: Mapped[list["PagoModel"]] = relationship(
        back_populates="factura",
        cascade="all, delete-orphan",
    )


class ConceptoModel(Base):
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

    factura: Mapped["FacturaModel"] = relationship(back_populates="conceptos")


class PagoModel(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"), index=True)
    fecha_pago: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    year_pago: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    month_pago: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    monto: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    moneda_p: Mapped[str | None] = mapped_column(String(10), nullable=True)
    forma_pago_p: Mapped[str | None] = mapped_column(String(10), nullable=True)

    factura: Mapped["FacturaModel"] = relationship(back_populates="pagos")


class RetencionModel(Base):
    __tablename__ = "retenciones_plataforma"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    version: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fecha_exp: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    ejercicio: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    mes_ini: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    mes_fin: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    emisor_rfc: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    emisor_nombre: Mapped[str | None] = mapped_column(String(300), nullable=True)
    receptor_rfc: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    receptor_nombre: Mapped[str | None] = mapped_column(String(300), nullable=True)
    monto_tot_operacion: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    monto_tot_grav: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    monto_tot_exent: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    monto_tot_ret: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    periodicidad: Mapped[str | None] = mapped_column(String(10), nullable=True)
    num_serv: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mon_tot_serv_siva: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    total_iva_trasladado: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    total_iva_retenido: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    total_isr_retenido: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    dif_iva_entregado_prest_serv: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    mon_total_por_uso_plataforma: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    xml_text: Mapped[str] = mapped_column(Text, nullable=False)


class PlatformRfcModel(Base):
    __tablename__ = "platform_rfcs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfc: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    nombre: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class DeclaracionModel(Base):
    __tablename__ = "declaraciones_pdf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int] = mapped_column(Integer, index=True)
    rfc: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    folio: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    fecha_presentacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    filename: Mapped[str] = mapped_column(String(260))
    original_name: Mapped[str | None] = mapped_column(String(260), nullable=True)
    num_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class SatCredentialModel(Base):
    __tablename__ = "sat_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfc: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    pfx_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    pfx_password_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SatDescargaModel(Base):
    __tablename__ = "sat_descargas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfc: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo_solicitud: Mapped[str] = mapped_column(String(20), nullable=False)
    anio_filtro: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    mes_filtro: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    id_solicitud: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    codigo_estado: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mensaje_estado: Mapped[str | None] = mapped_column(Text, nullable=True)
    paquetes: Mapped[list[str]] = mapped_column(JSON, default=list)
    link_descarga: Mapped[str | None] = mapped_column(String(500), nullable=True)
    zip_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class RfcPhoneModel(Base):
    __tablename__ = "rfc_phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    rfc: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UserRfcModel(Base):
    __tablename__ = "user_rfcs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    rfc: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ux_user_rfc", "user_id", "rfc", unique=True),
    )
