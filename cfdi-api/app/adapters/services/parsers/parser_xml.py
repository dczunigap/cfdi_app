from __future__ import annotations

from datetime import datetime
from xml.etree import ElementTree as ET


def detect_xml_kind(xml_bytes: bytes) -> str:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return "unknown"

    root_name = _localname(root.tag)
    if root_name == "Comprobante":
        return "cfdi"
    if root_name == "Retenciones":
        return "retenciones"
    return "unknown"


def parse_cfdi_40(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)
    comprobante = root

    fecha_emision = _parse_datetime(comprobante.attrib.get("Fecha"))

    emisor = _find_first(comprobante, "Emisor")
    receptor = _find_first(comprobante, "Receptor")

    uuid = None
    tfd = _find_first(comprobante, "TimbreFiscalDigital")
    if tfd is not None:
        uuid = tfd.attrib.get("UUID")

    tipo = comprobante.attrib.get("TipoDeComprobante")

    conceptos = []
    for concepto in _find_all(comprobante, "Concepto"):
        conceptos.append(
            {
                "clave_prod_serv": concepto.attrib.get("ClaveProdServ"),
                "cantidad": _parse_float(concepto.attrib.get("Cantidad")),
                "clave_unidad": concepto.attrib.get("ClaveUnidad"),
                "descripcion": concepto.attrib.get("Descripcion"),
                "valor_unitario": _parse_float(concepto.attrib.get("ValorUnitario")),
                "importe": _parse_float(concepto.attrib.get("Importe")),
                "objeto_imp": concepto.attrib.get("ObjetoImp"),
            }
        )

    pagos = []
    for pago in _find_all(comprobante, "Pago"):
        fecha_pago = _parse_datetime(pago.attrib.get("FechaPago"))
        pagos.append(
            {
                "fecha_pago": fecha_pago,
                "year_pago": fecha_pago.year if fecha_pago else None,
                "month_pago": fecha_pago.month if fecha_pago else None,
                "monto": _parse_float(pago.attrib.get("Monto")),
                "moneda_p": pago.attrib.get("MonedaP"),
                "forma_pago_p": pago.attrib.get("FormaDePagoP"),
            }
        )

    return {
        "uuid": uuid,
        "version": comprobante.attrib.get("Version"),
        "tipo_comprobante": tipo,
        "fecha_emision": fecha_emision,
        "year_emision": fecha_emision.year if fecha_emision else None,
        "month_emision": fecha_emision.month if fecha_emision else None,
        "naturaleza": _map_naturaleza(tipo),
        "emisor_rfc": emisor.attrib.get("Rfc") if emisor is not None else None,
        "emisor_nombre": emisor.attrib.get("Nombre") if emisor is not None else None,
        "receptor_rfc": receptor.attrib.get("Rfc") if receptor is not None else None,
        "receptor_nombre": receptor.attrib.get("Nombre") if receptor is not None else None,
        "uso_cfdi": receptor.attrib.get("UsoCFDI") if receptor is not None else None,
        "moneda": comprobante.attrib.get("Moneda"),
        "metodo_pago": comprobante.attrib.get("MetodoPago"),
        "forma_pago": comprobante.attrib.get("FormaPago"),
        "subtotal": _parse_float(comprobante.attrib.get("SubTotal")),
        "descuento": _parse_float(comprobante.attrib.get("Descuento")),
        "total": _parse_float(comprobante.attrib.get("Total")),
        "total_trasladados": _parse_float(
            comprobante.attrib.get("TotalImpuestosTrasladados")
        ),
        "total_retenidos": _parse_float(
            comprobante.attrib.get("TotalImpuestosRetenidos")
        ),
        "conceptos": conceptos,
        "pagos": pagos,
    }


