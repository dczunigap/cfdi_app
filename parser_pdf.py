from __future__ import annotations

from datetime import datetime
import re
from typing import Any
import unicodedata

from pypdf import PdfReader


SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

HDR = "DECLARACIÓN PROVISIONAL O DEFINITIVA DE IMPUESTOS FEDERALES"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def _parse_amount(raw: str | None) -> float | None:
    if not raw:
        return None
    s = raw.strip().replace("$", "").replace("MXN", "").replace(" ", "")
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None


def extract_pdf_text(pdf_path: str, max_chars: int = 20000) -> tuple[str, int]:
    """Extrae texto de PDF usando pypdf (si el PDF tiene texto embebido).
    Devuelve (texto, num_paginas). Si es escaneo, el texto puede salir vacío.
    """
    reader = PdfReader(pdf_path)
    pages = reader.pages
    num_pages = len(pages)
    chunks: list[str] = []
    total = 0
    for p in pages:
        try:
            t = p.extract_text() or ""
        except Exception:
            t = ""
        if not t.strip():
            continue
        if total + len(t) > max_chars:
            t = t[: max_chars - total]
        chunks.append(t)
        total += len(t)
        if total >= max_chars:
            break
    return ("\n".join(chunks)).strip(), num_pages


def _parse_period_line(line: str) -> tuple[str | None, int | None, str | None]:
    # "Período de la declaración: Noviembre Ejercicio: 2025"
    m = re.search(
        r"Per[ií]odo\s*de\s*la\s*declaraci[oó]n\s*:\s*([A-Za-zÁÉÍÓÚÑáéíóúñ]+)\s+Ejercicio\s*:\s*(\d{4})",
        line,
        flags=re.IGNORECASE,
    )
    if not m:
        return None, None, None
    mes_name = m.group(1)
    year = int(m.group(2))
    mn = SPANISH_MONTHS.get(_norm(mes_name).lower())
    periodo = f"{year}-{mn:02d}" if mn else None
    return mes_name, year, periodo


def _split_sections(raw: str) -> list[str]:
    # Parte el texto por el encabezado HDR.
    # En muchos acuses, los importes (CANTIDAD A PAGAR, TOTAL DE CONTRIBUCIONES, etc.)
    # aparecen justo ANTES del encabezado. Por eso incluimos un "lookback" buscando
    # la última ocurrencia de "CANTIDAD A PAGAR" previa al HDR dentro de una ventana.
    idxs = [m.start() for m in re.finditer(re.escape(HDR), raw)]
    if not idxs:
        return []
    sections: list[str] = []
    for i, hdr_start in enumerate(idxs):
        end = idxs[i + 1] if i + 1 < len(idxs) else len(raw)

        # lookback de hasta ~2500 chars para enganchar importes
        start = hdr_start
        cap = raw.rfind("CANTIDAD A PAGAR", max(0, hdr_start - 2500), hdr_start)
        if cap != -1:
            # un pequeño margen para capturar "TOTAL DE CONTRIBUCIONES" que suele ir arriba
            start = max(0, cap - 250)

        sections.append(raw[start:end].strip())
    return sections



