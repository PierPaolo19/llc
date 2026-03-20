#!/usr/bin/env python3
"""
keybox_helper.py – Utility for working with AndroidAttestation keybox XML files.

Supports three sub-commands:
  validate  Verify that a keybox.xml file is structurally valid.
  inspect   Print human-readable metadata for every key/certificate in the file.
  generate  Create a self-signed dummy keybox (for structural testing only).

Usage examples:
  python keybox_helper.py validate keybox.xml
  python keybox_helper.py inspect  keybox.xml
  python keybox_helper.py generate --device-id MY_DEVICE --out keybox_test.xml

Requirements:
  pip install cryptography
"""

import argparse
import datetime
import re
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Optional dependency – only required for 'inspect' and 'generate'
# ---------------------------------------------------------------------------
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding
    from cryptography.hazmat.primitives.asymmetric.ec import (
        EllipticCurvePrivateKey,
        SECP256R1,
    )
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    from cryptography.x509.oid import NameOID
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

REQUIRED_ROOT_TAG = "AndroidAttestation"
VALID_ALGORITHMS = {"ecdsa", "rsa"}
VALID_FORMATS = {"pem"}


def _load_tree(path: Path) -> ET.ElementTree:
    """Parse *path* as XML and return the ElementTree."""
    try:
        return ET.parse(str(path))
    except FileNotFoundError:
        _die(f"File not found: '{path}'")
    except ET.ParseError as exc:
        _die(f"XML parse error in '{path}': {exc}")


def _text_or_empty(element: Optional[ET.Element]) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _extract_pem_blocks(text: str) -> List[str]:
    """Return all PEM blocks found inside *text*."""
    pattern = r"(-----BEGIN [A-Z ]+-----[\s\S]+?-----END [A-Z ]+-----)"
    return re.findall(pattern, text)


def _die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def cmd_validate(path: Path) -> None:
    """Validate the structure of a keybox.xml file."""
    errors: List[str] = []
    warnings: List[str] = []

    tree = _load_tree(path)
    root = tree.getroot()

    if root.tag != REQUIRED_ROOT_TAG:
        errors.append(
            f"Root element must be <{REQUIRED_ROOT_TAG}>, got <{root.tag}>"
        )

    num_kb_el = root.find("NumberOfKeyboxes")
    if num_kb_el is None:
        errors.append("Missing <NumberOfKeyboxes> element")
        declared_count = 0
    else:
        try:
            declared_count = int(_text_or_empty(num_kb_el))
        except ValueError:
            errors.append(
                f"<NumberOfKeyboxes> is not an integer: '{_text_or_empty(num_kb_el)}'"
            )
            declared_count = 0

    keyboxes = root.findall("Keybox")
    actual_count = len(keyboxes)

    if declared_count != actual_count:
        errors.append(
            f"<NumberOfKeyboxes> says {declared_count} but found {actual_count} <Keybox> element(s)"
        )

    if actual_count == 0:
        errors.append("No <Keybox> elements found")

    for kb_idx, keybox in enumerate(keyboxes, start=1):
        device_id = keybox.get("DeviceID", "").strip()
        prefix = f"Keybox[{kb_idx}]"

        if not device_id:
            warnings.append(f"{prefix}: Missing or empty DeviceID attribute")

        keys = keybox.findall("Key")
        if not keys:
            errors.append(f"{prefix}: Contains no <Key> elements")

        algorithms_found = set()
        for k_idx, key_el in enumerate(keys, start=1):
            k_prefix = f"{prefix}.Key[{k_idx}]"
            algorithm = key_el.get("algorithm", "").lower()

            if algorithm not in VALID_ALGORITHMS:
                errors.append(
                    f"{k_prefix}: Invalid algorithm '{algorithm}' "
                    f"(expected one of: {', '.join(sorted(VALID_ALGORITHMS))})"
                )
            else:
                algorithms_found.add(algorithm)

            pk_el = key_el.find("PrivateKey")
            if pk_el is None:
                errors.append(f"{k_prefix}: Missing <PrivateKey> element")
            else:
                pk_format = pk_el.get("format", "").lower()
                if pk_format not in VALID_FORMATS:
                    errors.append(
                        f"{k_prefix}.PrivateKey: Invalid format '{pk_format}'"
                    )
                pk_text = _text_or_empty(pk_el)
                # Only check for PEM block if format is correct
                if pk_format == "pem":
                    blocks = _extract_pem_blocks(pk_text)
                    if not blocks:
                        warnings.append(
                            f"{k_prefix}.PrivateKey: No PEM block found (template placeholder?)"
                        )

            chain_el = key_el.find("CertificateChain")
            if chain_el is None:
                errors.append(f"{k_prefix}: Missing <CertificateChain> element")
                continue

            num_certs_el = chain_el.find("NumberOfCertificates")
            if num_certs_el is None:
                errors.append(
                    f"{k_prefix}.CertificateChain: Missing <NumberOfCertificates>"
                )
                declared_certs = 0
            else:
                try:
                    declared_certs = int(_text_or_empty(num_certs_el))
                except ValueError:
                    errors.append(
                        f"{k_prefix}.CertificateChain: "
                        f"<NumberOfCertificates> is not an integer"
                    )
                    declared_certs = 0

            certs = chain_el.findall("Certificate")
            if len(certs) != declared_certs:
                errors.append(
                    f"{k_prefix}.CertificateChain: declared {declared_certs} certs "
                    f"but found {len(certs)}"
                )

            for c_idx, cert_el in enumerate(certs, start=1):
                c_prefix = f"{k_prefix}.Certificate[{c_idx}]"
                cert_format = cert_el.get("format", "").lower()
                if cert_format not in VALID_FORMATS:
                    errors.append(
                        f"{c_prefix}: Invalid format '{cert_format}'"
                    )
                cert_text = _text_or_empty(cert_el)
                if cert_format == "pem":
                    blocks = _extract_pem_blocks(cert_text)
                    if not blocks:
                        warnings.append(
                            f"{c_prefix}: No PEM block found (template placeholder?)"
                        )

    # ---- report ----
    print(f"Validating: {path}")
    print(f"  Keyboxes : {actual_count}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠  {w}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  ✗  {e}")
        print("\nResult: INVALID")
        sys.exit(1)
    else:
        print("\nResult: VALID ✓")


