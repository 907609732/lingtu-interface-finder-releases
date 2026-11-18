#!/usr/bin/env python3
r"""Small, dependency-free ZIP inspection/extraction helpers for the release CI.

Only the two candidate archives and the two assembled archives are ever opened.
Every member name is validated before it is hashed or extracted; CRCs are checked
with zipfile.testzip(). Long Windows paths are opened through the \\?\ prefix so
Python's extractor is not limited by MAX_PATH.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
import sys
import zipfile
from pathlib import Path

GIB = 1024**3
MIB = 1024**2
DRIVE = re.compile(r"^[A-Za-z]:")
RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}
WINDOWS_BAD = set('<>:"|?*')


class ZipSafetyError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ZipSafetyError(message)


def long_path(value: os.PathLike[str] | str) -> str:
    """Return a path that Python can open even when it exceeds MAX_PATH."""
    text = os.path.abspath(os.fspath(value))
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def ensure_dir(value: os.PathLike[str] | str) -> None:
    os.makedirs(long_path(value), exist_ok=True)


def open_write(value: os.PathLike[str] | str):
    return open(long_path(value), "xb")


def file_sha256(value: os.PathLike[str] | str) -> str:
    digest = hashlib.sha256()
    with open(long_path(value), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(value: os.PathLike[str] | str) -> int:
    return os.stat(long_path(value)).st_size


def safe_member_name(name: str) -> None:
    """Reject anything that could escape an extraction directory or break NTFS."""
    require(isinstance(name, str) and name != "", "empty ZIP member name")
    require("\x00" not in name, "NUL in ZIP member name")
    require("\\" not in name, f"backslash in ZIP member name: {name!r}")
    require(not name.startswith("/"), f"absolute ZIP member name: {name!r}")
    require(not DRIVE.match(name), f"drive-qualified ZIP member name: {name!r}")
    require(not any(ord(char) < 32 for char in name), f"control character in ZIP member name: {name!r}")
    parts = name.split("/")
    body = parts[:-1] if name.endswith("/") else parts
    require(body != [], f"empty ZIP path: {name!r}")
    for part in body:
        require(part not in ("", ".", ".."), f"unsafe ZIP path segment in {name!r}")
        require(not any(char in WINDOWS_BAD for char in part), f"invalid Windows character in {name!r}")
        require(not part.endswith((" ", ".")), f"trailing space/dot in ZIP member name: {name!r}")
        stem = part.split(".", 1)[0].upper()
        require(stem not in RESERVED, f"reserved Windows device name in ZIP member name: {name!r}")


def member_sha256(archive: Path, name: str) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(archive) as zf, zf.open(name) as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_member(archive: Path, name: str, limit: int = 32 * MIB) -> bytes:
    with zipfile.ZipFile(archive) as zf:
        info = zf.getinfo(name)
        require(info.file_size <= limit, f"ZIP member too large to read: {name}")
        with zf.open(info) as source:
            return source.read(limit + 1)


def inspect_zip(
    archive: Path,
    *,
    expected_top: str | None = None,
    required: tuple[str, ...] = (),
    forbidden_relative: tuple[re.Pattern[str], ...] = (),
    max_entries: int = 200_000,
    max_total: int = 4 * GIB,
    max_entry: int = 3 * GIB,
    max_ratio: int = 500,
    verify_crc: bool = True,
) -> dict:
    """Validate names, duplicates, encryption, links, sizes and CRCs."""
    archive = Path(archive)
    require(archive.is_file(), f"archive missing: {archive}")
    files: list[str] = []
    directories: list[str] = []
    seen: set[str] = set()
    total_uncompressed = 0
    total_compressed = 0
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        require(infos, f"empty ZIP: {archive}")
        require(len(infos) <= max_entries, f"too many ZIP entries in {archive.name}: {len(infos)}")
        for info in infos:
            name = info.filename
            safe_member_name(name)
            require(not (info.flag_bits & 0x1), f"encrypted ZIP member: {name}")
            mode = (info.external_attr >> 16) & 0xFFFF
            require(not (mode and stat.S_ISLNK(mode)), f"symbolic link in ZIP: {name}")
            if name.endswith("/"):
                require(info.file_size == 0, f"directory entry with data: {name}")
                directories.append(name)
                continue
            require(info.file_size <= max_entry, f"ZIP member too large: {name} ({info.file_size} bytes)")
            if info.compress_size and info.file_size > 64 * MIB:
                ratio = info.file_size / info.compress_size
                require(ratio <= max_ratio, f"suspicious compression ratio for {name}: {ratio:.0f}")
            key = name.casefold()
            require(key not in seen, f"duplicate ZIP member (case-insensitive): {name}")
            seen.add(key)
            total_uncompressed += info.file_size
            total_compressed += info.compress_size
            require(total_uncompressed <= max_total, f"ZIP expands beyond {max_total} bytes: {archive.name}")
            files.append(name)
        tops = {name.split("/", 1)[0] for name in files}
        require(len(tops) == 1, f"ZIP must have exactly one top-level directory: {sorted(tops)}")
        top = tops.pop()
        if expected_top is not None:
            require(top == expected_top, f"unexpected top-level directory: {top!r} (expected {expected_top!r})")
        require(len(files) > 0, f"ZIP has no files: {archive.name}")
        for name in files:
            require(name.startswith(top + "/"), f"file outside top-level directory: {name}")
            relative = name[len(top) + 1:]
            for pattern in forbidden_relative:
                require(not pattern.search(relative), f"forbidden ZIP member: {relative}")
        for wanted in required:
            require(wanted in files, f"required ZIP member missing: {wanted}")
        if verify_crc:
            bad = zf.testzip()
            require(bad is None, f"ZIP CRC failed: {bad}")
    return {
        "path": str(archive),
        "top": top,
        "files": files,
        "directories": directories,
        "fileCount": len(files),
        "uncompressedBytes": total_uncompressed,
        "compressedBytes": total_compressed,
        "sha256": file_sha256(archive),
        "bytes": file_size(archive),
    }


def extract_zip(archive: Path, destination: Path, expected_top: str, *, verify_crc: bool = False) -> Path:
    """Extract one verified archive into destination/<expected_top> without overwrites."""
    archive = Path(archive)
    destination = Path(destination)
    ensure_dir(destination)
    target_top = destination / expected_top
    require(not os.path.exists(long_path(target_top)), f"extraction target already exists: {target_top}")
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename
            safe_member_name(name)
            require(name.split("/", 1)[0] == expected_top, f"member outside expected top: {name}")
            target = destination.joinpath(*name.split("/"))
            normal_destination = os.path.abspath(destination)
            normal_target = os.path.abspath(target)
            require(
                normal_target == normal_destination or normal_target.startswith(normal_destination + os.sep),
                f"extraction escaped destination: {name}",
            )
            if name.endswith("/"):
                ensure_dir(target)
                continue
            ensure_dir(target.parent)
            with zf.open(info) as source, open_write(target) as sink:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(chunk)
    require(os.path.isdir(long_path(target_top)), f"extraction produced no top directory: {target_top}")
    return target_top


def main() -> int:
    print("zip_safe is a helper module; run verify_candidates.py, stage_candidates.py, "
          "verify_assembly.py or stage_final.py instead.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
