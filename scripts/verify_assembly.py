#!/usr/bin/env python3
"""Verify the final assembled dual-edition output.

This is the independent post-assembly gate: it re-checks both final ZIPs, the
extension manifest against the extracted win-unpacked resources and against the
app ZIP, the identity of app.asar across both editions, SHA256SUMS.txt, the
delivery descriptors and the unpacked extension staging directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import zip_safe

APP_NAME = "quick-interface-finder"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def app_forbidden() -> tuple[re.Pattern[str], ...]:
    return (
        re.compile(r"(^|/)(bundled-model|server-data|user-data|profile|cache)(/|$)", re.I),
        re.compile(r"^(?:resources/)?models/", re.I),
        re.compile(r"\.(trt|safetensors)$", re.I),
        re.compile(r"\.sqlite(?:-wal|-shm)?$", re.I),
        re.compile(r"(^|/)\.release-packaging\.lock$", re.I),
    )


def extension_forbidden() -> tuple[re.Pattern[str], ...]:
    return app_forbidden() + (
        re.compile(r"(^|/)(快速找界面|electron)\.exe$", re.I),
        re.compile(r"(^|/)locales/", re.I),
    )


def hash_member(handle: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with handle.open(name) as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--build-dir", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--expected-asar", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        require(re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", args.version) is not None,
                f"invalid version: {args.version!r}")
        output = args.output.resolve()
        build = args.build_dir.resolve()
        name = f"{APP_NAME}-{args.version}"
        app_zip = output / f"{name}-app-windows-x64.zip"
        extension_zip = output / f"{name}-extension.zip"
        app_top = f"{name}-app"
        extension_top = name
        expected_asar = args.expected_asar.lower()
        require(SHA256.match(expected_asar) is not None, "expected app.asar hash must be sha256")

        expected_entries = {
            name, app_zip.name, extension_zip.name,
            "app-delivery.json", "extension-delivery.json",
            "SHA256SUMS.txt", "release-manifest.json", "版本选择.md",
        }
        require(output.is_dir(), f"output directory missing: {output}")
        actual_entries = {entry.name for entry in output.iterdir()}
        unexpected = actual_entries - expected_entries
        missing = expected_entries - actual_entries
        require(not missing, f"assembled output is missing: {sorted(missing)}")
        require(not unexpected, f"unexpected files in assembled output: {sorted(unexpected)}")
        for entry in output.iterdir():
            if entry.is_dir():
                require(entry.name == name, f"unexpected output directory: {entry.name}")
                require(not entry.is_symlink(), f"symlink in assembled output: {entry.name}")

        for required_file in (app_zip, extension_zip, output / "app-delivery.json",
                              output / "extension-delivery.json", output / "SHA256SUMS.txt",
                              output / "release-manifest.json", output / "版本选择.md"):
            require(required_file.is_file(), f"assembled file missing: {required_file}")

        app_delivery = json.loads((output / "app-delivery.json").read_text(encoding="utf-8-sig"))
        extension_delivery = json.loads((output / "extension-delivery.json").read_text(encoding="utf-8-sig"))
        release_manifest = json.loads((output / "release-manifest.json").read_text(encoding="utf-8-sig"))
        require(release_manifest.get("format") == 1, "release-manifest format must be 1")
        require(release_manifest.get("kind") == "dual-edition-release", "release-manifest kind must be dual-edition-release")
        require(release_manifest.get("version") == args.version, "release-manifest version mismatch")
        require(release_manifest.get("sharedResourcesVerified") is True, "release-manifest sharedResourcesVerified must be true")
        require(release_manifest.get("notAutoUpdateManifest") is True, "release-manifest must not be an auto-update manifest")
        require(release_manifest.get("appAsarSha256") == expected_asar, "release-manifest appAsarSha256 mismatch")
        require(isinstance(release_manifest.get("artifacts"), list) and len(release_manifest["artifacts"]) == 2,
                "release-manifest must contain two artifacts")
        editions = {item.get("edition"): item for item in release_manifest["artifacts"] if isinstance(item, dict)}
        require(set(editions) == {"extension", "standalone-full"}, "release-manifest editions mismatch")

        for label, delivery in (("app-delivery.json", app_delivery), ("extension-delivery.json", extension_delivery)):
            require(delivery.get("id") == APP_NAME, f"{label} id mismatch")
            require(delivery.get("version") == args.version, f"{label} version mismatch")
        require(extension_delivery.get("format") == 1, "extension-delivery.json format mismatch")

        require(app_delivery.get("zip") == app_zip.name, "app-delivery zip name mismatch")
        require(extension_delivery.get("zip") == extension_zip.name, "extension-delivery zip name mismatch")
        require(app_delivery.get("appAsarSha256") == expected_asar, "app-delivery appAsarSha256 mismatch")
        require(editions["extension"].get("appAsarSha256") == expected_asar,
                "release-manifest extension appAsarSha256 mismatch")
        require(editions["standalone-full"].get("appAsarSha256") == expected_asar,
                "release-manifest standalone appAsarSha256 mismatch")
        require(app_delivery.get("bundledElectron") is True and app_delivery.get("bundledModels") is False,
                "app-delivery bundled flags mismatch")
        require(app_delivery.get("crcVerified") is True, "app-delivery must record CRC verification")
        require(editions["standalone-full"].get("crcVerified") is True, "release-manifest app CRC flag missing")
        require(editions["extension"].get("crcVerified") is True, "release-manifest extension CRC flag missing")
        require(extension_delivery.get("noBundledElectron") is True and extension_delivery.get("noBundledModels") is True,
                "extension-delivery bundled flags mismatch")

        app_size = zip_safe.file_size(app_zip)
        extension_size = zip_safe.file_size(extension_zip)
        app_sha = zip_safe.file_sha256(app_zip)
        extension_sha = zip_safe.file_sha256(extension_zip)
        require(app_delivery.get("zipBytes") == app_size, "app-delivery zipBytes mismatch")
        require(extension_delivery.get("zipBytes") == extension_size, "extension-delivery zipBytes mismatch")
        require(app_delivery.get("sha256") == app_sha, "app-delivery sha256 mismatch")
        require(extension_delivery.get("sha256") == extension_sha, "extension-delivery sha256 mismatch")
        require(editions["standalone-full"].get("sha256") == app_sha, "release-manifest app sha256 mismatch")
        require(editions["extension"].get("sha256") == extension_sha, "release-manifest extension sha256 mismatch")

        sums_text = (output / "SHA256SUMS.txt").read_text(encoding="utf-8-sig").strip().splitlines()
        sums = {}
        for line in sums_text:
            match = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line.strip())
            require(match is not None, f"invalid SHA256SUMS line: {line!r}")
            sums[match.group(2)] = match.group(1).lower()
        require(sums == {app_zip.name: app_sha, extension_zip.name: extension_sha},
                "SHA256SUMS.txt does not match the two final archives")

        app = zip_safe.inspect_zip(
            app_zip,
            expected_top=app_top,
            required=(f"{app_top}/快速找界面.exe", f"{app_top}/resources/app.asar"),
            forbidden_relative=app_forbidden(),
            verify_crc=True,
        )
        extension = zip_safe.inspect_zip(
            extension_zip,
            expected_top=extension_top,
            required=(f"{extension_top}/extension.json", f"{extension_top}/resources/app.asar"),
            forbidden_relative=extension_forbidden(),
            verify_crc=True,
        )

        app_asar = zip_safe.member_sha256(app_zip, f"{app_top}/resources/app.asar")
        extension_asar = zip_safe.member_sha256(extension_zip, f"{extension_top}/resources/app.asar")
        build_asar = build / "resources" / "app.asar"
        require(build_asar.is_file(), f"build resources missing: {build_asar}")
        build_asar_sha = zip_safe.file_sha256(build_asar)
        require(app_asar == expected_asar, f"final app.asar sha256 {app_asar} != expected {expected_asar}")
        require(extension_asar == expected_asar, f"final extension app.asar sha256 {extension_asar} != expected")
        require(build_asar_sha == expected_asar, f"build app.asar sha256 {build_asar_sha} != expected")

        extension_manifest_bytes = zip_safe.read_member(extension_zip, f"{extension_top}/extension.json")
        extension_manifest = json.loads(extension_manifest_bytes.decode("utf-8-sig"))
        require(extension_manifest.get("format") == 1, "final extension.json format must be 1")
        require(extension_manifest.get("id") == APP_NAME, "final extension id mismatch")
        require(extension_manifest.get("name") == "快速找界面", "final extension name mismatch")
        require(extension_manifest.get("version") == args.version, "final extension version mismatch")
        require(extension_manifest.get("hostApi") == 1, "final extension hostApi mismatch")
        require(extension_manifest.get("entry") == "resources/app.asar/desktop/main.cjs", "final extension entry mismatch")
        require(extension_manifest.get("platform") == "win32", "final extension platform mismatch")
        require(extension_manifest.get("arch") == "x64", "final extension arch mismatch")

        listed = extension_manifest.get("files")
        require(isinstance(listed, list) and listed, "final extension.json files must be a non-empty array")
        build_root = os.path.abspath(build)
        build_resources = build / "resources"
        require(build_resources.is_dir(), f"build resources directory missing: {build_resources}")
        build_files = set()
        for directory, _dirs, files in os.walk(zip_safe.long_path(build_resources)):
            for filename in files:
                full = Path(directory.replace("\\\\?\\", "")) / filename
                relative = os.path.relpath(full, build_root).replace(os.sep, "/")
                build_files.add(relative)
        extension_names = set(extension["files"])
        app_names = set(app["files"])

        seen: set[str] = set()
        checked = 0
        with zipfile.ZipFile(app_zip) as app_zf, zipfile.ZipFile(extension_zip) as ext_zf:
            for item in listed:
                require(isinstance(item, dict), "final extension file entry must be an object")
                relative = item.get("path")
                size = item.get("size")
                digest = item.get("sha256")
                require(isinstance(relative, str) and relative, "final extension file path missing")
                zip_safe.safe_member_name(relative)
                require(relative not in seen, f"duplicate final extension file entry: {relative}")
                seen.add(relative)
                require(isinstance(size, int) and size >= 0, f"invalid final size for {relative}")
                require(isinstance(digest, str) and SHA256.match(digest.lower()) is not None,
                        f"invalid final sha256 for {relative}")
                build_file = build / Path(*relative.split("/"))
                require(zip_safe.file_size(build_file) == size, f"build size mismatch for {relative}")
                require(zip_safe.file_sha256(build_file) == digest.lower(), f"build sha256 mismatch for {relative}")
                app_member = f"{app_top}/{relative}"
                extension_member = f"{extension_top}/{relative}"
                require(app_member in app_names, f"final extension file missing from app ZIP: {relative}")
                require(extension_member in extension_names, f"final extension file missing from extension ZIP: {relative}")
                require(app_zf.getinfo(app_member).file_size == size, f"app ZIP size mismatch for {relative}")
                require(ext_zf.getinfo(extension_member).file_size == size, f"extension ZIP size mismatch for {relative}")
                require(hash_member(app_zf, app_member) == digest.lower(), f"app ZIP sha256 mismatch for {relative}")
                require(hash_member(ext_zf, extension_member) == digest.lower(), f"extension ZIP sha256 mismatch for {relative}")
                checked += 1
        require("resources/app.asar" in seen, "final extension.json must list resources/app.asar")
        require(seen == build_files, "extension.json does not match the packaged win-unpacked file set")

        staging = output / name
        require(staging.is_dir(), "unpacked extension staging directory missing")
        staging_files = set()
        for directory, _dirs, files in os.walk(zip_safe.long_path(staging)):
            for filename in files:
                full = Path(directory.replace("\\\\?\\", "")) / filename
                staging_files.add(os.path.relpath(full, os.path.abspath(staging)).replace(os.sep, "/"))
        extension_relative = {member[len(extension_top) + 1:] for member in extension_names}
        require(staging_files == extension_relative, "unpacked extension staging tree differs from the final ZIP")
        with zipfile.ZipFile(extension_zip) as ext_zf:
            for relative in sorted(staging_files):
                local = staging / Path(*relative.split("/"))
                require(hash_member(ext_zf, f"{extension_top}/{relative}") == zip_safe.file_sha256(local),
                        f"staging file differs from final ZIP: {relative}")

        readme = (output / "版本选择.md").read_text(encoding="utf-8-sig")
        for needle in (args.version, app_zip.name, extension_zip.name, "AI资源领航扩展版", "独立 APP 完整版"):
            require(needle in readme, f"版本选择.md missing {needle!r}")

        report = {
            "ok": True,
            "version": args.version,
            "appAsarSha256": expected_asar,
            "archives": {
                "app": {"name": app_zip.name, "sha256": app_sha, "bytes": app_size,
                        "fileCount": app["fileCount"], "top": app["top"], "crcVerified": True},
                "extension": {"name": extension_zip.name, "sha256": extension_sha, "bytes": extension_size,
                              "fileCount": extension["fileCount"], "top": extension["top"], "crcVerified": True},
            },
            "extensionManifestFiles": checked,
            "sameSourceVerified": True,
            "stagingTreeVerified": True,
            "sha256SumsVerified": True,
            "versionChoiceVerified": True,
        }
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (VerificationError, zip_safe.ZipSafetyError, zipfile.BadZipFile, OSError, json.JSONDecodeError) as error:
        print(f"ASSEMBLY VERIFICATION FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

