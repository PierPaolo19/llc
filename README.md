# Tricky Addon – Custom Keybox XML

A toolkit for working with custom `keybox.xml` files used by the **Tricky Store** Zygisk module for Android hardware-attestation customisation.

## What is Tricky Store?

[Tricky Store](https://github.com/5ec1cff/TrickyStore) is a Zygisk addon for Magisk / KernelSU that modifies the Android hardware-attestation chain. When supplied with a valid `keybox.xml`, it can present custom attestation keys to apps that perform Play Integrity / SafetyNet hardware-attestation checks.

## What is a keybox?

A *keybox* (defined by the Android Keystore / Widevine spec) is an XML document that bundles:

* **One or more key pairs** (ECDSA and/or RSA) used to sign attestation certificates.
* The matching **certificate chain** (leaf → intermediate → root) that links each signing key to a recognised Google root.

The file follows the `AndroidAttestation` XML schema and is typically placed at `/data/adb/tricky_store/keybox.xml` on a rooted device.

## Repository contents

| Path | Description |
|------|-------------|
| `keybox.xml` | Annotated template showing the full `AndroidAttestation` schema with placeholder values |
| `keybox_helper.py` | Python utility – validate, inspect, and generate dummy keybox XML files |
| `docs/tricky_addon_guide.md` | Step-by-step guide for deploying a custom keybox with Tricky Store |

## Quick start

```bash
# Validate an existing keybox.xml
python keybox_helper.py validate keybox.xml

# Inspect key / certificate metadata without exposing private-key material
python keybox_helper.py inspect keybox.xml

# Generate a self-signed dummy keybox (for testing structure only – not for real attestation)
python keybox_helper.py generate --device-id MY_DEVICE --out keybox_test.xml
```

## Requirements

* Python 3.8+
* [`cryptography`](https://cryptography.io/) library  (`pip install cryptography`)

## Disclaimer

This project is intended for **educational and research purposes** on devices you own. Using a third-party keybox on a production device may violate the terms of service of certain applications. Always respect applicable laws and terms of service.