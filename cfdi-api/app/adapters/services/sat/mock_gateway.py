from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from uuid import uuid4

from app.application.sat.dto import (
    DescargaPaqueteResult,
    SolicitudDescargaParams,
    SolicitudDescargaResult,
    VerificacionResult,
)
from app.ports.sat_gateway import SatGateway


class MockSatGateway(SatGateway):
    def load_key_material(self, pfx_bytes: bytes, password: str | None):
        return object()

    def autenticar(
        self,
        kind: str,
        key_material,
        soap_action: str | None = None,
        to_url: str | None = None,
        action: str | None = None,
    ) -> str:
        return "mock-token"

    def solicitar_descarga(
        self,
        kind: str,
        key_material,
        params: SolicitudDescargaParams,
        access_token: str,
        soap_action: str | None = None,
        tag_name: str = "SolicitaDescargaEmitidos",
    ) -> SolicitudDescargaResult:
        return SolicitudDescargaResult(
            id_solicitud=f"mock-solicitud-{uuid4()}",
            codigo_estado="5000",
            mensaje="Mock ok",
        )

    def verificar_descarga(
        self,
        kind: str,
        key_material,
        rfc_solicitante: str,
        id_solicitud: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> VerificacionResult:
        return VerificacionResult(
            estado_solicitud="1",
            codigo_estado="5000",
            numero_cfdis="1",
            mensaje="Mock listo",
            paquetes=[f"mock-paquete-{uuid4()}"],
        )

    def descargar_paquete(
        self,
        kind: str,
        key_material,
        rfc_solicitante: str,
        id_paquete: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> DescargaPaqueteResult:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        if kind == "retenciones":
            xml = _retenciones_xml(now)
        else:
            xml = _cfdi_xml(now)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mock.xml", xml)
        return DescargaPaqueteResult(
            zip_bytes=buffer.getvalue(),
            codigo_estado=None,
            mensaje=None,
        )


def _cfdi_xml(now: str) -> str:
    uuid = str(uuid4()).upper()
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" Version="4.0" '
        f'Fecha="{now}" TipoDeComprobante="I" SubTotal="0" Total="0" Moneda="MXN">'
        '<cfdi:Emisor Rfc="AAA010101AAA" Nombre="Mock Emisor"/>'
        '<cfdi:Receptor Rfc="BBB010101BBB" Nombre="Mock Receptor" UsoCFDI="G01"/>'
        '<cfdi:Conceptos>'
        '<cfdi:Concepto ClaveProdServ="01010101" Cantidad="1" ClaveUnidad="ACT" '
        'Descripcion="Servicio" ValorUnitario="0" Importe="0" ObjetoImp="01"/>'
        "</cfdi:Conceptos>"
        '<cfdi:Complemento>'
        f'<tfd:TimbreFiscalDigital xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital" UUID="{uuid}"/>'
        "</cfdi:Complemento>"
        "</cfdi:Comprobante>"
    )


def _retenciones_xml(now: str) -> str:
    uuid = str(uuid4()).upper()
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<retenciones:Retenciones xmlns:retenciones="http://www.sat.gob.mx/retenciones" '
        'Version="2.0" FechaExp="{now}" Ejercicio="2025" MesIni="1" MesFin="1">'
        '<retenciones:Emisor RfcE="AAA010101AAA" NomDenRazSocE="Mock Emisor"/>'
        '<retenciones:Receptor>'
        '<retenciones:Nacional RfcRecep="BBB010101BBB" NomDenRazSocR="Mock Receptor"/>'
        "</retenciones:Receptor>"
        '<retenciones:Totales MontoTotOperacion="0" MontoTotGrav="0" MontoTotExent="0" MontoTotRet="0"/>'
        '<retenciones:Complemento>'
        f'<tfd:TimbreFiscalDigital xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital" UUID="{uuid}"/>'
        "</retenciones:Complemento>"
        "</retenciones:Retenciones>"
    ).format(now=now)