def parse_sat_declaracion_summary(text: str) -> dict[str, Any]:
    """Extrae un resumen estructurado de un PDF/acuse de declaración SAT.

    Este acuse suele contener varias secciones (p.ej. ISR e IVA), cada una con:
      - Encabezado HDR
      - Línea del impuesto (ej. "ISR PERSONAS FÍSICAS PLATAFORMAS TECNOLÓGICAS")
      - RFC / Nombre / Tipo / Periodo / Número operación / Fecha presentación
      - Importes: CANTIDAD A PAGAR / TOTAL DE CONTRIBUCIONES / etc.

    Regresa:
      - campos generales (RFC/periodo/operación/fecha)
      - secciones: lista con un objeto por impuesto
      - atajos: isr / iva (si se detectan)
    """
    raw = (text or "").strip()

    out: dict[str, Any] = {
        "rfc": None,
        "nombre": None,
        "tipo_declaracion": None,
        "periodo_mes": None,
        "ejercicio": None,
        "periodo": None,  # YYYY-MM
        "numero_operacion": None,
        "fecha_presentacion": None,  # datetime
        "linea_captura": None,
        "secciones": [],
    }

    # Split into sections
    sections = _split_sections(raw)
    if not sections:
        # fallback: use whole text as one section
        sections = [raw]

    parsed_sections: list[dict[str, Any]] = []

    for sec in sections:
        lines = [ln.strip() for ln in sec.splitlines() if ln.strip()]
        if not lines:
            continue

        sec_obj: dict[str, Any] = {
            "impuesto": None,
            "rfc": None,
            "nombre": None,
            "tipo_declaracion": None,
            "periodo_mes": None,
            "ejercicio": None,
            "periodo": None,
            "numero_operacion": None,
            "fecha_presentacion": None,
            "linea_captura": None,
            "cantidad_a_pagar": None,
            "cantidad_a_cargo": None,
            "total_contribuciones": None,
        }

        # impuesto = primera línea después del HDR
        try:
            hdr_i = lines.index(HDR)
        except ValueError:
            hdr_i = 0
        # Busca la primera línea "en mayúsculas" después del hdr
        for j in range(hdr_i + 1, min(hdr_i + 6, len(lines))):
            cand = lines[j]
            if cand.upper() == cand and len(cand) >= 5 and "RFC" not in _norm(cand).upper():
                sec_obj["impuesto"] = cand
                break
        if sec_obj["impuesto"] is None and hdr_i + 1 < len(lines):
            sec_obj["impuesto"] = lines[hdr_i + 1]

        for ln in lines:
            nln = _norm(ln)
            if nln.upper().startswith("RFC:"):
                m = re.search(r"RFC:\s*([A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3})", nln, flags=re.IGNORECASE)
                if m:
                    sec_obj["rfc"] = m.group(1).upper()

            if nln.upper().startswith("NOMBRE:"):
                sec_obj["nombre"] = ln.split(":", 1)[1].strip() if ":" in ln else ln

            if "Tipo de declaración" in ln or "Tipo de declaracion" in nln:
                m = re.search(r"Tipo\s*de\s*declaraci[oó]n\s*:\s*(.+)", ln, flags=re.IGNORECASE)
                if m:
                    sec_obj["tipo_declaracion"] = m.group(1).strip()

            if "Período de la declaración" in ln or "Periodo de la declaracion" in nln:
                mes, year, periodo = _parse_period_line(ln)
                sec_obj["periodo_mes"] = mes
                sec_obj["ejercicio"] = year
                sec_obj["periodo"] = periodo

            if "Número de operación" in ln or "Numero de operacion" in nln:
                m = re.search(r"N[uú]mero\s*de\s*operaci[oó]n\s*:\s*(\d{6,})", ln, flags=re.IGNORECASE)
                if m:
                    sec_obj["numero_operacion"] = m.group(1)

                m = re.search(
                    r"Fecha\s*(?:y\s*hora\s*)?de\s*presentaci[oó]n\s*:\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})",
                    ln,
                    flags=re.IGNORECASE,
                )
                if m:
                    d, hm = m.group(1), m.group(2)
                    try:
                        sec_obj["fecha_presentacion"] = datetime.strptime(f"{d} {hm}", "%d/%m/%Y %H:%M")
                    except Exception:
                        pass

            if "Línea de captura" in ln or "Linea de captura" in nln:
                m = re.search(r"(?:L[ií]nea\s*de\s*captura)\s*:?\s*([0-9]{18,30})", ln, flags=re.IGNORECASE)
                if m:
                    sec_obj["linea_captura"] = m.group(1)

            # Importes (aparecen como "CANTIDAD A PAGAR 0" sin :)
            if nln.upper().startswith("CANTIDAD A PAGAR"):
                m = re.search(r"CANTIDAD\s+A\s+PAGAR\s*:?\s*\$?\s*(.+)$", ln, flags=re.IGNORECASE)
                if m:
                    sec_obj["cantidad_a_pagar"] = _parse_amount(m.group(1))

            if nln.upper().startswith("CANTIDAD A CARGO"):
                m = re.search(r"CANTIDAD\s+A\s+CARGO\s*:?\s*\$?\s*(.+)$", ln, flags=re.IGNORECASE)
                if m:
                    sec_obj["cantidad_a_cargo"] = _parse_amount(m.group(1))

            if nln.upper().startswith("TOTAL DE CONTRIBUCIONES"):
                m = re.search(r"TOTAL\s+DE\s+CONTRIBUCIONES\s*:?\s*\$?\s*(.+)$", ln, flags=re.IGNORECASE)
                if m:
                    sec_obj["total_contribuciones"] = _parse_amount(m.group(1))

        # Deduce "general" if not present
        parsed_sections.append(sec_obj)

    # Deduplicate repeated sections (mismo impuesto + mismo número de operación)
    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for s in parsed_sections:
        key = ((s.get("impuesto") or ""), (s.get("numero_operacion") or ""))
        if key in dedup:
            # prefer one with more info (e.g. has amounts)
            old = dedup[key]
            score_old = sum(1 for k in old.values() if k not in (None, "", []))
            score_new = sum(1 for k in s.values() if k not in (None, "", []))
            if score_new > score_old:
                dedup[key] = s
        else:
            dedup[key] = s

    out["secciones"] = list(dedup.values())

    # Choose "principal" as the last section in the PDF (often IVA is last)
    principal = out["secciones"][-1] if out["secciones"] else None

    # Fill general fields from principal (fallback from any)
    def pick(field: str):
        if principal and principal.get(field) not in (None, ""):
            return principal.get(field)
        for s in out["secciones"]:
            if s.get(field) not in (None, ""):
                return s.get(field)
        return None

    out["rfc"] = pick("rfc")
    out["nombre"] = pick("nombre")
    out["tipo_declaracion"] = pick("tipo_declaracion")
    out["periodo_mes"] = pick("periodo_mes")
    out["ejercicio"] = pick("ejercicio")
    out["periodo"] = pick("periodo")
    out["numero_operacion"] = pick("numero_operacion")
    out["fecha_presentacion"] = pick("fecha_presentacion")
    out["linea_captura"] = pick("linea_captura")

    # Shortcuts: isr / iva
    def first_by_prefix(prefix: str) -> dict[str, Any] | None:
        p = _norm(prefix).upper()
        for s in out["secciones"]:
            imp = _norm(str(s.get("impuesto") or "")).upper()
            if imp.startswith(p):
                return s
        return None

    out["isr"] = first_by_prefix("ISR")
    out["iva"] = first_by_prefix("IVA")

    return out
