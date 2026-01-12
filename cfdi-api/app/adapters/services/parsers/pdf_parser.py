from __future__ import annotations

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[5]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from parser_pdf import extract_pdf_text, parse_sat_declaracion_summary


class LocalPdfParser:
    def extract_text(self, path: str) -> tuple[str, int | None]:
        return extract_pdf_text(path)

    def parse_sat_summary(self, text: str) -> dict:
        return parse_sat_declaracion_summary(text)
