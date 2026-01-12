from __future__ import annotations

from typing import Optional

from app.domain.declaraciones.entities import DeclaracionPDF


def build_declaracion_payload(dec: DeclaracionPDF, parse_summary) -> dict:
    try:
        parsed = parse_summary(dec.text_excerpt or "")
    except Exception:
        parsed = {}

    def to_iso(v) -> Optional[str]:
        try:
            return v.isoformat() if v else None
        except Exception:
            return None

    return {
        "periodo": (parsed.get("periodo") if isinstance(parsed, dict) else None)
        or f"{dec.year}-{dec.month:02d}",
        "rfc": (parsed.get("rfc") if isinstance(parsed, dict) else None) or dec.rfc,
        "nombre": (parsed.get("nombre") if isinstance(parsed, dict) else None),
        "tipo_declaracion": (parsed.get("tipo_declaracion") if isinstance(parsed, dict) else None),
        "periodo_mes": (parsed.get("periodo_mes") if isinstance(parsed, dict) else None),
        "ejercicio": (parsed.get("ejercicio") if isinstance(parsed, dict) else None),
        "numero_operacion": (parsed.get("numero_operacion") if isinstance(parsed, dict) else None)
        or (dec.folio or None),
        "fecha_presentacion": to_iso(dec.fecha_presentacion)
        or to_iso(parsed.get("fecha_presentacion") if isinstance(parsed, dict) else None),
        "linea_captura": (parsed.get("linea_captura") if isinstance(parsed, dict) else None),
        "secciones": (parsed.get("secciones") if isinstance(parsed, dict) else None) or [],
        "isr": (parsed.get("isr") if isinstance(parsed, dict) else None),
        "iva": (parsed.get("iva") if isinstance(parsed, dict) else None),
        "ingresos_totales_mes": (parsed.get("ingresos_totales_mes") if isinstance(parsed, dict) else None),
        "isr_causado": (parsed.get("isr_causado") if isinstance(parsed, dict) else None),
        "retenciones_plataformas": (parsed.get("retenciones_plataformas") if isinstance(parsed, dict) else None),
        "iva_tasa": (parsed.get("iva_tasa") if isinstance(parsed, dict) else None),
        "iva_a_cargo_16": (parsed.get("iva_a_cargo_16") if isinstance(parsed, dict) else None),
        "iva_acreditable": (parsed.get("iva_acreditable") if isinstance(parsed, dict) else None),
        "iva_retenido": (parsed.get("iva_retenido") if isinstance(parsed, dict) else None),
        "num_pages": dec.num_pages,
        "archivo": dec.original_name or dec.filename,
        "sha256": dec.sha256,
        "tiene_texto_extraible": bool((dec.text_excerpt or "").strip()),
    }
