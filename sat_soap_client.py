from __future__ import annotations

import gzip
import logging
import re
import zlib
import urllib.request
from urllib.error import HTTPError, URLError

from config import SAT_TIMEOUT_SECONDS


SOAP_ENV = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
    "{header}"
    "<soapenv:Body>{body}</soapenv:Body>"
    "</soapenv:Envelope>"
)


class SoapHttpClient:
    def __init__(self, timeout_seconds: int | None = None) -> None:
        self._timeout_seconds = timeout_seconds or SAT_TIMEOUT_SECONDS
        self._logger = logging.getLogger("cfdi_app")

    def post_soap_bytes(
        self,
        url: str,
        body_xml: str,
        soap_action: str | None = None,
        header_xml: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> bytes:
        if "Envelope" in body_xml:
            envelope = body_xml
        else:
            header_part = header_xml if header_xml is not None else "<soapenv:Header/>"
            envelope = SOAP_ENV.format(header=header_part, body=body_xml)
        self._logger.debug(
            "SAT SOAP request url=%s action=%s bytes=%s headers=%s",
            url,
            soap_action or "",
            len(envelope),
            ",".join(sorted((extra_headers or {}).keys())),
        )
        self._logger.debug("SAT SOAP body preview=%s", _redact_envelope(envelope))
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "Accept-Encoding": "gzip, deflate",
            "Expect": "100-continue",
        }
        if soap_action:
            action_value = soap_action.strip()
            if not (action_value.startswith('"') and action_value.endswith('"')):
                action_value = f"\"{action_value}\""
            headers["SOAPAction"] = action_value
        if extra_headers:
            headers.update(extra_headers)
        request = urllib.request.Request(
            url=url,
            data=envelope.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                data = response.read()
                encoding = (response.headers.get("Content-Encoding") or "").lower()
                if encoding == "gzip":
                    data = gzip.decompress(data)
                elif encoding == "deflate":
                    try:
                        data = zlib.decompress(data)
                    except zlib.error:
                        data = zlib.decompress(data, -zlib.MAX_WBITS)
                return data
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            raise RuntimeError(f"SOAP HTTP {exc.code} at {url}: {detail}".strip()) from exc
        except URLError as exc:
            raise RuntimeError(f"SOAP URL error at {url}: {exc}") from exc

    def post_soap_text(
        self,
        url: str,
        body_xml: str,
        soap_action: str | None = None,
        header_xml: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> str:
        data = self.post_soap_bytes(
            url=url,
            body_xml=body_xml,
            soap_action=soap_action,
            header_xml=header_xml,
            extra_headers=extra_headers,
        )
        return data.decode("utf-8", errors="replace")

def _redact_envelope(envelope: str) -> str:
    redacted = envelope
    redacted = re.sub(
        r"(<o:BinarySecurityToken[^>]*>)(.*?)(</o:BinarySecurityToken>)",
        r"\1***REDACTED***\3",
        redacted,
        flags=re.DOTALL,
    )
    redacted = re.sub(
        r"(<ds:SignatureValue>)(.*?)(</ds:SignatureValue>)",
        r"\1***REDACTED***\3",
        redacted,
        flags=re.DOTALL,
    )
    if len(redacted) > 2000:
        return redacted[:2000] + "...[truncated]"
    return redacted