# ---------------------------------------------------------------------------
# inspect
# ---------------------------------------------------------------------------

def cmd_inspect(path: Path) -> None:
    """Print metadata for all keys and certificates in a keybox.xml."""
    if not CRYPTOGRAPHY_AVAILABLE:
        _die(
            "'inspect' requires the 'cryptography' package.\n"
            "Install it with: pip install cryptography"
        )

    tree = _load_tree(path)
    root = tree.getroot()
    keyboxes = root.findall("Keybox")

    print(f"File      : {path}")
    print(f"Keyboxes  : {len(keyboxes)}\n")

    for kb_idx, keybox in enumerate(keyboxes, start=1):
        device_id = keybox.get("DeviceID", "<not set>")
        print(f"{'=' * 60}")
        print(f"Keybox {kb_idx}  DeviceID = {device_id}")
        print(f"{'=' * 60}")

        for k_idx, key_el in enumerate(keybox.findall("Key"), start=1):
            algorithm = key_el.get("algorithm", "?").upper()
            print(f"\n  Key {k_idx} – algorithm: {algorithm}")

            pk_el = key_el.find("PrivateKey")
            if pk_el is not None:
                pk_text = _text_or_empty(pk_el)
                blocks = _extract_pem_blocks(pk_text)
                if blocks:
                    _print_private_key_info(blocks[0], algorithm)
                else:
                    print("    PrivateKey : (no PEM block – template placeholder)")

            chain_el = key_el.find("CertificateChain")
            if chain_el is None:
                print("    CertificateChain: (missing)")
                continue

            certs = chain_el.findall("Certificate")
            labels = ["Leaf/device", "Intermediate CA", "Root CA"]
            for c_idx, cert_el in enumerate(certs):
                label = labels[c_idx] if c_idx < len(labels) else f"Cert {c_idx + 1}"
                cert_text = _text_or_empty(cert_el)
                blocks = _extract_pem_blocks(cert_text)
                if blocks:
                    print(f"\n    Certificate {c_idx + 1} ({label}):")
                    _print_cert_info(blocks[0])
                else:
                    print(
                        f"\n    Certificate {c_idx + 1} ({label}): "
                        "(no PEM block – template placeholder)"
                    )

    print()


