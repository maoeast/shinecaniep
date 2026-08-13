#!/usr/bin/env python3
"""Verify release artifact metadata for APK, AAB, or Windows EXE."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"error: {message}")


def version_key(path: Path) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", path.name))


def locate(name: str) -> str | None:
    sdk_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    sdk = Path(sdk_value).expanduser() if sdk_value else Path.home() / "android-sdk"
    build_tools = sdk / "build-tools"
    if build_tools.is_dir():
        for version in sorted(build_tools.iterdir(), key=version_key, reverse=True):
            candidate = version / name
            if candidate.is_file():
                return str(candidate)
    return shutil.which(name)


def run(command: list[str]) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        fail(f"command failed: {name_for_log(command)}\n{result.stdout[-1200:]}")
    return result.stdout


def name_for_log(command: list[str]) -> str:
    return " ".join(command)


def verify_apk(path: Path, args: argparse.Namespace) -> None:
    aapt = locate("aapt")
    if not aapt:
        fail("aapt is required for APK verification")
    badging = run([aapt, "dump", "badging", str(path)])
    package_match = re.search(r"^package: name='([^']+)'(?:\s+versionCode='[^']+')?\s+versionName='([^']+)'", badging, re.MULTILINE)
    label_match = re.search(r"^application-label:'([^']*)'", badging, re.MULTILINE)
    if not package_match:
        fail("could not read APK package metadata")
    package_id, version = package_match.groups()
    label = label_match.group(1) if label_match else ""
    checks = [("package id", args.package_id, package_id), ("version", args.version, version), ("application label", args.app_name, label)]
    for label_name, expected, actual in checks:
        if expected is not None and expected != actual:
            fail(f"{label_name} mismatch: expected {expected!r}, got {actual!r}")
    if args.expect_signed:
        apksigner = locate("apksigner")
        if not apksigner:
            fail("apksigner is required when --expect-signed is used")
        output = run([apksigner, "verify", "--verbose", "--print-certs", str(path)])
        if "Verifies" not in output and "Verification succesful" not in output and "Verification successful" not in output:
            fail("apksigner did not report successful verification")
        if "Verified using v2 scheme (APK Signature Scheme v2): true" not in output:
            fail("APK V2 signature is not verified")
        if args.cert_sha256 and args.cert_sha256.lower() not in output.lower():
            fail("signing certificate SHA-256 digest does not match")
    print(f"APK verified: package={package_id}, version={version}, label={label!r}, signed={args.expect_signed}")


def verify_aab(path: Path, args: argparse.Namespace) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile as exc:
        fail(f"invalid AAB: {exc}")
    if "base/manifest/AndroidManifest.xml" not in names:
        fail("AAB does not contain base/manifest/AndroidManifest.xml")
    print(f"AAB verified as a bundle archive: {path}")
    if args.package_id or args.version or args.app_name:
        print("warning: bundle metadata was not decoded; use bundletool or install-time verification for exact values")


def verify_exe(path: Path, args: argparse.Namespace) -> None:
    if path.suffix.lower() != ".exe":
        fail(f"expected an .exe artifact, got: {path}")
    if args.app_name and args.app_name not in path.name:
        print(f"warning: application name not present in EXE filename: {path.name}")
    print(f"EXE artifact exists: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--app-name")
    parser.add_argument("--package-id")
    parser.add_argument("--version")
    parser.add_argument("--expect-signed", action="store_true")
    parser.add_argument("--cert-sha256")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = args.artifact.expanduser().resolve()
    if not path.is_file():
        fail(f"artifact not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".apk":
        verify_apk(path, args)
    elif suffix == ".aab":
        verify_aab(path, args)
    elif suffix == ".exe":
        verify_exe(path, args)
    else:
        fail(f"unsupported artifact type: {suffix}")


if __name__ == "__main__":
    main()
