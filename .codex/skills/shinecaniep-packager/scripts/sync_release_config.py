#!/usr/bin/env python3
"""Synchronize confirmed release metadata across the shinecaniep project."""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import shutil
import sys
from html import escape as xml_escape
from pathlib import Path


PACKAGE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"error: {message}")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected an object in {path}")
    return value


def save_json(path: Path, value: dict, dry_run: bool) -> None:
    if not dry_run:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_required(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    result, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        fail(f"could not update {label}")
    return result


def update_cargo(root: Path, app_name: str, version: str, dry_run: bool) -> None:
    cargo_path = root / "src-tauri" / "Cargo.toml"
    cargo = cargo_path.read_text(encoding="utf-8")
    old_name_match = re.search(r'^name\s*=\s*"([^"]+)"', cargo, flags=re.MULTILINE)
    if not old_name_match:
        fail(f"could not find Cargo package name in {cargo_path}")
    old_name = old_name_match.group(1)
    cargo = replace_required(cargo, r'^name\s*=\s*"[^"]+"', f'name = "{app_name}"', "Cargo package name", re.MULTILINE)
    cargo = replace_required(cargo, r'^version\s*=\s*"[^"]+"', f'version = "{version}"', "Cargo package version", re.MULTILINE)
    cargo = replace_required(cargo, r'^description\s*=\s*"[^"]*"', f'description = "{app_name}"', "Cargo description", re.MULTILINE)
    if not dry_run:
        cargo_path.write_text(cargo, encoding="utf-8")

    lock_path = root / "src-tauri" / "Cargo.lock"
    if not lock_path.exists():
        return
    lock = lock_path.read_text(encoding="utf-8")
    block_pattern = re.compile(
        r'(?ms)(^\[\[package\]\]\nname\s*=\s*")'
        + re.escape(old_name)
        + r'("\nversion\s*=\s*")[^"]+(")'
    )
    lock, count = block_pattern.subn(rf'\g<1>{app_name}\g<2>{version}\g<3>', lock, count=1)
    if count != 1:
        fail(f"could not find the root package {old_name!r} in {lock_path}")
    if not dry_run:
        lock_path.write_text(lock, encoding="utf-8")


def update_window_title(root: Path, app_name: str, dry_run: bool) -> None:
    path = root / "src-tauri" / "src" / "lib.rs"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    updated = replace_required(
        text,
        r'(\.title\(")[^"]*("\)\s*\.resizable\(true\))',
        rf'\g<1>{app_name}\g<2>',
        "native window title",
    )
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def update_page_files(root: Path, system_name: str, system_name_en: str, company: str, dry_run: bool) -> None:
    config_path = root / "dist" / "config.json"
    config = load_json(config_path)
    config["systemName"] = system_name
    config["systemNameEn"] = system_name_en
    config["copyright"] = company
    save_json(config_path, config, dry_run)

    dist_index = root / "dist" / "index.html"
    html = dist_index.read_text(encoding="utf-8")
    html = replace_required(html, r"<title>[^<]*</title>", f"<title>{system_name}</title>", "dist page title")
    default_config = re.compile(r"(const defaultConfig\s*=\s*\{.*?\bsystemName:\s*)\"[^\"]*\"", re.DOTALL)
    html, count = default_config.subn(rf'\g<1>"{system_name}"', html, count=1)
    if count != 1:
        fail("could not update dist default system name")
    if not dry_run:
        dist_index.write_text(html, encoding="utf-8")
        (root / "index.html").write_text(html, encoding="utf-8")


def update_strings(root: Path, app_name: str, dry_run: bool) -> None:
    path = root / "src-tauri" / "gen" / "android" / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    if not path.exists():
        return
    value = xml_escape(app_name, quote=False)
    text = path.read_text(encoding="utf-8")
    text = replace_required(text, r'(<string name="app_name">)[^<]*(</string>)', rf'\g<1>{value}\g<2>', "Android app_name")
    text = replace_required(text, r'(<string name="main_activity_title">)[^<]*(</string>)', rf'\g<1>{value}\g<2>', "Android activity title")
    if not dry_run:
        path.write_text(text, encoding="utf-8")


def update_android_package(root: Path, package_id: str, dry_run: bool) -> None:
    android_root = root / "src-tauri" / "gen" / "android"
    gradle_path = android_root / "app" / "build.gradle.kts"
    if not gradle_path.exists():
        return
    gradle = gradle_path.read_text(encoding="utf-8")
    namespace_match = re.search(r'namespace\s*=\s*"([^"]+)"', gradle)
    application_match = re.search(r'applicationId\s*=\s*"([^"]+)"', gradle)
    old_package = (application_match or namespace_match).group(1) if (application_match or namespace_match) else ""
    if not old_package:
        fail(f"could not determine the existing Android package from {gradle_path}")
    gradle = replace_required(gradle, r'namespace\s*=\s*"[^"]+"', f'namespace = "{package_id}"', "Android namespace")
    gradle = replace_required(gradle, r'applicationId\s*=\s*"[^"]+"', f'applicationId = "{package_id}"', "Android applicationId")
    if not dry_run:
        gradle_path.write_text(gradle, encoding="utf-8")

    java_root = android_root / "app" / "src" / "main" / "java"
    old_dir = java_root.joinpath(*old_package.split("."))
    new_dir = java_root.joinpath(*package_id.split("."))
    if old_package != package_id:
        if new_dir.exists() and new_dir.resolve() != old_dir.resolve():
            if any(new_dir.iterdir()):
                fail(f"target Android package directory is not empty: {new_dir}")
        if old_dir.exists() and not dry_run:
            new_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_dir), str(new_dir))
        elif not old_dir.exists() and not new_dir.exists():
            fail(f"existing Android package directory not found: {old_dir}")

    if new_dir.exists():
        for path in new_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if old_package in text:
                updated = text.replace(old_package, package_id)
                if not dry_run:
                    path.write_text(updated, encoding="utf-8")

    asset_config = android_root / "app" / "src" / "main" / "assets" / "tauri.conf.json"
    if asset_config.exists():
        config = load_json(asset_config)
        config["identifier"] = package_id
        save_json(asset_config, config, dry_run)


