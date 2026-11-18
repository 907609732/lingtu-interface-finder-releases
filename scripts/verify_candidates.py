#!/usr/bin/env python3
"""Verify the two draft-release candidate ZIPs before any extraction.

Checks:
  * inputs-manifest.json SHA256 equals the workflow_dispatch input;
  * manifest schema, version, expected app.asar hash and both artifact hashes/sizes;
  * ZIP CRCs, member paths, duplicates, links, encryption and size limits;
  * candidate-app and candidate-extension share the same resources/app.asar;
  * extension.json lists every extension file and each one matches the app ZIP
    byte-for-byte (same source tree), including version/name/entry metadata.

Nothing is written outside the report path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import zip_safe

APP_NAME = "quick-interface-finder"
CANDIDATE_APP = "candidate-app.zip"
CANDIDATE_EXTENSION = "candidate-extension.zip"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_forbidden() -> tuple[re.Pattern[str], ...]:
    # Mirrors scripts/package_release.mjs; patterns are matched after the ZIP top
    # directory is removed so worker Python packages named "models" stay allowed.
    return (
        re.compile(r"(^|/)(bundled-model|server-data|user-data|profile|cache)(/|$)", re.I),
        re.compile(r"^(?:resources/)?models/", re.I),
        re.compile(r"\.(trt|safetensors)$", re.I),
        re.compile(r"\.sqlite(?:-wal|-shm)?$", re.I),
        re.compile(r"(^|/)\.release-packaging\.lock$", re.I),
    )


def extension_forbidden() -> tuple[re.Pattern[str], ...]:
    return relative_forbidden() + (
        re.compile(r"(^|/)(快速找界面|electron)\.exe$", re.I),
        re.compile(r"(^|/)locales/", re.I),
    )


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:  # noqa: BLE001 - report the original parser message
        raise VerificationError(f"inputs-manifest.json is not valid JSON: {error}") from error
    require(isinstance(data, dict), "inputs-manifest.json must be a JSON object")
    if "format" in data:
        require(data["format"] == 1, f"unsupported inputs-manifest format: {data['format']!r}")
    return data


def expected_asar(manifest: dict) -> str:
    value = manifest.get("appAsarSha256") or manifest.get("expectedAppAsarSha256")
    require(isinstance(value, str) and bool(SHA256.match(value.lower())),
            "manifest.appAsarSha256 (or expectedAppAsarSha256) must be a sha256 hex string")
    return value.lower()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        require(re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", args.version) is not None,
                f"invalid version: {args.version!r}")
        manifest_bytes = args.manifest.read_bytes()
        actual_manifest_sha = sha256_bytes(manifest_bytes)
        require(actual_manifest_sha == args.manifest_sha256.lower(),
                f"inputs-manifest.json sha256 mismatch: {actual_manifest_sha} != {args.manifest_sha256.lower()}")
        manifest = load_manifest(args.manifest)
        require(manifest.get("version") == args.version,
                f"manifest version {manifest.get('version')!r} does not match input {args.version!r}")
        asar_expected = expected_asar(manifest)

        artifacts = manifest.get("artifacts")
        require(isinstance(artifacts, list) and len(artifacts) == 2,
                "manifest.artifacts must contain exactly candidate-app.zip and candidate-extension.zip")
        by_name: dict[str, dict] = {}
        for item in artifacts:
            require(isinstance(item, dict), "each artifact must be an object")
            name = item.get("name")
            require(name in (CANDIDATE_APP, CANDIDATE_EXTENSION), f"unexpected artifact name: {name!r}")
            require(name not in by_name, f"duplicate artifact: {name}")
            digest = item.get("sha256")
            size = item.get("size")
            require(isinstance(digest, str) and bool(SHA256.match(digest.lower())),
                    f"artifact {name} sha256 must be 64 hex characters")
            require(isinstance(size, int) and not isinstance(size, bool) and size > 0,
                    f"artifact {name} size must be a positive integer")
            by_name[name] = {"name": name, "sha256": digest.lower(), "size": size}
        require(set(by_name) == {CANDIDATE_APP, CANDIDATE_EXTENSION},
                "manifest must list candidate-app.zip and candidate-extension.zip")

        app_zip = args.input_dir / CANDIDATE_APP
        extension_zip = args.input_dir / CANDIDATE_EXTENSION
        checked_artifacts = []
        for name, expected in by_name.items():
            path = args.input_dir / name
            require(path.is_file(), f"missing input artifact: {path}")
            actual_size = zip_safe.file_size(path)
            actual_sha = zip_safe.file_sha256(path)
            require(actual_size == expected["size"],
                    f"{name} size mismatch: {actual_size} != {expected['size']}")
            require(actual_sha == expected["sha256"],
                    f"{name} sha256 mismatch: {actual_sha} != {expected['sha256']}")
            checked_artifacts.append({**expected, "verified": True})

        app_top = f"{APP_NAME}-{args.version}-app"
        extension_top = f"{APP_NAME}-{args.version}"
        app_required = (f"{app_top}/快速找界面.exe", f"{app_top}/resources/app.asar")
        extension_required = (f"{extension_top}/extension.json", f"{extension_top}/resources/app.asar")
        app = zip_safe.inspect_zip(
            app_zip,
            expected_top=app_top,
            required=app_required,
            forbidden_relative=relative_forbidden(),
            verify_crc=True,
        )
        extension = zip_safe.inspect_zip(
            extension_zip,
            expected_top=extension_top,
            required=extension_required,
            forbidden_relative=extension_forbidden(),
            verify_crc=True,
        )

        app_asar = zip_safe.member_sha256(app_zip, f"{app_top}/resources/app.asar")
        extension_asar = zip_safe.member_sha256(extension_zip, f"{extension_top}/resources/app.asar")
        require(app_asar == asar_expected,
                f"candidate-app app.asar sha256 {app_asar} != manifest {asar_expected}")
        require(extension_asar == asar_expected,
                f"candidate-extension app.asar sha256 {extension_asar} != manifest {asar_expected}")

        manifest_bytes_extension = zip_safe.read_member(extension_zip, f"{extension_top}/extension.json")
        try:
            extension_manifest = json.loads(manifest_bytes_extension.decode("utf-8-sig"))
        except Exception as error:  # noqa: BLE001
            raise VerificationError(f"extension.json is not valid JSON: {error}") from error
        require(extension_manifest.get("format") == 1, "extension.json format must be 1")
        require(extension_manifest.get("id") == APP_NAME, f"extension id must be {APP_NAME}")
        require(extension_manifest.get("name") == "快速找界面", "extension name must be 快速找界面")
        require(extension_manifest.get("version") == args.version,
                f"extension version {extension_manifest.get('version')!r} != {args.version!r}")
        require(extension_manifest.get("hostApi") == 1, "extension hostApi must be 1")
        require(extension_manifest.get("entry") == "resources/app.asar/desktop/main.cjs",
                "extension entry must be resources/app.asar/desktop/main.cjs")
        require(extension_manifest.get("platform") == "win32", "extension platform must be win32")
        require(extension_manifest.get("arch") == "x64", "extension arch must be x64")

        listed = extension_manifest.get("files")
        require(isinstance(listed, list) and listed, "extension.json files must be a non-empty array")
        app_names = set(app["files"])
        extension_names = set(extension["files"])

        def hash_member(handle: zipfile.ZipFile, name: str) -> str:
            digest = hashlib.sha256()
            with handle.open(name) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            return digest.hexdigest()

        seen: set[str] = set()
        checked_files = 0
        with zipfile.ZipFile(app_zip) as app_zf, zipfile.ZipFile(extension_zip) as ext_zf:
            for item in listed:
                require(isinstance(item, dict), "extension.json file entry must be an object")
                relative = item.get("path")
                size = item.get("size")
                digest = item.get("sha256")
                require(isinstance(relative, str) and relative, "extension file path missing")
                zip_safe.safe_member_name(relative)
                require(not relative.startswith("/"), f"absolute extension file path: {relative}")
                require(relative not in seen, f"duplicate extension file entry: {relative}")
                seen.add(relative)
                require(isinstance(size, int) and size >= 0, f"invalid size for {relative}")
                require(isinstance(digest, str) and bool(SHA256.match(digest.lower())),
                        f"invalid sha256 for {relative}")
                app_member = f"{app_top}/{relative}"
                extension_member = f"{extension_top}/{relative}"
                require(app_member in app_names, f"extension file missing from candidate-app: {relative}")
                require(extension_member in extension_names, f"extension file missing from candidate-extension: {relative}")
                app_info = app_zf.getinfo(app_member)
                ext_info = ext_zf.getinfo(extension_member)
                require(app_info.file_size == size, f"candidate-app size mismatch for {relative}")
                require(ext_info.file_size == size, f"candidate-extension size mismatch for {relative}")
                app_hash = hash_member(app_zf, app_member)
                extension_hash = hash_member(ext_zf, extension_member)
                require(app_hash == digest.lower(), f"candidate-app sha256 mismatch for {relative}")
                require(extension_hash == digest.lower(), f"candidate-extension sha256 mismatch for {relative}")
                checked_files += 1

        require("resources/app.asar" in seen, "extension.json must list resources/app.asar")
        extension_relative = {member[len(extension_top) + 1:] for member in extension["files"]}
        require(seen | {"extension.json"} == extension_relative,
                "extension.json file list does not match the candidate-extension contents")
        require(app["top"] == app_top, "candidate-app top directory mismatch")
        require(extension["top"] == extension_top, "candidate-extension top directory mismatch")
        require("快速找界面.exe" not in seen, "extension.json must not contain the desktop EXE")

        report = {
            "ok": True,
            "version": args.version,
            "manifestSha256": actual_manifest_sha,
            "appAsarSha256": asar_expected,
            "artifacts": sorted(checked_artifacts, key=lambda item: item["name"]),
            "candidateApp": {key: app[key] for key in ("top", "fileCount", "bytes", "uncompressedBytes", "sha256")},
            "candidateExtension": {key: extension[key] for key in ("top", "fileCount", "bytes", "uncompressedBytes", "sha256")},
            "extensionManifestFiles": checked_files,
            "sameSourceVerified": True,
            "crcVerified": True,
            "pathSafetyVerified": True,
        }
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (VerificationError, zip_safe.ZipSafetyError, zipfile.BadZipFile, OSError, json.JSONDecodeError) as error:
        print(f"CANDIDATE VERIFICATION FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

