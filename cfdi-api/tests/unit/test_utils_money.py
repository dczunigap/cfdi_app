from app.utils.money import apply_sign_factor, format_money


def test_format_money_handles_none():
    assert format_money(None) == ""


def test_format_money_formats_value():
    assert format_money(1234.5) == "1,234.50 MXN"


def test_apply_sign_factor_for_egreso():
    assert apply_sign_factor(10.0, "E") == -10.0


def test_apply_sign_factor_for_ingreso():
    assert apply_sign_factor(10.0, "I") == 10.0
