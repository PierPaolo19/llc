"""
test_keybox_helper.py – Unit tests for keybox_helper.py

Run with:
    pip install cryptography pytest
    pytest test_keybox_helper.py -v
"""
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

# Ensure the module under test is importable when running from the repo root.
sys.path.insert(0, str(Path(__file__).parent))

import keybox_helper as kh

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEMPLATE_PATH = Path(__file__).parent / "keybox.xml"


@pytest.fixture
def minimal_valid_xml(tmp_path):
    """A structurally valid keybox XML with placeholder (non-PEM) key material."""
    xml = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <AndroidAttestation>
          <NumberOfKeyboxes>1</NumberOfKeyboxes>
          <Keybox DeviceID="TEST_DEVICE">
            <Key algorithm="ecdsa">
              <PrivateKey format="pem">
                -----BEGIN EC PRIVATE KEY-----
                PLACEHOLDER
                -----END EC PRIVATE KEY-----
              </PrivateKey>
              <CertificateChain>
                <NumberOfCertificates>3</NumberOfCertificates>
                <Certificate format="pem">
                  -----BEGIN CERTIFICATE-----
                  PLACEHOLDER
                  -----END CERTIFICATE-----
                </Certificate>
                <Certificate format="pem">
                  -----BEGIN CERTIFICATE-----
                  PLACEHOLDER
                  -----END CERTIFICATE-----
                </Certificate>
                <Certificate format="pem">
                  -----BEGIN CERTIFICATE-----
                  PLACEHOLDER
                  -----END CERTIFICATE-----
                </Certificate>
              </CertificateChain>
            </Key>
          </Keybox>
        </AndroidAttestation>
        """)
    p = tmp_path / "valid_keybox.xml"
    p.write_text(xml)
    return p


@pytest.fixture
def wrong_root_xml(tmp_path):
    xml = "<WrongRoot><NumberOfKeyboxes>0</NumberOfKeyboxes></WrongRoot>"
    p = tmp_path / "wrong_root.xml"
    p.write_text(xml)
    return p


@pytest.fixture
def count_mismatch_xml(tmp_path):
    xml = textwrap.dedent("""\
        <AndroidAttestation>
          <NumberOfKeyboxes>2</NumberOfKeyboxes>
          <Keybox DeviceID="ONE">
            <Key algorithm="ecdsa">
              <PrivateKey format="pem">
                -----BEGIN EC PRIVATE KEY-----
                X
                -----END EC PRIVATE KEY-----
              </PrivateKey>
              <CertificateChain>
                <NumberOfCertificates>1</NumberOfCertificates>
                <Certificate format="pem">
                  -----BEGIN CERTIFICATE-----
                  X
                  -----END CERTIFICATE-----
                </Certificate>
              </CertificateChain>
            </Key>
          </Keybox>
        </AndroidAttestation>
        """)
    p = tmp_path / "count_mismatch.xml"
    p.write_text(xml)
    return p


@pytest.fixture
def invalid_algorithm_xml(tmp_path):
    xml = textwrap.dedent("""\
        <AndroidAttestation>
          <NumberOfKeyboxes>1</NumberOfKeyboxes>
          <Keybox DeviceID="TEST">
            <Key algorithm="dsa">
              <PrivateKey format="pem">
                -----BEGIN DSA PRIVATE KEY-----
                X
                -----END DSA PRIVATE KEY-----
              </PrivateKey>
              <CertificateChain>
                <NumberOfCertificates>1</NumberOfCertificates>
                <Certificate format="pem">
                  -----BEGIN CERTIFICATE-----
                  X
                  -----END CERTIFICATE-----
                </Certificate>
              </CertificateChain>
            </Key>
          </Keybox>
        </AndroidAttestation>
        """)
    p = tmp_path / "invalid_algorithm.xml"
    p.write_text(xml)
    return p


# ---------------------------------------------------------------------------
# Tests: _extract_pem_blocks
# ---------------------------------------------------------------------------

class TestExtractPemBlocks:
    def test_single_block(self):
        text = "-----BEGIN CERTIFICATE-----\nabc\n-----END CERTIFICATE-----"
        blocks = kh._extract_pem_blocks(text)
        assert len(blocks) == 1
        assert "BEGIN CERTIFICATE" in blocks[0]

    def test_multiple_blocks(self):
        text = (
            "-----BEGIN CERTIFICATE-----\na\n-----END CERTIFICATE-----\n"
            "-----BEGIN EC PRIVATE KEY-----\nb\n-----END EC PRIVATE KEY-----"
        )
        blocks = kh._extract_pem_blocks(text)
        assert len(blocks) == 2

    def test_no_blocks(self):
        assert kh._extract_pem_blocks("no pem here") == []

    def test_comment_placeholder(self):
        # Template uses XML comments, not real PEM blocks
        text = "<!-- -----BEGIN EC PRIVATE KEY----- ... -----END EC PRIVATE KEY----- -->"
        # Should still match (comment content is just text in XML)
        blocks = kh._extract_pem_blocks(text)
        assert len(blocks) == 1


# ---------------------------------------------------------------------------
# Tests: validate
# ---------------------------------------------------------------------------

class TestValidate:
    def test_valid_file_exits_0(self, minimal_valid_xml):
        # Should not raise SystemExit
        kh.cmd_validate(minimal_valid_xml)

    def test_wrong_root_exits_1(self, wrong_root_xml):
        with pytest.raises(SystemExit) as exc_info:
            kh.cmd_validate(wrong_root_xml)
        assert exc_info.value.code == 1

    def test_count_mismatch_exits_1(self, count_mismatch_xml):
        with pytest.raises(SystemExit) as exc_info:
            kh.cmd_validate(count_mismatch_xml)
        assert exc_info.value.code == 1

    def test_invalid_algorithm_exits_1(self, invalid_algorithm_xml):
        with pytest.raises(SystemExit) as exc_info:
            kh.cmd_validate(invalid_algorithm_xml)
        assert exc_info.value.code == 1

    def test_missing_file_exits_1(self, tmp_path):
        with pytest.raises(SystemExit):
            kh.cmd_validate(tmp_path / "nonexistent.xml")

    def test_template_file_is_structurally_valid(self):
        """The shipped keybox.xml template must pass structural validation."""
        # Template has placeholder PEM blocks so warnings are expected, but no errors.
        kh.cmd_validate(TEMPLATE_PATH)


# ---------------------------------------------------------------------------
# Tests: generate (requires cryptography)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not kh.CRYPTOGRAPHY_AVAILABLE,
    reason="cryptography package not installed",
)
class TestGenerate:
    def test_generate_creates_file(self, tmp_path):
        out = tmp_path / "test_keybox.xml"
        kh.cmd_generate(device_id="TEST_DEVICE", out=out)
        assert out.exists()

    def test_generated_file_is_valid_xml(self, tmp_path):
        out = tmp_path / "test_keybox.xml"
        kh.cmd_generate(device_id="TEST_DEVICE", out=out)
        tree = ET.parse(str(out))
        assert tree.getroot().tag == "AndroidAttestation"

    def test_generated_file_passes_validate(self, tmp_path):
        out = tmp_path / "test_keybox.xml"
        kh.cmd_generate(device_id="VALIDATE_ME", out=out)
        kh.cmd_validate(out)

    def test_generated_file_contains_device_id(self, tmp_path):
        out = tmp_path / "test_keybox.xml"
        kh.cmd_generate(device_id="MY_UNIQUE_ID", out=out)
        content = out.read_text()
        assert "MY_UNIQUE_ID" in content

    def test_generated_file_has_ecdsa_and_rsa(self, tmp_path):
        out = tmp_path / "test_keybox.xml"
        kh.cmd_generate(device_id="ALGO_TEST", out=out)
        tree = ET.parse(str(out))
        root = tree.getroot()
        keybox = root.find("Keybox")
        algorithms = {k.get("algorithm") for k in keybox.findall("Key")}
        assert "ecdsa" in algorithms
        assert "rsa" in algorithms

    def test_generated_file_certificate_chain_length(self, tmp_path):
        out = tmp_path / "test_keybox.xml"
        kh.cmd_generate(device_id="CHAIN_TEST", out=out)
        tree = ET.parse(str(out))
        root = tree.getroot()
        keybox = root.find("Keybox")
        for key_el in keybox.findall("Key"):
            chain = key_el.find("CertificateChain")
            certs = chain.findall("Certificate")
            assert len(certs) == 3, (
                f"Expected 3 certificates for {key_el.get('algorithm')} key, got {len(certs)}"
            )


# ---------------------------------------------------------------------------
# Tests: inspect (requires cryptography)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not kh.CRYPTOGRAPHY_AVAILABLE,
    reason="cryptography package not installed",
)
class TestInspect:
    def test_inspect_generated_file(self, tmp_path, capsys):
        out = tmp_path / "inspect_keybox.xml"
        kh.cmd_generate(device_id="INSPECT_TEST", out=out)
        kh.cmd_inspect(out)
        captured = capsys.readouterr()
        assert "INSPECT_TEST" in captured.out
        assert "ecdsa" in captured.out.lower() or "ec" in captured.out.lower()

    def test_inspect_template_shows_placeholders(self, capsys):
        kh.cmd_inspect(TEMPLATE_PATH)
        captured = capsys.readouterr()
        # Template has no real PEM data; should mention placeholder or "no PEM block"
        output_lower = captured.out.lower()
        assert "placeholder" in output_lower or "no pem block" in output_lower


# ---------------------------------------------------------------------------
# Tests: _build_keybox_xml
# ---------------------------------------------------------------------------

class TestBuildKeyboxXml:
    def test_device_id_in_output(self):
        xml = kh._build_keybox_xml(
            device_id="MY_ID",
            ecdsa_private_pem="-----BEGIN EC PRIVATE KEY-----\ntest\n-----END EC PRIVATE KEY-----",
            ecdsa_cert_pems=["-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"],
            rsa_private_pem="-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
            rsa_cert_pems=["-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"],
        )
        assert "MY_ID" in xml
        assert "<AndroidAttestation>" in xml
        assert 'algorithm="ecdsa"' in xml
        assert 'algorithm="rsa"' in xml

    def test_number_of_certificates_matches_actual(self):
        xml = kh._build_keybox_xml(
            device_id="COUNT_TEST",
            ecdsa_private_pem="-----BEGIN EC PRIVATE KEY-----\nx\n-----END EC PRIVATE KEY-----",
            ecdsa_cert_pems=[
                "-----BEGIN CERTIFICATE-----\na\n-----END CERTIFICATE-----",
                "-----BEGIN CERTIFICATE-----\nb\n-----END CERTIFICATE-----",
            ],
            rsa_private_pem="-----BEGIN RSA PRIVATE KEY-----\nx\n-----END RSA PRIVATE KEY-----",
            rsa_cert_pems=[
                "-----BEGIN CERTIFICATE-----\nc\n-----END CERTIFICATE-----",
            ],
        )
        root = ET.fromstring(xml)
        keybox = root.find("Keybox")
        for key_el in keybox.findall("Key"):
            chain = key_el.find("CertificateChain")
            declared = int(chain.find("NumberOfCertificates").text.strip())
            actual = len(chain.findall("Certificate"))
            assert declared == actual
