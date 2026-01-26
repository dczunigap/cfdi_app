from __future__ import annotations

import os
import time
import unittest
from datetime import datetime

from app.adapters.outbound.db.session import SessionLocal
from app.adapters.outbound.db.models import SatCredentialModel
from app.adapters.services.sat.crypto.crypto import decrypt_bytes, decrypt_text
from app.application.sat.dto import SolicitudDescargaParams
from app.adapters.services.sat.sat_gateway import SoapSatGateway
from app.adapters.services.sat.soap.actions import (
    SOAP_CFDI_ACTION_AUTENTICA,
    SOAP_CFDI_ACTION_SOLICITA_EMITIDOS,
    SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS,
    SOAP_RETENCIONES_ACTION_AUTENTICA,
    SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS,
    SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS,
    SOAP_RETENCIONES_ACTION_VERIFICA,
    SOAP_RETENCIONES_ACTION_DESCARGA,
)
from app.adapters.services.sat.pkcs12.pfx import load_key_material_from_pfx_bytes
from app.core.config import settings


class TestSatSolicitudIntegration(unittest.TestCase):
    def _load_credentials(self) -> tuple[str, object]:
        if os.getenv("RUN_SAT_INTEGRATION") != "1":
            self.skipTest("Set RUN_SAT_INTEGRATION=1 to run SAT integration tests.")

        if not (settings.sat_password_secret or "").strip():
            self.skipTest("SAT_PASSWORD_SECRET no configurado.")

        with SessionLocal() as db:
            cred = (
                db.query(SatCredentialModel)
                .order_by(SatCredentialModel.created_at.desc())
                .first()
            )
            if not cred:
                self.skipTest("No hay credenciales SAT en la BD.")
            password = decrypt_text(cred.pfx_password_encrypted)
            try:
                pfx_bytes = decrypt_bytes(cred.pfx_encrypted)
            except Exception:
                self.skipTest("Credenciales no cifradas con la clave actual.")
            key_material = load_key_material_from_pfx_bytes(pfx_bytes, password)
            rfc_value = cred.rfc
        return rfc_value, key_material

    def test_solicitud_descarga_emitidos_y_recibidos(self) -> None:
        rfc_value, key_material = self._load_credentials()

        gateway = SoapSatGateway()

        token = gateway.autenticar(
            kind="cfdi",
            key_material=key_material,
            soap_action=SOAP_CFDI_ACTION_AUTENTICA,
            to_url=None,
            action=SOAP_CFDI_ACTION_AUTENTICA,
        )
        params_emitidos = SolicitudDescargaParams(
            rfc_solicitante=rfc_value,
            rfc_emisor=rfc_value,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_emitidos = gateway.solicitar_descarga(
            kind="cfdi",
            key_material=key_material,
            params=params_emitidos,
            access_token=token,
            soap_action=SOAP_CFDI_ACTION_SOLICITA_EMITIDOS,
            tag_name="SolicitaDescargaEmitidos",
        )
        print(f"\nIdSolicitud emitidos: {solicitud_id_emitidos}")

        params_recibidos = SolicitudDescargaParams(
            rfc_solicitante=rfc_value,
            rfc_receptor=rfc_value,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_recibidos = gateway.solicitar_descarga(
            kind="cfdi",
            key_material=key_material,
            params=params_recibidos,
            access_token=token,
            soap_action=SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS,
            tag_name="SolicitaDescargaRecibidos",
        )
        print(f"\nIdSolicitud recibidos: {solicitud_id_recibidos}")
        time.sleep(120)

        verificacion_emitidos = gateway.verificar_descarga(
            kind="cfdi",
            key_material=key_material,
            rfc_solicitante=rfc_value,
            id_solicitud=solicitud_id_emitidos,
            access_token=token,
        )
        print(
            "Verificacion emitidos:",
            f"EstadoSolicitud={verificacion_emitidos.estado_solicitud}",
            f"NumeroCFDIs={verificacion_emitidos.numero_cfdis}",
            f"Mensaje={verificacion_emitidos.mensaje}",
        )

        time.sleep(10)

        verificacion_recibidos = gateway.verificar_descarga(
            kind="cfdi",
            key_material=key_material,
            rfc_solicitante=rfc_value,
            id_solicitud=solicitud_id_recibidos,
            access_token=token,
        )
        print(
            "Verificacion recibidos:",
            f"EstadoSolicitud={verificacion_recibidos.estado_solicitud}",
            f"NumeroCFDIs={verificacion_recibidos.numero_cfdis}",
            f"Mensaje={verificacion_recibidos.mensaje}",
        )

        self.assertTrue(isinstance(solicitud_id_emitidos, str) and solicitud_id_emitidos.strip())
        self.assertTrue(isinstance(solicitud_id_recibidos, str) and solicitud_id_recibidos.strip())

    def test_verificacion_emitidos_recibidos(self) -> None:
        rfc_value, key_material = self._load_credentials()

        gateway = SoapSatGateway()

        token = gateway.autenticar(
            kind="cfdi",
            key_material=key_material,
            soap_action=SOAP_CFDI_ACTION_AUTENTICA,
            to_url=None,
            action=SOAP_CFDI_ACTION_AUTENTICA,
        )

        verificacion_emitidos = gateway.verificar_descarga(
            kind="cfdi",
            key_material=key_material,
            rfc_solicitante=rfc_value,
            id_solicitud="fd0b8cd0-7778-4d93-bcc1-8703ffcf8e69",
            access_token=token,
        )
        print(
            "Verificacion emitidos:",
            f"EstadoSolicitud={verificacion_emitidos.estado_solicitud}",
            f"NumeroCFDIs={verificacion_emitidos.numero_cfdis}",
            f"Mensaje={verificacion_emitidos.mensaje}",
        )

        verificacion_recibidos = gateway.verificar_descarga(
            kind="cfdi",
            key_material=key_material,
            rfc_solicitante=rfc_value,
            id_solicitud="a10c16a2-2381-4011-a86f-17ce76853dfe",
            access_token=token,
        )
        print(
            "Verificacion recibidos:",
            f"EstadoSolicitud={verificacion_recibidos.estado_solicitud}",
            f"NumeroCFDIs={verificacion_recibidos.numero_cfdis}",
            f"Mensaje={verificacion_recibidos.mensaje}",
        )

        self.assertTrue(isinstance(verificacion_emitidos.mensaje, str) and verificacion_emitidos.mensaje.strip())
        self.assertTrue(isinstance(verificacion_recibidos.mensaje, str) and verificacion_recibidos.mensaje.strip())

    def test_retenciones_solicitud_verificacion_descarga(self) -> None:
        rfc_value, key_material = self._load_credentials()

        gateway = SoapSatGateway()

        token_value = gateway.autenticar(
            kind="retenciones",
            key_material=key_material,
            soap_action=SOAP_RETENCIONES_ACTION_AUTENTICA,
            to_url=None,
            action=SOAP_RETENCIONES_ACTION_AUTENTICA,
        )

        params_emitidos = SolicitudDescargaParams(
            rfc_solicitante=rfc_value,
            rfc_emisor=rfc_value,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_emitidos = gateway.solicitar_descarga(
            kind="retenciones",
            key_material=key_material,
            params=params_emitidos,
            access_token=token_value,
            soap_action=SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS,
            tag_name="SolicitaDescargaEmitidos",
        )
        print(f"\nRET IdSolicitud emitidos: {solicitud_id_emitidos}")

        params_recibidos = SolicitudDescargaParams(
            rfc_solicitante=rfc_value,
            rfc_receptor=rfc_value,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_recibidos = gateway.solicitar_descarga(
            kind="retenciones",
            key_material=key_material,
            params=params_recibidos,
            access_token=token_value,
            soap_action=SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS,
            tag_name="SolicitaDescargaRecibidos",
        )
        print(f"\nRET IdSolicitud recibidos: {solicitud_id_recibidos}")

        time.sleep(120)

        verificacion_emitidos = gateway.verificar_descarga(
            kind="retenciones",
            key_material=key_material,
            rfc_solicitante=rfc_value,
            id_solicitud=solicitud_id_emitidos,
            access_token=token_value,
            soap_action=SOAP_RETENCIONES_ACTION_VERIFICA,
        )
        print(
            "RET Verificacion emitidos:",
            f"EstadoSolicitud={verificacion_emitidos.estado_solicitud}",
            f"NumeroCFDIs={verificacion_emitidos.numero_cfdis}",
            f"Mensaje={verificacion_emitidos.mensaje}",
        )

        time.sleep(10)

        verificacion_recibidos = gateway.verificar_descarga(
            kind="retenciones",
            key_material=key_material,
            rfc_solicitante=rfc_value,
            id_solicitud=solicitud_id_recibidos,
            access_token=token_value,
            soap_action=SOAP_RETENCIONES_ACTION_VERIFICA,
        )
        print(
            "RET Verificacion recibidos:",
            f"EstadoSolicitud={verificacion_recibidos.estado_solicitud}",
            f"NumeroCFDIs={verificacion_recibidos.numero_cfdis}",
            f"Mensaje={verificacion_recibidos.mensaje}",
        )

        for paquete_id in verificacion_emitidos.paquetes + verificacion_recibidos.paquetes:
            zip_bytes = gateway.descargar_paquete(
                kind="retenciones",
                key_material=key_material,
                rfc_solicitante=rfc_value,
                id_paquete=paquete_id,
                access_token=token_value,
                soap_action=SOAP_RETENCIONES_ACTION_DESCARGA,
            )
            print(f"RET paquete {paquete_id}: {len(zip_bytes)} bytes")

        self.assertTrue(isinstance(solicitud_id_emitidos, str) and solicitud_id_emitidos.strip())
        self.assertTrue(isinstance(solicitud_id_recibidos, str) and solicitud_id_recibidos.strip())


if __name__ == "__main__":
    unittest.main()