def _print_private_key_info(pem: str, algorithm: str) -> None:
    try:
        key = serialization.load_pem_private_key(pem.encode(), password=None)
        if isinstance(key, EllipticCurvePrivateKey):
            print(f"    PrivateKey : EC curve={key.curve.name}, bits={key.key_size}")
        elif isinstance(key, RSAPrivateKey):
            print(f"    PrivateKey : RSA bits={key.key_size}")
        else:
            print(f"    PrivateKey : (unknown type)")
    except Exception as exc:
        print(f"    PrivateKey : (parse error: {exc})")


def _print_cert_info(pem: str) -> None:
    try:
        cert = x509.load_pem_x509_certificate(pem.encode())
        print(f"      Subject   : {cert.subject.rfc4514_string()}")
        print(f"      Issuer    : {cert.issuer.rfc4514_string()}")
        # not_valid_before_utc was added in cryptography 42.0.0; fall back for older versions
        try:
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc
        except AttributeError:
            not_before = cert.not_valid_before
            not_after = cert.not_valid_after
        print(f"      Valid from: {not_before}")
        print(f"      Valid to  : {not_after}")
        print(f"      Serial    : {cert.serial_number}")
    except Exception as exc:
        print(f"      (parse error: {exc})")


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def cmd_generate(device_id: str, out: Path) -> None:
    """Generate a self-signed dummy keybox XML (for structural testing only)."""
    if not CRYPTOGRAPHY_AVAILABLE:
        _die(
            "'generate' requires the 'cryptography' package.\n"
            "Install it with: pip install cryptography"
        )

    print(f"Generating dummy keybox for DeviceID='{device_id}' ...")

    ecdsa_pem_key, ecdsa_cert_pems = _make_ecdsa_chain(device_id)
    rsa_pem_key, rsa_cert_pems = _make_rsa_chain(device_id)

    xml_str = _build_keybox_xml(
        device_id=device_id,
        ecdsa_private_pem=ecdsa_pem_key,
        ecdsa_cert_pems=ecdsa_cert_pems,
        rsa_private_pem=rsa_pem_key,
        rsa_cert_pems=rsa_cert_pems,
    )

    out.write_text(xml_str, encoding="utf-8")
    print(f"Written to: {out}")
    print(
        "\nWARNING: This keybox uses self-signed certificates and is NOT valid\n"
        "for real hardware attestation. It is only useful for testing XML structure."
    )


def _make_subject(cn: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])


def _cert_builder(subject: x509.Name, issuer: x509.Name) -> x509.CertificateBuilder:
    now = datetime.datetime.now(datetime.timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
    )


