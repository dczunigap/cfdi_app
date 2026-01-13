from __future__ import annotations

from .parser_xml import detect_xml_kind, parse_cfdi_40, parse_retenciones_plataforma


class LocalXmlParser:
    def detect_kind(self, xml_bytes: bytes) -> str:
        return detect_xml_kind(xml_bytes)

    def parse_cfdi(self, xml_bytes: bytes) -> dict:
        return parse_cfdi_40(xml_bytes)

    def parse_retenciones(self, xml_bytes: bytes) -> dict:
        return parse_retenciones_plataforma(xml_bytes)
