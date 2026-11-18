#!/usr/bin/env python3
"""Extract the two final ZIPs into an isolated smoke-test staging directory.

The extracted app is exactly what the workflow launches with Playwright; the
extracted extension is exactly what the host harness loads. Both app.asar hashes
are re-checked after extraction.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

import zip_safe

APP_NAME = "quick-interface-finder"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dest", required=True, type=Path)
    parser.add_argument("--expected-asar", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", args.version):
            raise zip_safe.ZipSafetyError(f"invalid version: {args.version!r}")
        output = args.output.resolve()
        dest = args.dest.resolve()
        name = f"{APP_NAME}-{args.version}"
        app_zip = output / f"{name}-app-windows-x64.zip"
        extension_zip = output / f"{name}-extension.zip"
        app_top = f"{name}-app"
        extension_top = name
        expected_asar = args.expected_asar.lower()

        app_destination = dest / "app"
        extension_destination = dest / "extension"
        for path in (app_destination, extension_destination):
            if path.exists():
                raise zip_safe.ZipSafetyError(f"smoke staging already exists: {path}")
        dest.mkdir(parents=True, exist_ok=True)

        zip_safe.inspect_zip(
            app_zip,
            expected_top=app_top,
            required=(f"{app_top}/快速找界面.exe", f"{app_top}/resources/app.asar"),
        )
        zip_safe.inspect_zip(
            extension_zip,
            expected_top=extension_top,
            required=(f"{extension_top}/extension.json", f"{extension_top}/resources/app.asar"),
        )
        app_root = zip_safe.extract_zip(app_zip, app_destination, app_top)
        extension_root = zip_safe.extract_zip(extension_zip, extension_destination, extension_top)
        app_asar = app_root / "resources" / "app.asar"
        extension_asar = extension_root / "resources" / "app.asar"
        exe = app_root / "快速找界面.exe"
        for path in (exe, app_asar, extension_asar, extension_root / "extension.json"):
            if not path.is_file():
                raise zip_safe.ZipSafetyError(f"smoke staging missing {path}")
        app_sha = zip_safe.file_sha256(app_asar)
        extension_sha = zip_safe.file_sha256(extension_asar)
        if app_sha != expected_asar or extension_sha != expected_asar:
            raise zip_safe.ZipSafetyError(
                f"staged app.asar mismatch: app={app_sha} extension={extension_sha} expected={expected_asar}"
            )
        report = {
            "ok": True,
            "version": args.version,
            "appRoot": str(app_root),
            "appExe": str(exe),
            "extensionRoot": str(extension_root),
            "extensionResources": str(extension_root / "resources"),
            "appAsarSha256": app_sha,
            "extensionAsarSha256": extension_sha,
        }
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (zip_safe.ZipSafetyError, zipfile.BadZipFile, OSError) as error:
        print(f"FINAL STAGING FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