def _make_ecdsa_chain(device_id: str):
    """Return (private_key_pem, [leaf_pem, intermediate_pem, root_pem])."""
    root_key = ec.generate_private_key(SECP256R1())
    root_name = _make_subject(f"Dummy ECDSA Root – {device_id}")
    root_cert = (
        _cert_builder(root_name, root_name)
        .public_key(root_key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(root_key, hashes.SHA256())
    )

    int_key = ec.generate_private_key(SECP256R1())
    int_name = _make_subject(f"Dummy ECDSA Intermediate – {device_id}")
    int_cert = (
        _cert_builder(int_name, root_name)
        .public_key(int_key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(root_key, hashes.SHA256())
    )

    leaf_key = ec.generate_private_key(SECP256R1())
    leaf_name = _make_subject(f"Dummy ECDSA Leaf – {device_id}")
    leaf_cert = (
        _cert_builder(leaf_name, int_name)
        .public_key(leaf_key.public_key())
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(int_key, hashes.SHA256())
    )

    def _to_pem_cert(c) -> str:
        return c.public_bytes(serialization.Encoding.PEM).decode()

    def _to_pem_key(k) -> str:
        return k.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode()

    return _to_pem_key(leaf_key), [
        _to_pem_cert(leaf_cert),
        _to_pem_cert(int_cert),
        _to_pem_cert(root_cert),
    ]


def _make_rsa_chain(device_id: str):
    """Return (private_key_pem, [leaf_pem, intermediate_pem, root_pem])."""
    root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    root_name = _make_subject(f"Dummy RSA Root – {device_id}")
    root_cert = (
        _cert_builder(root_name, root_name)
        .public_key(root_key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(root_key, hashes.SHA256())
    )

    int_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    int_name = _make_subject(f"Dummy RSA Intermediate – {device_id}")
    int_cert = (
        _cert_builder(int_name, root_name)
        .public_key(int_key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(root_key, hashes.SHA256())
    )

    leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    leaf_name = _make_subject(f"Dummy RSA Leaf – {device_id}")
    leaf_cert = (
        _cert_builder(leaf_name, int_name)
        .public_key(leaf_key.public_key())
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(int_key, hashes.SHA256())
    )

    def _to_pem_cert(c) -> str:
        return c.public_bytes(serialization.Encoding.PEM).decode()

    def _to_pem_key(k) -> str:
        return k.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode()

    return _to_pem_key(leaf_key), [
        _to_pem_cert(leaf_cert),
        _to_pem_cert(int_cert),
        _to_pem_cert(root_cert),
    ]


def _build_keybox_xml(
    device_id: str,
    ecdsa_private_pem: str,
    ecdsa_cert_pems: List[str],
    rsa_private_pem: str,
    rsa_cert_pems: List[str],
) -> str:
    def _indent(pem: str, spaces: int = 8) -> str:
        pad = " " * spaces
        return "\n".join(pad + line for line in pem.strip().splitlines())

    ecdsa_certs_xml = "\n".join(
        f"        <Certificate format=\"pem\">\n{_indent(p)}\n        </Certificate>"
        for p in ecdsa_cert_pems
    )
    rsa_certs_xml = "\n".join(
        f"        <Certificate format=\"pem\">\n{_indent(p)}\n        </Certificate>"
        for p in rsa_cert_pems
    )

    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!-- Generated by keybox_helper.py – DUMMY keybox for testing only -->
        <AndroidAttestation>

          <NumberOfKeyboxes>1</NumberOfKeyboxes>

          <Keybox DeviceID="{device_id}">

            <Key algorithm="ecdsa">
              <PrivateKey format="pem">
        {_indent(ecdsa_private_pem, 8)}
              </PrivateKey>
              <CertificateChain>
                <NumberOfCertificates>{len(ecdsa_cert_pems)}</NumberOfCertificates>
        {ecdsa_certs_xml}
              </CertificateChain>
            </Key>

            <Key algorithm="rsa">
              <PrivateKey format="pem">
        {_indent(rsa_private_pem, 8)}
              </PrivateKey>
              <CertificateChain>
                <NumberOfCertificates>{len(rsa_cert_pems)}</NumberOfCertificates>
        {rsa_certs_xml}
              </CertificateChain>
            </Key>

          </Keybox>

        </AndroidAttestation>
        """)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Utility for AndroidAttestation keybox XML files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # validate
    p_val = sub.add_parser("validate", help="Check structural validity of a keybox.xml")
    p_val.add_argument("file", type=Path, help="Path to keybox.xml")

    # inspect
    p_ins = sub.add_parser(
        "inspect", help="Print metadata for all keys/certificates in a keybox.xml"
    )
    p_ins.add_argument("file", type=Path, help="Path to keybox.xml")

    # generate
    p_gen = sub.add_parser(
        "generate",
        help="Generate a self-signed dummy keybox XML (for structural testing only)",
    )
    p_gen.add_argument(
        "--device-id",
        default="TEST_DEVICE",
        help="DeviceID attribute value (default: TEST_DEVICE)",
    )
    p_gen.add_argument(
        "--out",
        type=Path,
        default=Path("keybox_generated.xml"),
        help="Output file path (default: keybox_generated.xml)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "validate":
        if not args.file.exists():
            _die(f"File not found: {args.file}")
        cmd_validate(args.file)

    elif args.command == "inspect":
        if not args.file.exists():
            _die(f"File not found: {args.file}")
        cmd_inspect(args.file)

    elif args.command == "generate":
        cmd_generate(device_id=args.device_id, out=args.out)


if __name__ == "__main__":
    main()
