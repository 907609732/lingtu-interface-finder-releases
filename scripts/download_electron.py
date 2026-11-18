#!/usr/bin/env python3
"""Download the fixed official Electron runtime and verify its SHASUMS256 entry.

Only github.com/electron/electron release assets are read. Nothing is installed
through npm and no application dependency is pulled in.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import zip_safe

BASE = "https://github.com/electron/electron/releases/download"
SHA_LINE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+)$")


class DownloadError(RuntimeError):
    pass


def fetch(url: str, destination: Path, attempts: int = 3) -> None:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "qif-release-ci"})
            with urllib.request.urlopen(request, timeout=120) as response, open(destination, "wb") as sink:
                if response.status != 200:
                    raise DownloadError(f"HTTP {response.status} for {url}")
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    sink.write(chunk)
            return
        except Exception as error:  # noqa: BLE001 - retry network/HTTP failures
            last_error = error
            if attempt < attempts:
                time.sleep(5 * attempt)
    raise DownloadError(f"download failed after {attempts} attempts: {url}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="44.7.0")
    parser.add_argument("--dest", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
            raise DownloadError(f"invalid Electron version: {args.version!r}")
        asset = f"electron-v{args.version}-win32-x64.zip"
        base = f"{BASE}/v{args.version}"
        dest = args.dest.resolve()
        dest.mkdir(parents=True, exist_ok=True)
        sums_file = dest / "SHASUMS256.txt"
        archive = dest / asset
        fetch(f"{base}/SHASUMS256.txt", sums_file)
        expected: str | None = None
        for line in sums_file.read_text(encoding="utf-8").splitlines():
            match = SHA_LINE.match(line.strip())
            if match and match.group(2) == asset:
                expected = match.group(1).lower()
                break
        if not expected:
            raise DownloadError(f"{asset} is not listed in SHASUMS256.txt")
        fetch(f"{base}/{asset}", archive)
        actual = zip_safe.file_sha256(archive)
        if actual != expected:
            raise DownloadError(f"{asset} sha256 mismatch: {actual} != {expected}")
        runtime = dest / f"electron-v{args.version}-win32-x64"
        if runtime.exists():
            raise DownloadError(f"Electron extraction target already exists: {runtime}")
        with zipfile.ZipFile(archive) as zf:
            bad = zf.testzip()
            if bad is not None:
                raise DownloadError(f"Electron ZIP CRC failed: {bad}")
            for info in zf.infolist():
                name = info.filename
                zip_safe.safe_member_name(name)
                target = runtime.joinpath(*name.split("/"))
                normal_runtime = str(runtime.resolve())
                normal_target = str(target.resolve())
                if not (normal_target == normal_runtime or normal_target.startswith(normal_runtime + "\\")
                        or normal_target.startswith(normal_runtime + "/")):
                    raise DownloadError(f"Electron ZIP path escape: {name}")
                if name.endswith("/"):
                    zip_safe.ensure_dir(target)
                    continue
                zip_safe.ensure_dir(target.parent)
                with zf.open(info) as source, zip_safe.open_write(target) as sink:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        sink.write(chunk)
        electron = runtime / "electron.exe"
        if not electron.is_file():
            raise DownloadError("electron.exe missing after extraction")
        report = {
            "ok": True,
            "version": args.version,
            "asset": asset,
            "sha256": actual,
            "sumsFile": str(sums_file),
            "electronExe": str(electron),
            "zipBytes": zip_safe.file_size(archive),
        }
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (DownloadError, zip_safe.ZipSafetyError, zipfile.BadZipFile, OSError) as error:
        print(f"ELECTRON DOWNLOAD FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

