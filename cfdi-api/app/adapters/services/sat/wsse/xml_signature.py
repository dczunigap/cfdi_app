from __future__ import annotations

import base64

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from lxml import etree

DS = "http://www.w3.org/2000/09/xmldsig#"


def sign_enveloped_element(element: etree._Element, key_pem: bytes, cert_pem: bytes) -> None:
    digest_value = _digest_enveloped(element)
    signature = etree.Element(etree.QName(DS, "Signature"), nsmap={None: DS})
    signed_info = etree.SubElement(signature, etree.QName(DS, "SignedInfo"))
    etree.SubElement(
        signed_info,
        etree.QName(DS, "CanonicalizationMethod"),
        Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )
    etree.SubElement(
        signed_info,
        etree.QName(DS, "SignatureMethod"),
        Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1",
    )
    reference = etree.SubElement(signed_info, etree.QName(DS, "Reference"), URI="")
    transforms = etree.SubElement(reference, etree.QName(DS, "Transforms"))
    etree.SubElement(
        transforms,
        etree.QName(DS, "Transform"),
        Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature",
    )
    etree.SubElement(
        reference, etree.QName(DS, "DigestMethod"), Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"
    )
    digest_el = etree.SubElement(reference, etree.QName(DS, "DigestValue"))
    digest_el.text = digest_value

    signed_info_c14n = etree.tostring(
        signed_info, method="c14n", exclusive=False, with_comments=False
    )
    private_key = load_pem_private_key(key_pem, password=None)
    signature_value = private_key.sign(
        signed_info_c14n, padding.PKCS1v15(), hashes.SHA1()
    )

    sig_value_el = etree.SubElement(signature, etree.QName(DS, "SignatureValue"))
    sig_value_el.text = base64.b64encode(signature_value).decode("ascii")
    key_info = etree.SubElement(signature, etree.QName(DS, "KeyInfo"))
    x509_data = etree.SubElement(key_info, etree.QName(DS, "X509Data"))
    _append_x509_issuer_serial(x509_data, cert_pem)
    x509_cert = etree.SubElement(x509_data, etree.QName(DS, "X509Certificate"))
    x509_cert.text = _pem_to_b64(cert_pem)

    element.append(signature)


def _digest_enveloped(element: etree._Element) -> str:
    clone = etree.fromstring(etree.tostring(element))
    for sig in clone.findall(f".//{{{DS}}}Signature"):
        sig.getparent().remove(sig)
    data = etree.tostring(clone, method="c14n", exclusive=False, with_comments=False)
    digest = hashes.Hash(hashes.SHA1())
    digest.update(data)
    return base64.b64encode(digest.finalize()).decode("ascii")


def _pem_to_b64(pem_bytes: bytes) -> str:
    text = pem_bytes.decode("utf-8").strip()
    lines = [line for line in text.splitlines() if "BEGIN CERTIFICATE" not in line and "END CERTIFICATE" not in line]
    return "".join(lines).strip()


def _append_x509_issuer_serial(parent: etree._Element, cert_pem: bytes) -> None:
    cert = x509.load_pem_x509_certificate(cert_pem)
    issuer_name = cert.issuer.rfc4514_string()
    issuer_serial = etree.SubElement(parent, etree.QName(DS, "X509IssuerSerial"))
    issuer_name_el = etree.SubElement(issuer_serial, etree.QName(DS, "X509IssuerName"))
    issuer_name_el.text = issuer_name
    serial_el = etree.SubElement(issuer_serial, etree.QName(DS, "X509SerialNumber"))
    serial_el.text = str(cert.serial_number)
