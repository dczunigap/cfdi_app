from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.outbound.db.models import FacturaModel
from app.adapters.outbound.db.period_data import compute_period_data
from app.adapters.outbound.db.session import Base


RFC = "AAA010101AAA"


def _factura(
    *,
    year: int,
    month: int,
    emisor_rfc: str,
    receptor_rfc: str,
    uso_cfdi: str,
    naturaleza: str,
    subtotal: float,
    total: float,
    total_trasladados: float,
) -> FacturaModel:
    return FacturaModel(
        year_emision=year,
        month_emision=month,
        tipo_comprobante="I",
        naturaleza=naturaleza,
        emisor_rfc=emisor_rfc,
        receptor_rfc=receptor_rfc,
        uso_cfdi=uso_cfdi,
        subtotal=subtotal,
        descuento=0.0,
        total=total,
        total_trasladados=total_trasladados,
        total_retenidos=0.0,
        xml_text="<xml/>",
    )


def _session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    return SessionLocal()


def test_compute_period_data_keeps_ingresos_with_mi_rfc_even_if_uso_not_in_allowlist():
    with _session() as db:
        db.add(
            _factura(
                year=2025,
                month=1,
                emisor_rfc=RFC,
                receptor_rfc="XAXX010101000",
                uso_cfdi="P01",
                naturaleza="ingreso",
                subtotal=100.0,
                total=116.0,
                total_trasladados=16.0,
            )
        )
        db.commit()

        data = compute_period_data(
            db,
            2025,
            1,
            mi_rfc=RFC,
            gasto_uso_cfdi_allowlist={"G03"},
        )

        assert data["ingresos_base"] == 100.0
        assert data["ingresos_total"] == 116.0
        assert data["ingresos_trasl"] == 16.0


def test_compute_period_data_applies_default_gasto_filter_without_allowlist():
    with _session() as db:
        db.add_all(
            [
                _factura(
                    year=2025,
                    month=1,
                    emisor_rfc="XEXX010101000",
                    receptor_rfc=RFC,
                    uso_cfdi="G03",
                    naturaleza="gasto",
                    subtotal=100.0,
                    total=116.0,
                    total_trasladados=16.0,
                ),
                _factura(
                    year=2025,
                    month=1,
                    emisor_rfc="XEXX010101000",
                    receptor_rfc=RFC,
                    uso_cfdi="S01",
                    naturaleza="gasto",
                    subtotal=50.0,
                    total=58.0,
                    total_trasladados=8.0,
                ),
            ]
        )
        db.commit()

        data = compute_period_data(db, 2025, 1, mi_rfc=RFC)

        assert data["gastos_total"] == 116.0
        assert data["gastos_trasl"] == 16.0
