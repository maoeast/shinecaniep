#!/usr/bin/env python3
"""Zipalign, sign, and verify one Android APK without exposing passwords."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"error: {message}")


def version_key(path: Path) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", path.name))


def find_tool(sdk: Path, name: str) -> Path:
    candidates = []
    build_tools = sdk / "build-tools"
    if build_tools.is_dir():
        candidates.extend(version / name for version in sorted(build_tools.iterdir(), key=version_key, reverse=True) if version.is_dir())
    found = next((candidate for candidate in candidates if candidate.is_file()), None)
    if found:
        return found
    fallback = shutil.which(name)
    if fallback:
        return Path(fallback)
    fail(f"Android build tool not found: {name}")


def run(command: list[str], env: dict[str, str], label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        fail(f"{label} failed: {details[-1200:]}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--keystore", type=Path, required=True)
    parser.add_argument("--alias", required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_apk = args.input.expanduser().resolve()
    output_apk = args.output.expanduser().resolve()
    keystore = args.keystore.expanduser().resolve()
    if not input_apk.is_file():
        fail(f"input APK not found: {input_apk}")
    if not keystore.is_file():
        fail(f"keystore not found: {keystore}")
    if input_apk == output_apk:
        fail("input and output APK must be different")
    if output_apk.exists() and not args.force:
        fail(f"output already exists; choose another path or pass --force: {output_apk}")
    store_password = os.environ.get("KEYSTORE_PASSWORD")
    key_password = os.environ.get("KEY_PASSWORD") or store_password
    if not store_password:
        fail("KEYSTORE_PASSWORD environment variable is required")

    sdk_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    sdk = Path(sdk_value).expanduser() if sdk_value else Path.home() / "android-sdk"
    zipalign = find_tool(sdk, "zipalign")
    apksigner = find_tool(sdk, "apksigner")
    output_apk.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["KEYSTORE_PASSWORD"] = store_password
    env["KEY_PASSWORD"] = key_password or store_password

    with tempfile.TemporaryDirectory(prefix="apk-sign-") as temp_dir:
        aligned = Path(temp_dir) / "aligned.apk"
        run([str(zipalign), "-f", "4", str(input_apk), str(aligned)], env, "zipalign")
        run(
            [
                str(apksigner),
                "sign",
                "--ks",
                str(keystore),
                "--ks-key-alias",
                args.alias,
                "--ks-pass",
                "env:KEYSTORE_PASSWORD",
                "--key-pass",
                "env:KEY_PASSWORD",
                "--out",
                str(output_apk),
                str(aligned),
            ],
            env,
            "apksigner sign",
        )
    verify = run([str(apksigner), "verify", "--verbose", "--print-certs", str(output_apk)], env, "apksigner verify")
    if "Verified using v2 scheme (APK Signature Scheme v2): true" not in verify.stdout:
        fail("APK is not verified with APK Signature Scheme v2")
    idsig = Path(str(output_apk) + ".idsig")
    if idsig.exists():
        idsig.unlink()
    print(f"signed and verified: {output_apk}")


if __name__ == "__main__":
    main()
