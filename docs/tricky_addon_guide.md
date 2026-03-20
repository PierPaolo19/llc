# Tricky Store – Custom Keybox XML Guide

## Table of contents

1. [Background](#background)
2. [What is a keybox?](#what-is-a-keybox)
3. [Keybox XML structure](#keybox-xml-structure)
4. [Prerequisites](#prerequisites)
5. [Deploying a custom keybox](#deploying-a-custom-keybox)
6. [Verifying attestation](#verifying-attestation)
7. [Using keybox_helper.py](#using-keybox_helperpy)
8. [Troubleshooting](#troubleshooting)

---

## Background

**Tricky Store** is a [Zygisk](https://github.com/topjohnwu/Magisk) addon that intercepts the Android KeyStore hardware-attestation flow and replaces the device's built-in attestation keys with keys supplied in a `keybox.xml` file.  This is useful for:

* Researching the Play Integrity / SafetyNet attestation chain.
* Testing custom attestation implementations on developer devices.
* Restoring attestation capability on devices whose factory keys have been revoked.

> **Important:** Using a third-party keybox on a device you do not own, or in a way that violates the terms of service of an application, may have legal and contractual consequences.  This guide is provided for educational and research purposes only.

---

## What is a keybox?

Android hardware attestation relies on a chain of cryptographic keys that is rooted in a certificate authority (CA) trusted by Google.  Each certified Android device ships with a unique *keybox* – a set of private keys and their matching certificate chains – stored in the Trusted Execution Environment (TEE) or StrongBox.

When an app requests hardware attestation, the KeyStore:

1. Generates an ephemeral key pair.
2. Signs the public key with the device attestation key from the keybox.
3. Returns the signed certificate chain all the way up to the Google root CA.

Tricky Store intercepts step 2 and uses the keys from `keybox.xml` instead.

---

## Keybox XML structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AndroidAttestation>

  <NumberOfKeyboxes>1</NumberOfKeyboxes>

  <Keybox DeviceID="UNIQUE_ID">

    <!-- ECDSA key (required for Android 14+ strong-box path) -->
    <Key algorithm="ecdsa">
      <PrivateKey format="pem">
        -----BEGIN EC PRIVATE KEY-----
        ...
        -----END EC PRIVATE KEY-----
      </PrivateKey>
      <CertificateChain>
        <NumberOfCertificates>3</NumberOfCertificates>
        <Certificate format="pem"><!-- leaf --></Certificate>
        <Certificate format="pem"><!-- intermediate --></Certificate>
        <Certificate format="pem"><!-- root --></Certificate>
      </CertificateChain>
    </Key>

    <!-- RSA key (required for Android ≤13 path) -->
    <Key algorithm="rsa">
      <PrivateKey format="pem">
        -----BEGIN RSA PRIVATE KEY-----
        ...
        -----END RSA PRIVATE KEY-----
      </PrivateKey>
      <CertificateChain>
        <NumberOfCertificates>3</NumberOfCertificates>
        <Certificate format="pem"><!-- leaf --></Certificate>
        <Certificate format="pem"><!-- intermediate --></Certificate>
        <Certificate format="pem"><!-- root --></Certificate>
      </CertificateChain>
    </Key>

  </Keybox>

</AndroidAttestation>
```

### Field reference

| Element / Attribute | Required | Description |
|---------------------|----------|-------------|
| `NumberOfKeyboxes` | Yes | Must equal the number of `<Keybox>` children |
| `Keybox@DeviceID` | Yes | Arbitrary unique string for this keybox entry |
| `Key@algorithm` | Yes | `ecdsa` or `rsa` |
| `PrivateKey@format` | Yes | Always `pem` |
| `NumberOfCertificates` | Yes | Must equal the number of `<Certificate>` children |
| `Certificate@format` | Yes | Always `pem` |
| Certificate order | – | Leaf → Intermediate → Root |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Rooted Android device | Magisk ≥ 24 or KernelSU |
| Zygisk enabled | Settings → Magisk → Enable Zygisk |
| Tricky Store module | Install the latest release from the [GitHub releases page](https://github.com/5ec1cff/TrickyStore/releases) |
| A valid `keybox.xml` | Must contain keys that chain to a recognised root CA |
| `adb` tooling | Android Platform Tools installed on your PC |

---

## Deploying a custom keybox

### Step 1 – Prepare the file

Validate your `keybox.xml` before copying it to the device:

```bash
python keybox_helper.py validate keybox.xml
```

A green **VALID ✓** result means the XML structure is correct.  Warnings about placeholder PEM blocks will appear if you are using the template without filling in real keys.

### Step 2 – Push to the device

```bash
# Ensure the target directory exists
adb shell "mkdir -p /data/adb/tricky_store"

# Copy the file
adb push keybox.xml /data/adb/tricky_store/keybox.xml

# Restrict permissions so only root can read it
adb shell "chmod 600 /data/adb/tricky_store/keybox.xml"
adb shell "chown root:root /data/adb/tricky_store/keybox.xml"
```

### Step 3 – Enable Tricky Store for target apps

Edit `/data/adb/tricky_store/target.txt` to list the package names of apps that should receive the custom attestation:

```
# /data/adb/tricky_store/target.txt
com.example.app
```

Use `*` to apply globally (not recommended – this affects all apps).

### Step 4 – Reboot

```bash
adb reboot
```

---

## Verifying attestation

After rebooting, use an attestation verification tool to confirm that the custom keybox is active:

```bash
# Install the AOSP attestation verifier (from Android SDK build-tools)
# or use a third-party app such as "Key Attestation Demo"
adb shell am start -n com.example.keyattestation/.MainActivity
```

Alternatively, run Play Integrity checks via the Google Play Integrity API on a test app.

---

## Using keybox_helper.py

### Installation

```bash
pip install cryptography
```

### validate

```bash
python keybox_helper.py validate keybox.xml
```

Checks:

* Correct root element (`AndroidAttestation`)
* `NumberOfKeyboxes` matches the actual count
* Each `Key` has a valid `algorithm`, a `PrivateKey`, and a `CertificateChain`
* `NumberOfCertificates` matches the actual count
* All PEM blocks are present (warns if placeholders are detected)

### inspect

```bash
python keybox_helper.py inspect keybox.xml
```

Prints human-readable metadata for every key and certificate (subject, issuer, validity period, serial number) **without ever printing private-key material**.

### generate

```bash
python keybox_helper.py generate --device-id MY_DEVICE_001 --out test_keybox.xml
```

Generates a self-signed keybox with fresh ECDSA P-256 and RSA-2048 key pairs.  The resulting file has a valid XML structure and can be used to test the `validate` and `inspect` commands, but the self-signed certificates will **not** pass real Play Integrity hardware-attestation checks.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Attestation fails after reboot | Invalid or expired certificates in keybox | Check certificate validity with `keybox_helper.py inspect` |
| Module not loaded | Zygisk disabled | Enable Zygisk in Magisk settings and reboot |
| File permission error | Wrong permissions on keybox.xml | `chmod 600 /data/adb/tricky_store/keybox.xml` |
| Only some apps use custom keybox | `target.txt` not configured | Add package names to `/data/adb/tricky_store/target.txt` |
| XML parse error | Malformed keybox.xml | Run `keybox_helper.py validate` to identify the issue |
