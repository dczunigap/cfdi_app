def normalize_sat_kind(kind: str) -> str:
    return (kind or "").strip().lower()


def is_retenciones_kind(kind: str) -> bool:
    return normalize_sat_kind(kind) in {"retenciones", "retencion", "ret"}
