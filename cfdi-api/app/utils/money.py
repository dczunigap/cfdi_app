from __future__ import annotations

from typing import Optional


def format_money(value: Optional[float], currency: str = "MXN") -> str:
    if value is None:
        return ""
    try:
        num = float(value)
    except (ValueError, TypeError):
        return str(value)

    code = (currency or "MXN").strip() or "MXN"
    return f"{num:,.2f} {code}"


def apply_sign_factor(value: Optional[float], document_type: Optional[str]) -> float:
    if value is None:
        return 0.0
    factor = -1.0 if (document_type or "").upper() == "E" else 1.0
    return float(value) * factor
