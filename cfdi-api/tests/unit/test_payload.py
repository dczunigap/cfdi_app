from datetime import datetime

from app.application.declaraciones.payload import build_declaracion_payload
from app.domain.declaraciones.entities import DeclaracionPDF


def test_build_declaracion_payload_fills_defaults():
    dec = DeclaracionPDF(
        year=2025,
        month=1,
        rfc="AAA010101AAA",
        folio="F-123",
        fecha_presentacion=datetime(2025, 1, 15),
        sha256="hash",
        filename="file.pdf",
        original_name="orig.pdf",
        num_pages=2,
        text_excerpt="",
    )

    def parse_summary(_text: str) -> dict:
        return {}

    payload = build_declaracion_payload(dec, parse_summary)
    assert payload["periodo"] == "2025-01"
    assert payload["rfc"] == "AAA010101AAA"
    assert payload["archivo"] == "orig.pdf"
    assert payload["sha256"] == "hash"
