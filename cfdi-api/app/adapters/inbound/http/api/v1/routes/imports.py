from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db.repositories.declaraciones import SqlDeclaracionRepository
from app.adapters.outbound.db.repositories.facturas import SqlFacturaRepository
from app.adapters.outbound.db.repositories.retenciones import SqlRetencionRepository
from app.adapters.outbound.files.pdf_storage import LocalPdfStorage
from app.adapters.services.parsers.pdf_parser import LocalPdfParser
from app.adapters.services.parsers.xml_parser import LocalXmlParser
from app.application.imports.facturas import (
    create_factura_from_parsed,
    create_retencion_from_parsed,
)
from app.domain.declaraciones.entities import DeclaracionPDF
from app.utils.files import safe_pdf_filename, sha256_bytes

router = APIRouter(tags=["import"])


@router.post("/importar")
async def importar_xml(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    stats = {
        "cfdi_insertados": 0,
        "cfdi_duplicados": 0,
        "retenciones_insertadas": 0,
        "retenciones_duplicadas": 0,
        "errores": 0,
    }

    factura_repo = SqlFacturaRepository(db)
    ret_repo = SqlRetencionRepository(db)
    parser = LocalXmlParser()

    for file in files:
        try:
            xml_bytes = await file.read()
            kind = parser.detect_kind(xml_bytes)

            if kind == "cfdi":
                parsed = parser.parse_cfdi(xml_bytes)
                uuid = parsed.get("uuid")
                if uuid and factura_repo.exists_uuid(uuid):
                    stats["cfdi_duplicados"] += 1
                    continue
                parsed["xml_text"] = xml_bytes.decode("utf-8", errors="replace")
                factura = create_factura_from_parsed(parsed)
                factura_repo.add_factura(factura)
                stats["cfdi_insertados"] += 1
            elif kind == "retenciones":
                parsed = parser.parse_retenciones(xml_bytes)
                uuid = parsed.get("uuid")
                if uuid and ret_repo.exists_uuid(uuid):
                    stats["retenciones_duplicadas"] += 1
                    continue
                parsed["xml_text"] = xml_bytes.decode("utf-8", errors="replace")
                retencion = create_retencion_from_parsed(parsed)
                ret_repo.add_retencion(retencion)
                stats["retenciones_insertadas"] += 1
            else:
                stats["errores"] += 1
        except Exception:
            db.rollback()
            stats["errores"] += 1

    return stats


@router.post("/importar_pdf")
async def importar_pdf(
    files: list[UploadFile] = File(...),
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
):
    stats = {"insertados": 0, "duplicados": 0, "errores": 0}

    base_dir = Path(__file__).resolve().parents[7]
    storage = LocalPdfStorage(base_dir / "database" / "pdfs")
    parser = LocalPdfParser()
    repo = SqlDeclaracionRepository(db)

    for file in files:
        try:
            pdf_bytes = await file.read()
            sha = sha256_bytes(pdf_bytes)

            if repo.exists_sha256(sha):
                stats["duplicados"] += 1
                continue

            filename = safe_pdf_filename(sha, getattr(file, "filename", None))
            storage.save(filename, pdf_bytes)

            try:
                text, num_pages = parser.extract_text(
                    str(base_dir / "database" / "pdfs" / filename)
                )
            except Exception:
                text, num_pages = "", None

            try:
                summary = parser.parse_sat_summary(text or "")
            except Exception:
                summary = {}

            y, mth = year, month
            per = summary.get("periodo") if isinstance(summary, dict) else None
            if (not y or not mth) and per and "-" in per:
                try:
                    y = int(per.split("-")[0])
                    mth = int(per.split("-")[1])
                except Exception:
                    pass

            if not y or not mth:
                now = datetime.now()
                y = y or now.year
                mth = mth or now.month

            dec = DeclaracionPDF(
                year=int(y),
                month=int(mth),
                rfc=summary.get("rfc") if isinstance(summary, dict) else None,
                folio=summary.get("numero_operacion") if isinstance(summary, dict) else None,
                fecha_presentacion=summary.get("fecha_presentacion")
                if isinstance(summary, dict)
                else None,
                sha256=sha,
                filename=filename,
                original_name=getattr(file, "filename", None),
                num_pages=int(num_pages) if num_pages is not None else None,
                text_excerpt=text[:20000] if text else None,
            )
            repo.add_declaracion(dec)
            stats["insertados"] += 1
        except Exception:
            db.rollback()
            stats["errores"] += 1

    return stats
