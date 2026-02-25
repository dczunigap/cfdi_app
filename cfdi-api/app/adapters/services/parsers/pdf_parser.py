from __future__ import annotations

from .parser_pdf import (
    extract_pdf_text,
    extract_pdf_text_bytes,
    parse_sat_declaracion_summary,
)


class LocalPdfParser:
    def extract_text(self, path: str) -> tuple[str, int | None]:
        return extract_pdf_text(path)

    def extract_text_bytes(self, pdf_bytes: bytes) -> tuple[str, int | None]:
        return extract_pdf_text_bytes(pdf_bytes)

    def parse_sat_summary(self, text: str) -> dict:
        return parse_sat_declaracion_summary(text)
