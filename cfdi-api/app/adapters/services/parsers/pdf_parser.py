from __future__ import annotations

from .parser_pdf import extract_pdf_text, parse_sat_declaracion_summary


class LocalPdfParser:
    def extract_text(self, path: str) -> tuple[str, int | None]:
        return extract_pdf_text(path)

    def parse_sat_summary(self, text: str) -> dict:
        return parse_sat_declaracion_summary(text)
