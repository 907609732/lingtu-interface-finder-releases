#!/usr/bin/env python3
"""Extract the verified candidate-app.zip into build/win-unpacked.

The candidate is never renamed into a final deliverable: it only provides the
already compiled win-unpacked tree that the existing packaging scripts reuse.
Member paths are re-validated here even though verify_candidates.py ran first.
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
    parser.add_argument("--app-zip", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dest", required=True, type=Path)
    parser.add_argument("--expected-asar", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", args.version):
            raise zip_safe.ZipSafetyError(f"invalid version: {args.version!r}")
        expected_top = f"{APP_NAME}-{args.version}-app"
        dest = args.dest.resolve()
        if dest.exists():
            raise zip_safe.ZipSafetyError(f"build destination already exists: {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        staging = dest.parent / (dest.name + "-extract")
        if staging.exists():
            raise zip_safe.ZipSafetyError(f"staging destination already exists: {staging}")

        info = zip_safe.inspect_zip(
            args.app_zip,
            expected_top=expected_top,
            required=(f"{expected_top}/快速找界面.exe", f"{expected_top}/resources/app.asar"),
            verify_crc=True,
        )
        extracted = zip_safe.extract_zip(args.app_zip, staging, expected_top)
        destination = extracted.rename(dest)
        asar = destination / "resources" / "app.asar"
        exe = destination / "快速找界面.exe"
        if not exe.is_file():
            raise zip_safe.ZipSafetyError("packaged EXE missing after extraction")
        asar_sha = zip_safe.file_sha256(asar)
        if asar_sha != args.expected_asar.lower():
            raise zip_safe.ZipSafetyError(f"extracted app.asar sha256 mismatch: {asar_sha}")
        report = {
            "ok": True,
            "sourceZip": str(args.app_zip),
            "buildDir": str(destination),
            "exe": str(exe),
            "appAsarSha256": asar_sha,
            "crcVerified": True,
            "zip": {key: info[key] for key in ("top", "fileCount", "bytes", "sha256")},
        }
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (zip_safe.ZipSafetyError, zipfile.BadZipFile, OSError) as error:
        print(f"CANDIDATE STAGING FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

