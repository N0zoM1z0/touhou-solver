#!/usr/bin/env python3
"""Inspect and extract TH08's PBGZ archive format.

This implementation is derived from the TH08 executable's archive reader:

* pbgz_decode_xor_shuffle      at 0x0043E1D0
* pbgz_lzss_decompress        at 0x004740E0
* pbgz_archive_extract_member at 0x00474AF0
* pbgz_archive_parse          at 0x00474CE0
* pbgz_parse_directory        at 0x00474FA0

It intentionally has no dependency on external Touhou format libraries.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


PBGZ_MAGIC = b"PBGZ"
HEADER_SIZE = 16
LZSS_RING_SIZE = 0x2000


class PbgzError(ValueError):
    """Raised when the archive violates a constraint used by TH08."""


def decode_xor_shuffle(
    data: bytes, key: int, step: int, block_size: int, limit: int
) -> bytes:
    """Reproduce TH08's block-local XOR and byte permutation."""
    if block_size <= 0:
        raise PbgzError("block_size must be positive")

    remainder = len(data) % block_size
    preserved_remainder = remainder if remainder < block_size // 4 else 0
    preserved_size = (len(data) & 1) + preserved_remainder
    shuffled_size = len(data) - preserved_size

    output = bytearray(len(data))
    source = 0
    destination = 0
    remaining = shuffled_size
    remaining_limit = limit
    key &= 0xFF
    step &= 0xFF

    while remaining > 0 and remaining_limit > 0:
        current_size = min(remaining, block_size)
        block_start = destination

        write_at = block_start + current_size - 1
        for _ in range((current_size + 1) // 2):
            output[write_at] = data[source] ^ key
            write_at -= 2
            source += 1
            key = (key + step) & 0xFF

        write_at = block_start + current_size - 2
        for _ in range(current_size // 2):
            output[write_at] = data[source] ^ key
            write_at -= 2
            source += 1
            key = (key + step) & 0xFF

        destination += current_size
        remaining -= current_size
        remaining_limit -= current_size

    tail_size = preserved_size + remaining
    if tail_size:
        output[destination : destination + tail_size] = data[source : source + tail_size]
    return bytes(output)


class _MsbBitReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.bit_offset = 0

    def read(self, count: int) -> int:
        value = 0
        for _ in range(count):
            byte_offset = self.bit_offset >> 3
            bit_in_byte = 7 - (self.bit_offset & 7)
            # The game decoder substitutes a zero byte after the input buffer
            # is exhausted. Some streams rely on that padding for the zero
            # back-reference which terminates decoding.
            byte = self.data[byte_offset] if byte_offset < len(self.data) else 0
            value = (value << 1) | ((byte >> bit_in_byte) & 1)
            self.bit_offset += 1
        return value


def lzss_decompress(data: bytes, expected_size: int) -> bytes:
    """Reproduce TH08's 0x2000-byte-ring, MSB-first LZSS decoder."""
    if expected_size < 0:
        raise PbgzError("negative expected output size")

    bits = _MsbBitReader(data)
    ring = bytearray(LZSS_RING_SIZE)
    write_pos = 1
    output = bytearray()

    while True:
        if bits.read(1):
            value = bits.read(8)
            output.append(value)
            ring[write_pos] = value
            write_pos = (write_pos + 1) & (LZSS_RING_SIZE - 1)
        else:
            read_pos = bits.read(13)
            if read_pos == 0:
                break
            length = bits.read(4) + 3
            for index in range(length):
                value = ring[(read_pos + index) & (LZSS_RING_SIZE - 1)]
                output.append(value)
                ring[write_pos] = value
                write_pos = (write_pos + 1) & (LZSS_RING_SIZE - 1)

        if len(output) > expected_size:
            raise PbgzError(
                f"decompressed output exceeds declared size {expected_size:#x}"
            )

    if len(output) != expected_size:
        raise PbgzError(
            f"decompressed size mismatch: expected {expected_size:#x}, "
            f"got {len(output):#x}"
        )
    return bytes(output)


@dataclass(frozen=True)
class PbgzEntry:
    index: int
    name: str
    data_offset: int
    uncompressed_size: int
    unknown: int
    compressed_size: int


class PbgzArchive:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data = path.read_bytes()
        self.directory_offset = 0
        self.directory_size = 0
        self.directory_padding_size = 0
        self.entries = self._parse()
        self._entries_by_name = {entry.name.casefold(): entry for entry in self.entries}

    def _parse(self) -> list[PbgzEntry]:
        if len(self._data) < HEADER_SIZE or self._data[:4] != PBGZ_MAGIC:
            raise PbgzError(f"{self.path} is not a TH08 PBGZ archive")

        decoded_header = decode_xor_shuffle(
            self._data[4:HEADER_SIZE], key=0x1B, step=0x37, block_size=0x0C, limit=0x400
        )
        encoded_count, encoded_directory_offset, encoded_directory_size = struct.unpack(
            "<III", decoded_header
        )
        entry_count = encoded_count - 123456
        self.directory_offset = encoded_directory_offset - 345678
        self.directory_size = encoded_directory_size - 567891

        if entry_count <= 0:
            raise PbgzError(f"invalid entry count: {entry_count}")
        if not HEADER_SIZE <= self.directory_offset < len(self._data):
            raise PbgzError(f"invalid directory offset: {self.directory_offset:#x}")
        if self.directory_size <= 0:
            raise PbgzError(f"invalid directory size: {self.directory_size}")

        encoded_directory = self._data[self.directory_offset :]
        compressed_directory = decode_xor_shuffle(
            encoded_directory, key=0x3E, step=0x9B, block_size=0x80, limit=0x400
        )
        directory = lzss_decompress(compressed_directory, self.directory_size)
        raw_entries, self.directory_padding_size = self._parse_directory(
            directory, entry_count
        )

        entries: list[PbgzEntry] = []
        for index, (name, offset, size, unknown) in enumerate(raw_entries):
            next_offset = (
                raw_entries[index + 1][1]
                if index + 1 < len(raw_entries)
                else self.directory_offset
            )
            if offset < HEADER_SIZE or next_offset < offset or next_offset > self.directory_offset:
                raise PbgzError(
                    f"invalid data bounds for entry {index} {name!r}: "
                    f"{offset:#x}..{next_offset:#x}"
                )
            entries.append(
                PbgzEntry(
                    index=index,
                    name=name,
                    data_offset=offset,
                    uncompressed_size=size,
                    unknown=unknown,
                    compressed_size=next_offset - offset,
                )
            )
        return entries

    @staticmethod
    def _parse_directory(
        directory: bytes, entry_count: int
    ) -> tuple[list[tuple[str, int, int, int]], int]:
        cursor = 0
        entries: list[tuple[str, int, int, int]] = []
        for index in range(entry_count):
            terminator = directory.find(b"\0", cursor)
            if terminator < 0:
                raise PbgzError(f"directory entry {index} has no filename terminator")
            raw_name = directory[cursor:terminator]
            cursor = terminator + 1
            if cursor + 12 > len(directory):
                raise PbgzError(f"directory entry {index} metadata is truncated")
            offset, size, unknown = struct.unpack_from("<III", directory, cursor)
            cursor += 12
            try:
                name = raw_name.decode("ascii")
            except UnicodeDecodeError:
                name = raw_name.decode("cp932")
            entries.append((name, offset, size, unknown))

        padding = directory[cursor:]
        if any(padding):
            raise PbgzError(
                f"directory has {len(padding):#x} nonzero unexplained trailing bytes"
            )
        return entries, len(padding)

    def find(self, name: str) -> PbgzEntry:
        try:
            return self._entries_by_name[name.casefold()]
        except KeyError as exc:
            raise PbgzError(f"archive member not found: {name}") from exc

    def extract(self, entry: PbgzEntry) -> bytes:
        start = entry.data_offset
        end = start + entry.compressed_size
        return lzss_decompress(self._data[start:end], entry.uncompressed_size)


def _selected(entries: Iterable[PbgzEntry], patterns: list[str]) -> list[PbgzEntry]:
    if not patterns:
        return list(entries)
    return [
        entry
        for entry in entries
        if any(fnmatch.fnmatchcase(entry.name.casefold(), p.casefold()) for p in patterns)
    ]


def _safe_output_path(root: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/")
    relative = PurePosixPath(normalized)
    if relative.is_absolute() or ".." in relative.parts:
        raise PbgzError(f"unsafe archive member path: {member_name!r}")
    return root.joinpath(*relative.parts)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="path to th08.dat")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list archive members")
    list_parser.add_argument("patterns", nargs="*", help="optional case-insensitive globs")
    list_parser.add_argument("--json", action="store_true", help="emit JSON")

    extract_parser = subparsers.add_parser("extract", help="extract selected members")
    extract_parser.add_argument("output", type=Path, help="output directory")
    extract_parser.add_argument("patterns", nargs="+", help="case-insensitive member globs")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        archive = PbgzArchive(args.archive)
        entries = _selected(archive.entries, getattr(args, "patterns", []))
        if args.command == "list":
            if args.json:
                print(
                    json.dumps(
                        {
                            "archive": str(archive.path),
                            "directory_offset": archive.directory_offset,
                            "directory_size": archive.directory_size,
                            "directory_padding_size": archive.directory_padding_size,
                            "entry_count": len(archive.entries),
                            "entries": [asdict(entry) for entry in entries],
                        },
                        indent=2,
                    )
                )
            else:
                for entry in entries:
                    print(
                        f"{entry.index:4d}  {entry.data_offset:08x}  "
                        f"{entry.compressed_size:8d} -> {entry.uncompressed_size:8d}  "
                        f"u={entry.unknown:08x}  {entry.name}"
                    )
                print(f"{len(entries)} of {len(archive.entries)} entries")
        else:
            args.output.mkdir(parents=True, exist_ok=True)
            for entry in entries:
                output_path = _safe_output_path(args.output, entry.name)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(archive.extract(entry))
                print(f"{entry.name}: {entry.uncompressed_size} bytes")
            print(f"extracted {len(entries)} entries to {args.output}")
        return 0
    except (OSError, PbgzError, struct.error, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
