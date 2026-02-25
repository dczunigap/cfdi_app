from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.adapters.inbound.http.api.v1.routes.utils import csv_response, text_response
from app.adapters.inbound.http.deps import get_db, get_required_rfc
from app.adapters.outbound.db.period_data import compute_period_data
from app.application.reportes.periodo import build_hoja_sat_text
from app.application.reportes.service import build_sat_report_csv
from app.utils.money import format_money

router = APIRouter()


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
    csv_content = build_sat_report_csv(data, year, month, income_source)

    return csv_response(
        csv_content,
        filename=f"sat_report_{year}_{month:02d}.csv",
    )
