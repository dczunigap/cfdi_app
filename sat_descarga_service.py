from __future__ import annotations

from sat_endpoints import SatEndpoints
from sat_soap_client import SoapHttpClient


class SatDescargaSoapService:
    def __init__(self, endpoints: SatEndpoints, client: SoapHttpClient | None = None) -> None:
        self._endpoints = endpoints
        self._client = client or SoapHttpClient()

    def autenticar(self, signed_xml: str, soap_action: str | None = None) -> str:
        return self._client.post_soap_text(
            url=self._endpoints.auth_url,
            body_xml=signed_xml,
            soap_action=soap_action,
        )

    def solicitar_descarga(
        self,
        request_xml: str,
        soap_action: str | None = None,
        access_token: str | None = None,
    ) -> str:
        headers = _auth_headers(access_token)
        return self._client.post_soap_text(
            url=self._endpoints.solicitud_url,
            body_xml=request_xml,
            soap_action=soap_action,
            extra_headers=headers,
        )

    def verificar_descarga(
        self,
        request_xml: str,
        soap_action: str | None = None,
        access_token: str | None = None,
    ) -> str:
        headers = _auth_headers(access_token)
        return self._client.post_soap_text(
            url=self._endpoints.verificacion_url,
            body_xml=request_xml,
            soap_action=soap_action,
            extra_headers=headers,
        )

    def descargar_paquete(
        self,
        request_xml: str,
        soap_action: str | None = None,
        access_token: str | None = None,
    ) -> bytes:
        headers = _auth_headers(access_token)
        return self._client.post_soap_bytes(
            url=self._endpoints.descarga_url,
            body_xml=request_xml,
            soap_action=soap_action,
            extra_headers=headers,
        )


def _auth_headers(access_token: str | None) -> dict[str, str] | None:
    if not access_token:
        return None
    return {"Authorization": f'WRAP access_token="{access_token}"'}
