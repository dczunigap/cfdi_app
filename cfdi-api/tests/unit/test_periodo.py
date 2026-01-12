from app.application.reportes import periodo


def test_calc_income_and_iva_sources_auto_prefers_plataforma():
    data = {
        "plat_ing_siva": 100.0,
        "plat_iva_tras": 16.0,
        "ingresos_base": 200.0,
        "ingresos_trasl": 32.0,
    }
    ingresos, iva, source = periodo.calc_income_and_iva_sources(data, "auto")
    assert ingresos == 100.0
    assert iva == 16.0
    assert source == "plataforma"


def test_calc_income_and_iva_sources_auto_falls_back_cfdi():
    data = {
        "plat_ing_siva": 0.0,
        "plat_iva_tras": 0.0,
        "ingresos_base": 200.0,
        "ingresos_trasl": 32.0,
    }
    ingresos, iva, source = periodo.calc_income_and_iva_sources(data, "auto")
    assert ingresos == 200.0
    assert iva == 32.0
    assert source == "cfdi"


def test_build_hoja_sat_text_formats_values():
    data = {
        "plat_ing_siva": 100.0,
        "plat_iva_tras": 16.0,
        "plat_isr_ret": 4.0,
        "plat_iva_ret": 2.0,
        "gastos_trasl": 3.0,
    }

    def fmt_money(value: float) -> str:
        return f"{value:.2f}"

    text, effective = periodo.build_hoja_sat_text(2025, 1, "plataforma", data, fmt_money)
    assert "PERIODO: 2025-01" in text
    assert "FUENTE_INGRESOS: PLATAFORMA" in text
    assert "100.00" in text
    assert effective == "plataforma"
