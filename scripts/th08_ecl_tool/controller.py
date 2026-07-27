"""Public TH08 ECL facade and command-line orchestration."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from th08_ecl_tool.catalogs import (
    build_opcode_catalog,
    build_spell_catalog,
    expand_inputs as _expand_inputs,
    summarize,
)
from th08_ecl_tool.core import (  # noqa: F401
    ECL_MAGIC,
    HEADER_SIZE,
    SUB_INSTRUCTION_HEADER_SIZE,
    TIMELINE_INSTRUCTION_HEADER_SIZE,
    TIMELINE_OPCODE_NAMES,
    TIMELINE_SLOT_COUNT,
    EclError,
    EclFile,
    EclHeader,
    SubInstruction,
    Subroutine,
    Timeline,
    TimelineInstruction,
    parse_ecl,
)
from th08_ecl_tool.formatting import (  # noqa: F401
    decode_bullet_emission,
    decode_bullet_transform,
    decode_laser_spawn,
    decode_spell_card_start,
    format_listing,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    info = subparsers.add_parser(
        "info", help="validate files and print summaries"
    )
    info.add_argument("inputs", type=Path, nargs="+")
    info.add_argument("--json", action="store_true", help="emit JSON")

    dump = subparsers.add_parser(
        "dump", help="write a complete instruction listing"
    )
    dump.add_argument("input", type=Path)
    dump.add_argument("-o", "--output", type=Path)

    corpus = subparsers.add_parser(
        "corpus",
        help="write listings and a JSON summary for an ECL corpus",
    )
    corpus.add_argument("input", type=Path, help="decoded ECL directory")
    corpus.add_argument("output", type=Path, help="report output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "info":
            reports = [
                summarize(parse_ecl(path))
                for path in _expand_inputs(args.inputs)
            ]
            if args.json:
                print(json.dumps(reports, indent=2, sort_keys=True))
            else:
                for report in reports:
                    print(
                        f"{report['file']}: "
                        f"subs={report['subroutine_count']} "
                        f"timelines={report['timeline_count']} "
                        f"sub_insns={report['sub_instruction_count']} "
                        f"timeline_insns="
                        f"{report['timeline_instruction_count']} "
                        f"fire_insns={report['bullet_instruction_count']}"
                    )
            return 0

        if args.command == "dump":
            listing = format_listing(parse_ecl(args.input))
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(listing, encoding="utf-8")
            else:
                print(listing)
            return 0

        ecl_paths = _expand_inputs([args.input])
        args.output.mkdir(parents=True, exist_ok=True)
        reports = []
        parsed_ecls = []
        for path in ecl_paths:
            ecl = parse_ecl(path)
            parsed_ecls.append(ecl)
            reports.append(summarize(ecl))
            (args.output / f"{path.stem}.txt").write_text(
                format_listing(ecl), encoding="utf-8"
            )
        (args.output / "corpus_summary.json").write_text(
            json.dumps(reports, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        opcode_rows, opcode_markdown = build_opcode_catalog(parsed_ecls)
        (args.output / "opcode_catalog.json").write_text(
            json.dumps(opcode_rows, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.output / "opcode_catalog.md").write_text(
            opcode_markdown, encoding="utf-8"
        )
        spell_rows, spell_markdown = build_spell_catalog(parsed_ecls)
        (args.output / "spell_catalog.json").write_text(
            json.dumps(
                spell_rows,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (args.output / "spell_catalog.md").write_text(
            spell_markdown, encoding="utf-8"
        )
        print(
            f"wrote {len(reports)} listings, corpus_summary.json, "
            f"opcode catalog, and {len(spell_rows)} spell cards "
            f"to {args.output}"
        )
        return 0
    except (EclError, OSError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