def update_tauri(root: Path, app_name: str, package_id: str, version: str, company: str, dry_run: bool) -> None:
    path = root / "src-tauri" / "tauri.conf.json"
    config = load_json(path)
    config["productName"] = app_name
    config["identifier"] = package_id
    config["version"] = version
    config.setdefault("bundle", {})["copyright"] = company
    save_json(path, config, dry_run)


def update_logo(root: Path, logo_path: str | None, dry_run: bool) -> None:
    if not logo_path:
        return
    source = Path(logo_path).expanduser().resolve()
    if not source.is_file():
        fail(f"logo file not found: {source}")
    try:
        from PIL import Image
    except ImportError:
        fail("Pillow is required when --logo-path is used")
    image = Image.open(source).convert("RGBA")
    max_size = 512
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        image = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    config_path = root / "dist" / "config.json"
    config = load_json(config_path)
    config["logoUrl"] = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    save_json(config_path, config, dry_run)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--app-name", required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--system-name", required=True)
    parser.add_argument("--system-name-en", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--logo-path")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    if not root.is_dir():
        fail(f"project root not found: {root}")
    if not PACKAGE_ID_RE.fullmatch(args.package_id):
        fail(f"invalid Android package identifier: {args.package_id}")
    for field, value in (("app name", args.app_name), ("system name", args.system_name), ("English name", args.system_name_en), ("company", args.company)):
        if not value.strip() or any(char in value for char in "\r\n\x00"):
            fail(f"invalid {field}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        fail(f"version must match x.y.z: {args.version}")

    update_tauri(root, args.app_name, args.package_id, args.version, args.company, args.dry_run)
    update_cargo(root, args.app_name, args.version, args.dry_run)
    update_window_title(root, args.app_name, args.dry_run)
    update_page_files(root, args.system_name, args.system_name_en, args.company, args.dry_run)
    update_strings(root, args.app_name, args.dry_run)
    update_android_package(root, args.package_id, args.dry_run)
    update_logo(root, args.logo_path, args.dry_run)
    print("dry-run complete" if args.dry_run else "release configuration synchronized")


if __name__ == "__main__":
    main()
