from __future__ import annotations

from typing import Optional


def calc_income_and_iva_sources(
    data: dict, income_source: Optional[str]
) -> tuple[float, float, str]:
    income_source = (income_source or "auto").lower().strip()

    plat_income = float(data.get("plat_ing_siva") or 0.0)
    cfdi_income = float(data.get("ingresos_base") or 0.0)

    plat_iva_tras = float(data.get("plat_iva_tras") or 0.0)
    cfdi_iva_tras = float(data.get("ingresos_trasl") or 0.0)

    if income_source == "plataforma":
        return plat_income, plat_iva_tras, "plataforma"
    if income_source == "cfdi":
        return cfdi_income, cfdi_iva_tras, "cfdi"
    if income_source == "ambos":
        return plat_income + cfdi_income, plat_iva_tras + cfdi_iva_tras, "ambos"

    if plat_income > 0 or plat_iva_tras > 0:
        return plat_income, plat_iva_tras, "plataforma"
    return cfdi_income, cfdi_iva_tras, "cfdi"


def build_hoja_sat_text(
    year: int, month: int, income_source: Optional[str], data: dict, fmt_money
) -> tuple[str, str]:
    ingresos_sin_iva, iva_trasladado, effective = calc_income_and_iva_sources(
        data, income_source
    )

    isr_retenido = float(data.get("plat_isr_ret") or 0.0)
    iva_retenido = float(data.get("plat_iva_ret") or 0.0)
    iva_acreditable = float(data.get("gastos_trasl") or 0.0)

    iva_neto_sugerido = iva_trasladado - iva_acreditable - iva_retenido

    def fmt(x: float) -> str:
        return fmt_money(x)

    text = "\n".join(
        [
            f"PERIODO: {year}-{month:02d}",
            f"FUENTE_INGRESOS: {effective.upper()} (selector: {income_source})",
            "",
            "ISR (Pago provisional)",
            f"- Ingresos del periodo (sin IVA): {fmt(ingresos_sin_iva)}",
            f"- ISR retenido (plataforma): {fmt(isr_retenido)}",
            "",
            "IVA (Mensual)",
            f"- IVA trasladado del periodo: {fmt(iva_trasladado)}",
            f"- IVA retenido (plataforma): {fmt(iva_retenido)}",
            f"- IVA acreditable (gastos CFDI): {fmt(iva_acreditable)}",
            "",
            "CONTROLES",
            f"- IVA neto sugerido: {fmt(iva_neto_sugerido)}",
            "",
            "NOTAS",
            "- Si CFDI de ingreso = mismas ventas de plataforma, evita sumarlas.",
        ]
    )
    return text, effective


def build_checklist(
    data: dict,
    mi_rfc: str,
    income_source: str,
    effective_income_source: str,
) -> list[dict]:
    checks: list[dict] = []
    ret_rows = data.get("ret_rows") or []
    docs = data.get("docs") or []

    if not ret_rows:
        checks.append(
            {
                "level": "error",
                "title": "Falta XML de retenciones de plataformas",
                "detail": "Sin este XML, no podras acreditar ISR/IVA retenido.",
            }
        )
    else:
        checks.append(
            {
                "level": "ok",
                "title": "Retenciones de plataformas encontradas",
                "detail": f"Se detectaron {len(ret_rows)} XML(s) de retenciones.",
            }
        )

    if ret_rows:
        receivers = sorted(
            {
                (getattr(r, "receptor_rfc", "") or "").upper()
                for r in ret_rows
                if getattr(r, "receptor_rfc", None)
            }
        )
        if receivers and (mi_rfc or "").upper() not in receivers:
            checks.append(
                {
                    "level": "warn",
                    "title": "RFC receptor no coincide",
                    "detail": f"Receptores en XML: {', '.join(receivers)}",
                }
            )
        else:
            checks.append(
                {
                    "level": "ok",
                    "title": "RFC receptor coincide",
                    "detail": "El RFC del receptor coincide con tu configuracion.",
                }
            )

    bad_ranges = [
        r for r in ret_rows if (getattr(r, "mes_ini", 0) or 0) != (getattr(r, "mes_fin", 0) or 0)
    ]
    if bad_ranges:
        checks.append(
            {
                "level": "warn",
                "title": "Retencion con rango de meses",
                "detail": "Hay XML donde MesIni != MesFin.",
            }
        )

    missing_uso = [
        d
        for d in docs
        if getattr(d, "naturaleza", None) == "gasto"
        and not (getattr(d, "uso_cfdi", "") or "").strip()
        and (getattr(d, "tipo_comprobante", "") or "").upper() != "P"
    ]
    if missing_uso:
        checks.append(
            {
                "level": "warn",
                "title": f"Hay {len(missing_uso)} gastos sin UsoCFDI",
                "detail": "Revisa esos XML para completar el campo.",
            }
        )
    else:
        checks.append(
            {
                "level": "ok",
                "title": "UsoCFDI en gastos",
                "detail": "Tus CFDI de gastos traen UsoCFDI o no hay gastos.",
            }
        )

    gastos_count = sum(
        1
        for d in docs
        if getattr(d, "naturaleza", None) == "gasto"
        and (getattr(d, "tipo_comprobante", "") or "").upper() != "P"
    )
    if gastos_count == 0:
        checks.append(
            {
                "level": "warn",
                "title": "No hay CFDI de gastos",
                "detail": "Sin gastos no podras acreditar IVA ni deducirlos.",
            }
        )

    ingresos_count = sum(
        1
        for d in docs
        if getattr(d, "naturaleza", None) == "ingreso"
        and (getattr(d, "tipo_comprobante", "") or "").upper() != "P"
    )
    if ret_rows and ingresos_count > 0 and float(data.get("ingresos_base") or 0.0) > 0.0:
        if effective_income_source in ["plataforma", "cfdi"]:
            checks.append(
                {
                    "level": "info",
                    "title": "Doble fuente detectada",
                    "detail": f"Usando: {effective_income_source.upper()}",
                }
            )

    p_no_pagos = [
        d
        for d in docs
        if (getattr(d, "tipo_comprobante", "") or "").upper() == "P"
        and len(getattr(d, "pagos", []) or []) == 0
    ]
    if p_no_pagos:
        checks.append(
            {
                "level": "warn",
                "title": f"{len(p_no_pagos)} CFDI tipo P sin renglones <Pago>",
                "detail": "Puede ser XML incompleto o namespace distinto.",
            }
        )

    other_cur = sorted(
        {
            (getattr(d, "moneda", "") or "").upper()
            for d in docs
            if getattr(d, "moneda", None) and (getattr(d, "moneda", "") or "").upper() != "MXN"
        }
    )
    if other_cur:
        checks.append(
            {
                "level": "info",
                "title": f"Moneda distinta: {', '.join(other_cur)}",
                "detail": "Debes convertir a MXN con tipo de cambio.",
            }
        )

    _ = income_source
    return checks
