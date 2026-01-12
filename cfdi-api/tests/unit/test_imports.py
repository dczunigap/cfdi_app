from app.application.imports.facturas import create_factura_from_parsed


def test_create_factura_from_parsed_maps_conceptos_y_pagos():
    parsed = {
        "uuid": "abc",
        "conceptos": [
            {
                "clave_prod_serv": "101",
                "cantidad": 2.0,
                "descripcion": "Servicio",
                "importe": 200.0,
            }
        ],
        "pagos": [
            {
                "monto": 150.0,
                "moneda_p": "MXN",
            }
        ],
    }

    factura = create_factura_from_parsed(parsed)

    assert factura.uuid == "abc"
    assert len(factura.conceptos) == 1
    assert factura.conceptos[0].descripcion == "Servicio"
    assert len(factura.pagos) == 1
    assert factura.pagos[0].monto == 150.0
