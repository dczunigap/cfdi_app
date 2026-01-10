from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import io
import xml.etree.ElementTree as ET

from config import MI_RFC


# Namespaces conocidos
CFDI_40_NS = "http://www.sat.gob.mx/cfd/4"
TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"

RET_20_NS = "http://www.sat.gob.mx/esquemas/retencionpago/2"
PLAT_10_NS = "http://www.sat.gob.mx/esquemas/retencionpago/1/PlataformasTecnologicas10"
PLAT_10_NS_ALT = "http://www.sat.gob.mx/esquemas/retencionpago/1/PlataformasTecnologicas10"  # mismo

PAGOS20_NS = "http://www.sat.gob.mx/Pagos20"
PAGOS10_NS = "http://www.sat.gob.mx/Pagos"  # por si aparece


def _to_decimal(val: str | None) -> Decimal | None:
    if val is None or val == "":
        return None
    try:
        return Decimal(val)
    except Exception:
        return None


def _to_int(val: str | None) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(val)
    except Exception:
        return None


def _parse_dt(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except Exception:
        # Soporta offsets tipo -0600 (sin colon)
        try:
            if len(val) >= 5 and (val[-5] in ["+", "-"]) and val[-2:].isdigit() and val[-4:-2].isdigit():
                val2 = val[:-2] + ":" + val[-2:]
                return datetime.fromisoformat(val2)
        except Exception:
            pass
    return None


def _ns_from_tag(tag: str) -> str | None:
    # "{namespace}Comprobante"
    if tag.startswith("{") and "}" in tag:
        return tag[1:tag.index("}")]
    return None


def _collect_namespaces(xml_bytes: bytes) -> dict[str, str]:
    ns: dict[str, str] = {}
    for event, elem in ET.iterparse(io.BytesIO(xml_bytes), events=("start-ns",)):
        prefix, uri = elem
        ns[prefix or ""] = uri
    return ns


def detect_xml_kind(xml_bytes: bytes) -> str:
    """Devuelve: 'cfdi' | 'retenciones' | 'unknown'"""
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        # intenta quitar BOM si existe
        xml_bytes = xml_bytes.lstrip(b"\xef\xbb\xbf")
        root = ET.fromstring(xml_bytes)

    ns = _ns_from_tag(root.tag) or ""
    local = root.tag.split("}")[-1] if "}" in root.tag else root.tag

    if local == "Comprobante" and (CFDI_40_NS in ns or "/cfd/" in ns):
        return "cfdi"
    if local == "Retenciones" and (RET_20_NS in ns or "retencionpago" in ns):
        return "retenciones"
    return "unknown"


def _signed_factor(tipo: str | None) -> int:
    # E (egreso/nota de crédito) resta a I (ingreso).
    if (tipo or "").upper() == "E":
        return -1
    return 1


def _clasifica_naturaleza(tipo: str | None, emisor_rfc: str | None, receptor_rfc: str | None) -> str:
    tipo_u = (tipo or "").upper()
    em = (emisor_rfc or "").upper()
    rec = (receptor_rfc or "").upper()
    mi = (MI_RFC or "").upper()

    if tipo_u == "P":
        # Complemento de pago: si tú lo emites normalmente es cobro; si tú lo recibes es pago
        if em == mi:
            return "cobro"
        if rec == mi:
            return "pago"
        return "otro"

    if em == mi:
        return "ingreso"
    if rec == mi:
        return "gasto"
    return "otro"


def parse_cfdi_40(xml_bytes: bytes) -> dict:
    """Parsea CFDI 4.0 (I/E/P/T/N...) usando solo stdlib.

    Retorna:
    - factura: dict con campos para tabla Factura
    - conceptos: lista de dicts para Concepto
    - pagos: lista de dicts para Pago (solo si tipo=P y viene complemento)
    - factor: +1 o -1 (para resúmenes: E resta)
    """
    nsmap = _collect_namespaces(xml_bytes)

    root = ET.fromstring(xml_bytes.lstrip(b"\xef\xbb\xbf"))

    cfdi_ns = _ns_from_tag(root.tag) or nsmap.get("cfdi") or CFDI_40_NS

    def q(ns: str, t: str) -> str:
        return f"{{{ns}}}{t}"

    tipo = root.attrib.get("TipoDeComprobante")
    fecha_emision = _parse_dt(root.attrib.get("Fecha"))
    year_emision = fecha_emision.year if fecha_emision else None
    month_emision = fecha_emision.month if fecha_emision else None

    data: dict = {
        "uuid": None,
        "version": root.attrib.get("Version"),
        "tipo_comprobante": tipo,
        "fecha_emision": fecha_emision,
        "year_emision": year_emision,
        "month_emision": month_emision,
        "naturaleza": None,
        "emisor_rfc": None,
        "emisor_nombre": None,
        "receptor_rfc": None,
        "receptor_nombre": None,
        "uso_cfdi": None,
        "moneda": root.attrib.get("Moneda"),
        "metodo_pago": root.attrib.get("MetodoPago"),
        "forma_pago": root.attrib.get("FormaPago"),
        "subtotal": _to_decimal(root.attrib.get("SubTotal")),
        "descuento": _to_decimal(root.attrib.get("Descuento")),
        "total": _to_decimal(root.attrib.get("Total")),
        "total_trasladados": None,
        "total_retenidos": None,
        "conceptos": [],
        "pagos": [],
        "factor": _signed_factor(tipo),
    }

    emisor = root.find(q(cfdi_ns, "Emisor"))
    if emisor is not None:
        data["emisor_rfc"] = emisor.attrib.get("Rfc")
        data["emisor_nombre"] = emisor.attrib.get("Nombre")

    receptor = root.find(q(cfdi_ns, "Receptor"))
    if receptor is not None:
        data["receptor_rfc"] = receptor.attrib.get("Rfc")
        data["receptor_nombre"] = receptor.attrib.get("Nombre")
        data["uso_cfdi"] = receptor.attrib.get("UsoCFDI")

    data["naturaleza"] = _clasifica_naturaleza(tipo, data["emisor_rfc"], data["receptor_rfc"])

    impuestos = root.find(q(cfdi_ns, "Impuestos"))
    if impuestos is not None:
        data["total_trasladados"] = _to_decimal(impuestos.attrib.get("TotalImpuestosTrasladados"))
        data["total_retenidos"] = _to_decimal(impuestos.attrib.get("TotalImpuestosRetenidos"))

    # UUID
    timbre = root.find(f".//{{{TFD_NS}}}TimbreFiscalDigital")
    if timbre is not None:
        data["uuid"] = timbre.attrib.get("UUID")

    # Conceptos
    conceptos_parent = root.find(q(cfdi_ns, "Conceptos"))
    if conceptos_parent is not None:
        for c in conceptos_parent.findall(q(cfdi_ns, "Concepto")):
            data["conceptos"].append(
                {
                    "clave_prod_serv": c.attrib.get("ClaveProdServ"),
                    "cantidad": _to_decimal(c.attrib.get("Cantidad")),
                    "clave_unidad": c.attrib.get("ClaveUnidad"),
                    "descripcion": c.attrib.get("Descripcion"),
                    "valor_unitario": _to_decimal(c.attrib.get("ValorUnitario")),
                    "importe": _to_decimal(c.attrib.get("Importe")),
                    "objeto_imp": c.attrib.get("ObjetoImp"),
                }
            )

    # Complemento de pagos (Tipo=P)
    if (tipo or "").upper() == "P":
        pagos_ns = None
        if PAGOS20_NS in nsmap.values():
            pagos_ns = PAGOS20_NS
        elif PAGOS10_NS in nsmap.values():
            pagos_ns = PAGOS10_NS

        if pagos_ns:
            for p in root.findall(f".//{{{pagos_ns}}}Pago"):
                fecha_pago = _parse_dt(p.attrib.get("FechaPago"))
                y = fecha_pago.year if fecha_pago else None
                m = fecha_pago.month if fecha_pago else None
                data["pagos"].append(
                    {
                        "fecha_pago": fecha_pago,
                        "year_pago": y,
                        "month_pago": m,
                        "monto": _to_decimal(p.attrib.get("Monto")),
                        "moneda_p": p.attrib.get("MonedaP"),
                        "forma_pago_p": p.attrib.get("FormaDePagoP"),
                    }
                )

    return data


def parse_retenciones_plataforma(xml_bytes: bytes) -> dict:
    """Parsea Retenciones 2.0 con complemento Servicios de Plataformas Tecnológicas 1.0.

    Retorna dict con campos para RetencionPlataforma.
    """
    xml_bytes = xml_bytes.lstrip(b"\xef\xbb\xbf")
    nsmap = _collect_namespaces(xml_bytes)
    root = ET.fromstring(xml_bytes)

    ret_ns = _ns_from_tag(root.tag) or nsmap.get("retenciones") or RET_20_NS

    def q(ns: str, t: str) -> str:
        return f"{{{ns}}}{t}"

    out: dict = {
        "uuid": None,
        "version": root.attrib.get("Version"),
        "fecha_exp": _parse_dt(root.attrib.get("FechaExp")),
        "ejercicio": None,
        "mes_ini": None,
        "mes_fin": None,
        "emisor_rfc": None,
        "emisor_nombre": None,
        "receptor_rfc": None,
        "receptor_nombre": None,
        "monto_tot_operacion": None,
        "monto_tot_grav": None,
        "monto_tot_exent": None,
        "monto_tot_ret": None,
        "periodicidad": None,
        "num_serv": None,
        "mon_tot_serv_siva": None,
        "total_iva_trasladado": None,
        "total_iva_retenido": None,
        "total_isr_retenido": None,
        "dif_iva_entregado_prest_serv": None,
        "mon_total_por_uso_plataforma": None,
    }

    emisor = root.find(q(ret_ns, "Emisor"))
    if emisor is not None:
        out["emisor_rfc"] = emisor.attrib.get("RfcE")
        out["emisor_nombre"] = emisor.attrib.get("NomDenRazSocE")

    receptor = root.find(q(ret_ns, "Receptor"))
    if receptor is not None:
        # Nacional / Extranjero
        nac = receptor.find(q(ret_ns, "Nacional"))
        if nac is not None:
            out["receptor_rfc"] = nac.attrib.get("RfcR")
            out["receptor_nombre"] = nac.attrib.get("NomDenRazSocR")

    periodo = root.find(q(ret_ns, "Periodo"))
    if periodo is not None:
        out["ejercicio"] = _to_int(periodo.attrib.get("Ejercicio"))
        out["mes_ini"] = _to_int(periodo.attrib.get("MesIni"))
        out["mes_fin"] = _to_int(periodo.attrib.get("MesFin"))

    tot = root.find(q(ret_ns, "Totales"))
    if tot is not None:
        out["monto_tot_operacion"] = _to_decimal(tot.attrib.get("MontoTotOperacion"))
        out["monto_tot_grav"] = _to_decimal(tot.attrib.get("MontoTotGrav"))
        out["monto_tot_exent"] = _to_decimal(tot.attrib.get("MontoTotExent"))
        out["monto_tot_ret"] = _to_decimal(tot.attrib.get("MontoTotRet"))

    comp = root.find(q(ret_ns, "Complemento"))
    if comp is not None:
        # UUID del timbre
        tfd = comp.find(f".//{{{TFD_NS}}}TimbreFiscalDigital")
        if tfd is not None:
            out["uuid"] = tfd.attrib.get("UUID")

        # Complemento Plataformas Tecnológicas
        plat = comp.find(f".//{{{PLAT_10_NS}}}ServiciosPlataformasTecnologicas")
        if plat is None:
            plat = comp.find(f".//{{{PLAT_10_NS_ALT}}}ServiciosPlataformasTecnologicas")

        if plat is not None:
            out["periodicidad"] = plat.attrib.get("Periodicidad")
            out["num_serv"] = _to_int(plat.attrib.get("NumServ"))
            out["mon_tot_serv_siva"] = _to_decimal(plat.attrib.get("MonTotServSIVA"))
            out["total_iva_trasladado"] = _to_decimal(plat.attrib.get("TotalIVATrasladado"))
            out["total_iva_retenido"] = _to_decimal(plat.attrib.get("TotalIVARetenido"))
            out["total_isr_retenido"] = _to_decimal(plat.attrib.get("TotalISRRetenido"))
            out["dif_iva_entregado_prest_serv"] = _to_decimal(plat.attrib.get("DifIVAEntregadoPrestServ"))
            out["mon_total_por_uso_plataforma"] = _to_decimal(plat.attrib.get("MonTotalporUsoPlataforma"))

    return out
