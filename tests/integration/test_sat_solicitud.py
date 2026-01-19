import os
import time
import unittest
from datetime import datetime

from sqlalchemy.orm import Session

from config import MI_RFC
from db import SessionLocal
from models import SatCredential
from sat_crypto import decrypt_password
from sat_descarga_requests import SolicitudDescargaParams
from sat_descarga_service import SatDescargaSoapService
from sat_descarga_workflow import SatDescargaWorkflow
from sat_endpoints import SatEndpoints
from sat_actions import (
    SOAP_CFDI_ACTION_AUTENTICA,
    SOAP_CFDI_ACTION_SOLICITA_EMITIDOS,
    SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS,
    SOAP_RETENCIONES_ACTION_AUTENTICA,
    SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS,
    SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS,
    SOAP_RETENCIONES_ACTION_VERIFICA,
    SOAP_RETENCIONES_ACTION_DESCARGA,
)
from sat_ws_security import load_sat_key_material_from_bytes


class TestSatSolicitudIntegration(unittest.TestCase):
    def test_solicitud_descarga_emitidos_y_recibidos(self) -> None:
        if os.getenv("RUN_SAT_INTEGRATION") != "1":
            self.skipTest("Set RUN_SAT_INTEGRATION=1 to run SAT integration tests.")

        with SessionLocal() as db:
            cred = db.query(SatCredential).filter(SatCredential.rfc == MI_RFC).one_or_none()
            if not cred or not cred.cert_der or not cred.key_der:
                self.skipTest("No hay credenciales SAT en la BD para MI_RFC.")

            password = decrypt_password(cred.key_password)
            key_material = load_sat_key_material_from_bytes(
                cred.cert_der,
                cred.key_der,
                password,
            )

        endpoints = SatEndpoints.for_kind("cfdi")
        service = SatDescargaSoapService(endpoints)
        workflow = SatDescargaWorkflow(service=service, key_material=key_material)

        token = workflow.autenticar(
            soap_action=SOAP_CFDI_ACTION_AUTENTICA,
            to_url=endpoints.auth_url,
            action=SOAP_CFDI_ACTION_AUTENTICA,
        )
        params_emitidos = SolicitudDescargaParams(
            rfc_solicitante=MI_RFC,
            rfc_emisor=MI_RFC,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_emitidos = workflow.solicitar_descarga(
            params_emitidos,
            access_token=token,
            soap_action=SOAP_CFDI_ACTION_SOLICITA_EMITIDOS,
            tag_name="SolicitaDescargaEmitidos",
        )
        print(f"\nIdSolicitud emitidos: {solicitud_id_emitidos}")

        params_recibidos = SolicitudDescargaParams(
            rfc_solicitante=MI_RFC,
            rfc_receptor=MI_RFC,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_recibidos = workflow.solicitar_descarga(
            params_recibidos,
            access_token=token,
            soap_action=SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS,
            tag_name="SolicitaDescargaRecibidos",
        )
        print(f"\nIdSolicitud recibidos: {solicitud_id_recibidos}")
        time.sleep(120)

        verificacion_emitidos = workflow.verificar_descarga(
            rfc_solicitante=MI_RFC,
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

        verificacion_recibidos = workflow.verificar_descarga(
            rfc_solicitante=MI_RFC,
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
        if os.getenv("RUN_SAT_INTEGRATION") != "1":
            self.skipTest("Set RUN_SAT_INTEGRATION=1 to run SAT integration tests.")

        with SessionLocal() as db:
            cred = db.query(SatCredential).filter(SatCredential.rfc == MI_RFC).one_or_none()
            if not cred or not cred.cert_der or not cred.key_der:
                self.skipTest("No hay credenciales SAT en la BD para MI_RFC.")

            password = decrypt_password(cred.key_password)
            key_material = load_sat_key_material_from_bytes(
                cred.cert_der,
                cred.key_der,
                password,
            )

        endpoints = SatEndpoints.for_kind("cfdi")
        service = SatDescargaSoapService(endpoints)
        workflow = SatDescargaWorkflow(service=service, key_material=key_material)

        token = workflow.autenticar(
            soap_action=SOAP_CFDI_ACTION_AUTENTICA,
            to_url=endpoints.auth_url,
            action=SOAP_CFDI_ACTION_AUTENTICA,
        )

        verificacion_emitidos = workflow.verificar_descarga(
            rfc_solicitante=MI_RFC,
            id_solicitud="fd0b8cd0-7778-4d93-bcc1-8703ffcf8e69",
            access_token=token,
        )
        print(
            "Verificacion emitidos:",
            f"EstadoSolicitud={verificacion_emitidos.estado_solicitud}",
            f"NumeroCFDIs={verificacion_emitidos.numero_cfdis}",
            f"Mensaje={verificacion_emitidos.mensaje}",
        )
        
        verificacion_recibidos = workflow.verificar_descarga(
            rfc_solicitante=MI_RFC,
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
        if os.getenv("RUN_SAT_INTEGRATION") != "1":
            self.skipTest("Set RUN_SAT_INTEGRATION=1 to run SAT integration tests.")

        with SessionLocal() as db:
            cred = db.query(SatCredential).filter(SatCredential.rfc == MI_RFC).one_or_none()
            if not cred or not cred.cert_der or not cred.key_der:
                self.skipTest("No hay credenciales SAT en la BD para MI_RFC.")

            password = decrypt_password(cred.key_password)
            key_material = load_sat_key_material_from_bytes(
                cred.cert_der,
                cred.key_der,
                password,
            )

        endpoints = SatEndpoints.for_kind("retenciones")
        service = SatDescargaSoapService(endpoints)
        workflow = SatDescargaWorkflow(service=service, key_material=key_material)

        token_value = workflow.autenticar(
            soap_action=SOAP_RETENCIONES_ACTION_AUTENTICA,
            to_url=endpoints.auth_url,
            action=SOAP_RETENCIONES_ACTION_AUTENTICA,
        )

        params_emitidos = SolicitudDescargaParams(
            rfc_solicitante=MI_RFC,
            rfc_emisor=MI_RFC,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_emitidos = workflow.solicitar_descarga(
            params_emitidos,
            access_token=token_value,
            soap_action=SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS,
            tag_name="SolicitaDescargaEmitidos",
        )
        print(f"\nRET IdSolicitud emitidos: {solicitud_id_emitidos}")

        params_recibidos = SolicitudDescargaParams(
            rfc_solicitante=MI_RFC,
            rfc_receptor=MI_RFC,
            fecha_inicial=datetime(2025, 12, 1, 0, 0, 0),
            fecha_final=datetime(2025, 12, 31, 23, 59, 59),
            tipo_solicitud="CFDI",
            complemento="",
            estado_comprobante="Vigente",
            tipo_comprobante="",
            rfc_a_cuenta_terceros="",
        )
        solicitud_id_recibidos = workflow.solicitar_descarga(
            params_recibidos,
            access_token=token_value,
            soap_action=SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS,
            tag_name="SolicitaDescargaRecibidos",
        )
        print(f"\nRET IdSolicitud recibidos: {solicitud_id_recibidos}")

        time.sleep(120)

        verificacion_emitidos = workflow.verificar_descarga(
            rfc_solicitante=MI_RFC,
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

        verificacion_recibidos = workflow.verificar_descarga(
            rfc_solicitante=MI_RFC,
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
            zip_bytes = workflow.descargar_paquete(
                rfc_solicitante=MI_RFC,
                id_paquete=paquete_id,
                access_token=token_value,
                soap_action=SOAP_RETENCIONES_ACTION_DESCARGA,
            )
            print(f"RET paquete {paquete_id}: {len(zip_bytes)} bytes")

        self.assertTrue(isinstance(solicitud_id_emitidos, str) and solicitud_id_emitidos.strip())
        self.assertTrue(isinstance(solicitud_id_recibidos, str) and solicitud_id_recibidos.strip())

    
if __name__ == "__main__":
    unittest.main()
