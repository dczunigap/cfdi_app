from __future__ import annotations

import argparse
import base64
import hashlib
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import etree

SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
WSU = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
DS = "http://www.w3.org/2000/09/xmldsig#"


def _load_xml(path: Path) -> etree._Element:
    text = path.read_text(encoding="utf-8")
    return etree.fromstring(text.encode("utf-8"))


def _c14n(element: etree._Element) -> bytes:
    return etree.tostring(element, method="c14n", exclusive=True, with_comments=False)


def verify_xml(xml_path: Path) -> int:
    root = _load_xml(xml_path)
    ns = {"s": SOAP_ENV, "u": WSU, "o": WSSE, "ds": DS}

    timestamp = root.find(".//u:Timestamp", namespaces=ns)
    signed_info = root.find(".//ds:SignedInfo", namespaces=ns)
    digest_value = root.find(".//ds:DigestValue", namespaces=ns)
    signature_value = root.find(".//ds:SignatureValue", namespaces=ns)
    token = root.find(".//o:BinarySecurityToken", namespaces=ns)

    if timestamp is None or signed_info is None or digest_value is None or signature_value is None:
        print("No se encontraron los nodos requeridos en el XML.")
        return 2
    if token is None or not token.text:
        print("No se encontro el BinarySecurityToken en el XML.")
        return 2

    ts_c14n = _c14n(timestamp)
    digest_calc = base64.b64encode(hashlib.sha1(ts_c14n).digest()).decode("ascii")
    digest_xml = (digest_value.text or "").strip()

    print("Digest XML  :", digest_xml)
    print("Digest Calc :", digest_calc)
    print("Digest Match:", digest_xml == digest_calc)

    si_c14n = _c14n(signed_info)
    sig_xml = base64.b64decode((signature_value.text or "").strip())

    cert_der = base64.b64decode(token.text.strip())
    cert = x509.load_der_x509_certificate(cert_der)
    pub = cert.public_key()
    try:
        pub.verify(sig_xml, si_c14n, padding.PKCS1v15(), hashes.SHA1())
        print("Signature Match: True")
    except Exception as exc:
        print(f"Signature Match: False ({exc})")
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica DigestValue y SignatureValue WS-Security.")
    parser.add_argument("--xml", required=True, help="Ruta del XML SOAP (sat_req_*.xml)")
    args = parser.parse_args()
    return verify_xml(Path(args.xml))


if __name__ == "__main__":
    raise SystemExit(main())
