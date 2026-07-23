#!/usr/bin/env python3
"""Decode TH08's optional four-byte ``edz?`` resource wrapper.

The marker checks and parameter table are recovered from 0x0043E390 and
0x004C78E0 in the TH08 executable. The payload transform is shared with the
PBGZ directory decoder at 0x0043E1D0.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from th08_pbgz import PbgzError, decode_xor_shuffle


@dataclass(frozen=True)
class ResourceCodec:
    marker: int
    key: int
    step: int
    block_size: int
    limit: int


RESOURCE_MAGIC = b"edz"
RESOURCE_CODECS = (
    ResourceCodec(ord("M"), 0x1B, 0x37, 0x0040, 0x2800),
    ResourceCodec(ord("T"), 0x51, 0xE9, 0x0040, 0x3000),
    ResourceCodec(ord("A"), 0xC1, 0x51, 0x1400, 0x2000),
    ResourceCodec(ord("J"), 0x03, 0x19, 0x1400, 0x7800),
    ResourceCodec(ord("E"), 0xAB, 0xCD, 0x0200, 0x1000),
    ResourceCodec(ord("W"), 0x12, 0x34, 0x0400, 0x2800),
    ResourceCodec(ord("-"), 0x35, 0x97, 0x0080, 0x2800),
    ResourceCodec(ord("*"), 0x99, 0x37, 0x0400, 0x1000),
)


def decode_resource(data: bytes, require_wrapper: bool = False) -> bytes:
    """Return the decoded payload, or the original data if it is unwrapped."""
    if len(data) < 4 or data[:3] != RESOURCE_MAGIC:
        if require_wrapper:
            raise PbgzError("resource does not have a recognized edz wrapper")
        return data

    codec = next((item for item in RESOURCE_CODECS if item.marker == data[3]), None)
    if codec is None:
        if require_wrapper:
            raise PbgzError(f"unknown edz resource marker: {data[3]:#04x}")
        return data

    return decode_xor_shuffle(
        data[4:], codec.key, codec.step, codec.block_size, codec.limit
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="output file or directory")
    parser.add_argument("inputs", type=Path, nargs="+", help="wrapped input files")
    parser.add_argument(
        "--require-wrapper",
        action="store_true",
        help="fail instead of passing through unwrapped files",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    multiple = len(args.inputs) > 1
    if multiple:
        args.output.mkdir(parents=True, exist_ok=True)
    elif args.output.exists() and args.output.is_dir():
        multiple = True

    try:
        for input_path in args.inputs:
            output_path = args.output / input_path.name if multiple else args.output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            decoded = decode_resource(
                input_path.read_bytes(), require_wrapper=args.require_wrapper
            )
            output_path.write_bytes(decoded)
            print(f"{input_path.name}: {input_path.stat().st_size} -> {len(decoded)} bytes")
        return 0
    except (OSError, PbgzError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