def parse_retenciones_plataforma(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)

    emisor = _find_first(root, "Emisor")
    receptor = _find_first(root, "Receptor")
    receptor_rfc, receptor_nombre = _parse_retenciones_receptor(receptor)

    totales = _find_first(root, "Totales")
    plataforma = _find_first(root, "PlataformasTecnologicas") or _find_first(
        root, "ServiciosPlataforma"
    )

    uuid = None
    tfd = _find_first(root, "TimbreFiscalDigital")
    if tfd is not None:
        uuid = tfd.attrib.get("UUID")

    fecha_exp = _parse_datetime(root.attrib.get("FechaExp"))

    return {
        "uuid": uuid,
        "version": root.attrib.get("Version"),
        "fecha_exp": fecha_exp,
        "ejercicio": _parse_int(root.attrib.get("Ejercicio")),
        "mes_ini": _parse_int(root.attrib.get("MesIni")),
        "mes_fin": _parse_int(root.attrib.get("MesFin")),
        "emisor_rfc": emisor.attrib.get("RfcEmisor") if emisor is not None else None,
        "emisor_nombre": emisor.attrib.get("NomDenRazSocE")
        if emisor is not None
        else None,
        "receptor_rfc": receptor_rfc,
        "receptor_nombre": receptor_nombre,
        "monto_tot_operacion": _parse_float(
            totales.attrib.get("MontoTotOperacion") if totales is not None else None
        ),
        "monto_tot_grav": _parse_float(
            totales.attrib.get("MontoTotGrav") if totales is not None else None
        ),
        "monto_tot_exent": _parse_float(
            totales.attrib.get("MontoTotExent") if totales is not None else None
        ),
        "monto_tot_ret": _parse_float(
            totales.attrib.get("MontoTotRet") if totales is not None else None
        ),
        "periodicidad": root.attrib.get("Periodicidad"),
        "num_serv": _parse_int(
            plataforma.attrib.get("NumServ") if plataforma is not None else None
        ),
        "mon_tot_serv_siva": _parse_float(
            plataforma.attrib.get("MonTotServSIVA") if plataforma is not None else None
        ),
        "total_iva_trasladado": _parse_float(
            plataforma.attrib.get("TotalIVATrasladado")
            if plataforma is not None
            else None
        ),
        "total_iva_retenido": _parse_float(
            plataforma.attrib.get("TotalIVARetenido")
            if plataforma is not None
            else None
        ),
        "total_isr_retenido": _parse_float(
            plataforma.attrib.get("TotalISRRetenido")
            if plataforma is not None
            else None
        ),
        "dif_iva_entregado_prest_serv": _parse_float(
            plataforma.attrib.get("DifIVAEntregadoPrestServ")
            if plataforma is not None
            else None
        ),
        "mon_total_por_uso_plataforma": _parse_float(
            plataforma.attrib.get("MonTotalporUsoPlataforma")
            if plataforma is not None
            else None
        ),
    }


def _localname(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_first(root: ET.Element, localname: str) -> ET.Element | None:
    for elem in root.iter():
        if _localname(elem.tag) == localname:
            return elem
    return None


def _find_all(root: ET.Element, localname: str) -> list[ET.Element]:
    return [elem for elem in root.iter() if _localname(elem.tag) == localname]


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def _parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _map_naturaleza(tipo: str | None) -> str | None:
    if not tipo:
        return None
    return {
        "I": "Ingreso",
        "E": "Egreso",
        "P": "Pago",
        "T": "Traslado",
        "N": "Nomina",
    }.get(tipo, tipo)


def _parse_retenciones_receptor(
    receptor: ET.Element | None,
) -> tuple[str | None, str | None]:
    if receptor is None:
        return None, None

    nacional = _find_first(receptor, "Nacional")
    if nacional is not None:
        return nacional.attrib.get("RfcRecep"), nacional.attrib.get("NomDenRazSocR")

    extranjero = _find_first(receptor, "Extranjero")
    if extranjero is not None:
        return extranjero.attrib.get("NumRegIdTrib"), extranjero.attrib.get("NomDenRazSocR")

    return receptor.attrib.get("RfcRecep"), receptor.attrib.get("NomDenRazSocR")
