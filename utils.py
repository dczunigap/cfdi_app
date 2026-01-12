"""Funciones utilitarias centralizadas para la aplicación CFDI."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, date
from typing import Any, Optional


def sha256_bytes(data: bytes) -> str:
    """Calcula el hash SHA256 de bytes."""
    return hashlib.sha256(data).hexdigest()


def safe_pdf_filename(sha: str, original: Optional[str] = None) -> str:
    """Genera un nombre seguro para PDF basado en su hash SHA256."""
    return f"{sha}.pdf"


def json_default_encoder(obj: Any) -> str:
    """Encoder personalizado para json.dumps que maneja datetime y date."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def format_money(value: Optional[float], currency: str = "MXN") -> str:
    """
    Formatea un número como dinero con separadores de miles y 2 decimales.
    
    Args:
        value: Número a formatear
        currency: Código de moneda (default: MXN)
        
    Returns:
        String formateado (ej: "1,234,567.89 MXN")
    """
    if value is None:
        return ""
    try:
        num = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    currency_code = (currency or "MXN").strip() or "MXN"
    return f"{num:,.2f} {currency_code}"


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """
    Parsea un datetime en formato ISO 8601, soportando offsets sin colon (-0600).
    
    Args:
        value: String en formato ISO o con offset
        
    Returns:
        datetime object o None si no puede parsear
    """
    if not value:
        return None
    
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    
    # Soporta offsets tipo -0600 (sin colon)
    try:
        if len(value) >= 5 and value[-5] in ("+", "-") and value[-2:].isdigit() and value[-4:-2].isdigit():
            adjusted = value[:-2] + ":" + value[-2:]
            return datetime.fromisoformat(adjusted)
    except ValueError:
        pass
    
    return None


def parse_percentage_float(value: Optional[str]) -> Optional[float]:
    """
    Parsea un número que puede tener símbolos de dinero, comas, etc.
    
    Args:
        value: String con número (ej: "$1,234.56")
        
    Returns:
        float o None
    """
    if not value:
        return None
    
    cleaned = value.strip().replace("$", "").replace("MXN", "").replace(" ", "")
    try:
        return float(cleaned.replace(",", ""))
    except ValueError:
        return None


def extract_period_parts(period: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """
    Extrae año y mes de un string formato YYYY-MM.
    
    Args:
        period: String como "2025-01"
        
    Returns:
        Tupla (año, mes) o (None, None)
    """
    if not period or "-" not in period:
        return None, None
    
    try:
        parts = period.split("-")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None, None


def build_period_string(year: Optional[int], month: Optional[int]) -> Optional[str]:
    """
    Construye un string de periodo YYYY-MM desde año y mes.
    
    Args:
        year: Año
        month: Mes (1-12)
        
    Returns:
        String "YYYY-MM" o None
    """
    if year is None or month is None:
        return None
    
    try:
        return f"{int(year)}-{int(month):02d}"
    except (ValueError, TypeError):
        return None


def apply_sign_factor(value: Optional[float], document_type: Optional[str]) -> float:
    """
    Aplica factor de signo: documentos tipo 'E' (egreso) multiplican por -1.
    
    Args:
        value: Valor a modificar
        document_type: Tipo de comprobante (I/E/P/etc)
        
    Returns:
        float con signo aplicado
    """
    if value is None:
        return 0.0
    
    factor = -1.0 if (document_type or "").upper() == "E" else 1.0
    return float(value) * factor


def is_valid_rfc(rfc: Optional[str]) -> bool:
    """
    Valida formato básico de RFC mexicano.
    
    Args:
        rfc: String con RFC
        
    Returns:
        True si tiene formato válido
    """
    if not rfc:
        return False
    
    rfc = rfc.strip().upper()
    # RFC debe tener 12 o 13 caracteres (3-4 letras + 6 números + 3 alfanuméricos + opcional homoclave)
    return len(rfc) in (12, 13) and (rfc[:3].isalpha() or rfc[:4].isalpha())


def serialize_to_json(obj: Any, ensure_ascii: bool = False, indent: Optional[int] = 2) -> str:
    """
    Serializa un objeto a JSON con manejo especial de datetime.
    
    Args:
        obj: Objeto a serializar
        ensure_ascii: Si False, permite caracteres no-ASCII
        indent: Espacios de indentación
        
    Returns:
        String JSON
    """
    return json.dumps(obj, ensure_ascii=ensure_ascii, indent=indent, default=json_default_encoder)


def parse_json_safely(text: Optional[str], default: Optional[dict] = None) -> dict[str, Any]:
    """
    Parsea JSON de forma segura con fallback a default.
    
    Args:
        text: String JSON
        default: Diccionario por defecto si falla
        
    Returns:
        Diccionario parseado o default
    """
    if not text:
        return default or {}
    
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def normalize_rfc(rfc: Optional[str]) -> Optional[str]:
    """
    Normaliza RFC a mayúsculas sin espacios.
    
    Args:
        rfc: RFC a normalizar
        
    Returns:
        RFC normalizado o None
    """
    if not rfc:
        return None
    
    return rfc.strip().upper()
