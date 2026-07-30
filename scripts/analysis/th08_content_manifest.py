#!/usr/bin/env python3
"""Build a content-addressed TH08 ECL/STD/ANM/MSG manifest.

The report compares pinned thtk archive extraction with the independent
native-derived repository PBGZ and ``edz?`` decoders.  It also compares every
ECL's structural counts with thtk's raw disassembly.  External-tool failures
are retained explicitly and do not acquire runtime or semantic authority.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import signal
import struct
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from th08_ecl import parse_ecl
from th08_pbgz import PbgzArchive, PbgzEntry
from th08_resource import decode_resource


SCHEMA = "th08-immutable-content-manifest-v1"
TASKBOOK_CARD = "CONTENT-01"
EXPECTED_ARCHIVE_SHA256 = (
    "9d7edf43b8ddd347cbb641836f6b5050745dd936f688daebbf9382ca557043bb"
)
EXPECTED_EXECUTABLE_SHA256 = (
    "330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924"
)
EXPECTED_THTK_COMMIT = "892114a0fcaa0bbdaaecf3cb4ad56f758683fb40"
EXPECTED_ARCHIVE_ENTRY_COUNT = 317
EXPECTED_CONTENT_ASSET_COUNT = 188
CONTENT_GLOBS = ("*.ecl", "*.std", "*.anm", "msg*.dat")
MANDATORY_SCENE_PATTERNS = {
    "stage3": (
        "ecldata3*.ecl",
        "stage3*.std",
        "eff03.anm",
        "face_st03*.anm",
        "stg3*.anm",
        "msg3*.dat",
    ),
    "stage4a": (
        "ecldata4a*.ecl",
        "stage4a*.std",
        "eff04a.anm",
        "face_st04a*.anm",
        "stg4a*.anm",
        "msg4a*.dat",
    ),
    "stage5": (
        "ecldata5*.ecl",
        "stage5*.std",
        "eff05.anm",
        "face_st05*.anm",
        "stg5*.anm",
        "msg5*.dat",
    ),
    "final_b": (
        "ecldata7*.ecl",
        "stage7*.std",
        "eff07.anm",
        "face_st07*.anm",
        "stg7*.anm",
        "msg7*.dat",
    ),
}
MANDATORY_SCENE_METADATA = {
    "stage3": {"route_stage_index": 2, "content_stage": 3},
    "stage4a": {"route_stage_index": 3, "content_stage": "4a"},
    "stage5": {"route_stage_index": 5, "content_stage": 5},
    "final_b": {"route_stage_index": 7, "content_stage": 7},
}
_THTK_LIST_ROW = re.compile(
    rb"^(?P<name>\S+)\s+(?P<size>[0-9]+)\s+(?P<stored>[0-9]+)$"
)
_THECL_SUB = re.compile(rb"(?m)^sub Sub[0-9]+\(\)$")
_THECL_TIMELINE = re.compile(rb"(?m)^timeline Timeline[0-9]+\(\)$")
_THECL_INSTRUCTION = re.compile(
    rb"(?m)^[^\r\n]*?\bins_([0-9]+)\("
)


class ContentManifestError(ValueError):
    """Raised when content identity or a required differential disagrees."""


@dataclass(frozen=True)
class ThdatListRow:
    name: str
    uncompressed_size: int
    compressed_size: int


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(
    arguments: list[str],
    *,
    require_success: bool,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        arguments,
        check=False,
        capture_output=True,
    )
    if require_success and result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise ContentManifestError(
            f"{Path(arguments[0]).name} failed with {result.returncode}: "
            f"{stderr}"
        )
    return result


def _parse_thdat_list(payload: bytes) -> tuple[ThdatListRow, ...]:
    lines = payload.splitlines()
    if not lines or lines[0].split() != [b"Name", b"Size", b"Stored"]:
        raise ContentManifestError("unexpected thdat list header")
    rows: list[ThdatListRow] = []
    for line in lines[1:]:
        match = _THTK_LIST_ROW.fullmatch(line)
        if match is None:
            raise ContentManifestError(
                f"unexpected thdat list row: {line!r}"
            )
        try:
            name = match.group("name").decode("ascii")
        except UnicodeDecodeError as error:
            raise ContentManifestError(
                "thdat emitted a non-ASCII TH08 member name"
            ) from error
        rows.append(
            ThdatListRow(
                name=name,
                uncompressed_size=int(match.group("size")),
                compressed_size=int(match.group("stored")),
            )
        )
    return tuple(rows)


def _content_category(name: str) -> str | None:
    lowered = name.casefold()
    if lowered.endswith(".ecl"):
        return "ecl"
    if lowered.endswith(".std"):
        return "std"
    if lowered.endswith(".anm"):
        return "anm"
    if fnmatch.fnmatchcase(lowered, "msg*.dat"):
        return "msg"
    return None


def _scene_tags(name: str) -> tuple[str, ...]:
    lowered = name.casefold()
    return tuple(
        scene
        for scene, patterns in MANDATORY_SCENE_PATTERNS.items()
        if any(
            fnmatch.fnmatchcase(lowered, pattern.casefold())
            for pattern in patterns
        )
    )


def _parse_thecl_structure(payload: bytes) -> dict[str, int]:
    opcodes = _parse_thecl_opcodes(payload)
    return {
        "subroutine_count": len(_THECL_SUB.findall(payload)),
        "timeline_count": len(_THECL_TIMELINE.findall(payload)),
        "instruction_line_count": len(opcodes),
    }


def _parse_thecl_opcodes(payload: bytes) -> tuple[int, ...]:
    return tuple(int(match) for match in _THECL_INSTRUCTION.findall(payload))


def _repository_opcode_sequence(path: Path) -> tuple[tuple[int, ...], int]:
    data = path.read_bytes()
    ecl = parse_ecl(path)
    opcodes = [
        instruction.opcode
        for subroutine in ecl.subroutines
        for instruction in subroutine.instructions
    ]
    terminal_count = 0
    for timeline in ecl.timelines:
        opcodes.extend(
            instruction.opcode for instruction in timeline.instructions
        )
        offset = timeline.stop_offset
        while offset < timeline.end:
            remaining = data[offset : timeline.end]
            if not any(remaining):
                break
            if len(remaining) < 8:
                raise ContentManifestError(
                    f"{path.name}: truncated terminal timeline record"
                )
            time, opcode, size, _difficulty_mask = struct.unpack_from(
                "<iHBB",
                data,
                offset,
            )
            if time == -1 and opcode == 0 and size == 0:
                offset += 8
                break
            if time >= 0 or size < 8 or offset + size > timeline.end:
                raise ContentManifestError(
                    f"{path.name}: malformed terminal timeline record"
                )
            opcodes.append(opcode)
            terminal_count += 1
            offset += size
        if any(data[offset : timeline.end]):
            raise ContentManifestError(
                f"{path.name}: nonzero bytes after terminal records"
            )
    return tuple(opcodes), terminal_count


def _termination(returncode: int) -> dict[str, object]:
    if returncode < 0:
        number = -returncode
        try:
            name = signal.Signals(number).name
        except ValueError:
            name = "UNKNOWN_SIGNAL"
        return {"kind": "signal", "number": number, "name": name}
    return {"kind": "exit", "code": returncode}


def _validate_external_source(source: Path) -> dict[str, object]:
    commit = _run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        require_success=True,
    ).stdout.decode("ascii").strip()
    if commit != EXPECTED_THTK_COMMIT:
        raise ContentManifestError(
            f"thtk commit {commit} != expected {EXPECTED_THTK_COMMIT}"
        )
    status = _run(
        ["git", "-C", str(source), "status", "--porcelain"],
        require_success=True,
    ).stdout
    if status:
        raise ContentManifestError("pinned thtk source worktree is dirty")
    return {
        "project": "thpatch/thtk",
        "commit": commit,
        "source_worktree_clean": True,
    }


def _tool_record(path: Path) -> dict[str, object]:
    result = _run([str(path), "-V"], require_success=True)
    version = result.stdout.decode("utf-8", errors="strict").strip()
    if version != "Touhou Toolkit release 12":
        raise ContentManifestError(f"unexpected thtk tool version: {version}")
    return {
        "version": version,
        "binary_sha256": _sha256_path(path),
    }


def _validate_directory(
    rows: tuple[ThdatListRow, ...],
    entries: tuple[PbgzEntry, ...] | list[PbgzEntry],
) -> None:
    if len(rows) != EXPECTED_ARCHIVE_ENTRY_COUNT:
        raise ContentManifestError(
            f"thdat listed {len(rows)} entries, expected "
            f"{EXPECTED_ARCHIVE_ENTRY_COUNT}"
        )
    if len(entries) != len(rows):
        raise ContentManifestError("thdat/repository entry counts disagree")
    for row, entry in zip(rows, entries, strict=True):
        if (
            row.name != entry.name
            or row.uncompressed_size != entry.uncompressed_size
            or row.compressed_size != entry.compressed_size
        ):
            raise ContentManifestError(
                "thdat/repository directory mismatch at "
                f"{entry.index}: {row!r} != {entry!r}"
            )


def _tracked_record(
    path: Path,
    *,
    expected: bytes,
    repo_root: Path,
) -> dict[str, object] | None:
    if not path.exists():
        return None
    actual = path.read_bytes()
    if actual != expected:
        raise ContentManifestError(
            f"tracked artifact disagrees with shipped content: {path}"
        )
    return {
        "path": str(path.relative_to(repo_root)),
        "sha256": _sha256_bytes(actual),
        "exact_match": True,
    }


def _asset_record(
    entry: PbgzEntry,
    *,
    wrapped: bytes,
    decoded: bytes,
    thtk_decoded: bytes,
    repo_root: Path,
) -> dict[str, object]:
    if decoded != thtk_decoded:
        raise ContentManifestError(
            f"thtk/repository decoded payload mismatch: {entry.name}"
        )
    marker: str | None = None
    if len(wrapped) >= 4 and wrapped[:3] == b"edz":
        marker = wrapped[:4].decode("ascii")
    return {
        "name": entry.name,
        "category": _content_category(entry.name),
        "archive_index": entry.index,
        "archive_data_offset": entry.data_offset,
        "archive_compressed_size": entry.compressed_size,
        "wrapped_size": len(wrapped),
        "wrapped_sha256": _sha256_bytes(wrapped),
        "resource_wrapper": marker,
        "decoded_size": len(decoded),
        "decoded_sha256": _sha256_bytes(decoded),
        "thtk_decoded_sha256": _sha256_bytes(thtk_decoded),
        "thtk_repository_payload_exact_match": True,
        "mandatory_scene_tags": list(_scene_tags(entry.name)),
        "tracked_wrapped": _tracked_record(
            repo_root / "artifacts" / "extracted" / entry.name,
            expected=wrapped,
            repo_root=repo_root,
        ),
        "tracked_decoded": _tracked_record(
            repo_root / "artifacts" / "decoded" / entry.name,
            expected=decoded,
            repo_root=repo_root,
        ),
    }


def _content_set_sha256(assets: list[dict[str, object]]) -> str:
    payload = b"".join(
        str(asset["name"]).encode("ascii")
        + b"\0"
        + str(asset["decoded_sha256"]).encode("ascii")
        + b"\0"
        for asset in sorted(assets, key=lambda value: str(value["name"]))
    )
    return _sha256_bytes(payload)


def _ecl_differential(
    path: Path,
    *,
    thecl: Path,
    output: Path,
) -> dict[str, object]:
    result = _run(
        [str(thecl), "-r", "-d8", str(path), str(output)],
        require_success=True,
    )
    listing = output.read_bytes()
    thtk_counts = _parse_thecl_structure(listing)
    ecl = parse_ecl(path)
    thtk_opcodes = _parse_thecl_opcodes(listing)
    repo_opcodes, terminal_count = _repository_opcode_sequence(path)
    repo_counts = {
        "subroutine_count": ecl.header.subroutine_count,
        "timeline_count": ecl.header.timeline_count,
        "sub_instruction_count": sum(
            len(sub.instructions) for sub in ecl.subroutines
        ),
        "timeline_instruction_count": sum(
            len(timeline.instructions) for timeline in ecl.timelines
        ),
    }
    exact = (
        thtk_counts["subroutine_count"] == repo_counts["subroutine_count"]
        and thtk_counts["timeline_count"] == repo_counts["timeline_count"]
        and thtk_opcodes == repo_opcodes
    )
    if not exact:
        raise ContentManifestError(
            f"thecl/repository structural mismatch: {path.name}"
        )
    return {
        "name": path.name,
        "decoded_sha256": ecl.sha256,
        "repository_counts": repo_counts,
        "thtk_counts": thtk_counts,
        "repository_timeline_terminal_record_count": terminal_count,
        "opcode_sequence_count": len(repo_opcodes),
        "opcode_sequence_sha256": _sha256_bytes(
            b"".join(opcode.to_bytes(2, "little") for opcode in repo_opcodes)
        ),
        "structural_counts_and_opcode_sequence_exact_match": True,
        "thtk_listing_size": len(listing),
        "thtk_listing_sha256": _sha256_bytes(listing),
        "stdout_sha256": _sha256_bytes(result.stdout),
        "stderr_sha256": _sha256_bytes(result.stderr),
    }


def _std_probe(
    path: Path,
    *,
    thstd: Path,
    output: Path,
) -> dict[str, object]:
    result = _run(
        [str(thstd), "-d8", str(path), str(output)],
        require_success=False,
    )
    payload = output.read_bytes() if output.exists() else b""
    return {
        "name": path.name,
        "decoded_sha256": _sha256_path(path),
        "success": result.returncode == 0,
        "termination": _termination(result.returncode),
        "output_size": len(payload),
        "output_sha256": _sha256_bytes(payload),
        "stdout_sha256": _sha256_bytes(result.stdout),
        "stderr_size": len(result.stderr),
        "stderr_sha256": _sha256_bytes(result.stderr),
    }


def build_content_manifest(
    *,
    archive_path: Path,
    executable_path: Path,
    thtk_source: Path,
    thdat: Path,
    thecl: Path,
    thstd: Path,
    repo_root: Path,
) -> dict[str, object]:
    archive_sha256 = _sha256_path(archive_path)
    if archive_sha256 != EXPECTED_ARCHIVE_SHA256:
        raise ContentManifestError("unexpected shipped th08.dat SHA-256")
    executable_sha256 = _sha256_path(executable_path)
    if executable_sha256 != EXPECTED_EXECUTABLE_SHA256:
        raise ContentManifestError("unexpected shipped th08.exe SHA-256")

    external = _validate_external_source(thtk_source)
    external["tools"] = {
        "thdat": _tool_record(thdat),
        "thecl": _tool_record(thecl),
        "thstd": _tool_record(thstd),
    }

    archive = PbgzArchive(archive_path)
    list_result = _run(
        [str(thdat), "-l8", str(archive_path)],
        require_success=True,
    )
    thdat_rows = _parse_thdat_list(list_result.stdout)
    _validate_directory(thdat_rows, archive.entries)

    content_entries = tuple(
        entry
        for entry in archive.entries
        if _content_category(entry.name) is not None
    )
    if len(content_entries) != EXPECTED_CONTENT_ASSET_COUNT:
        raise ContentManifestError(
            f"selected {len(content_entries)} content assets, expected "
            f"{EXPECTED_CONTENT_ASSET_COUNT}"
        )

    with TemporaryDirectory(prefix="th08-content-manifest-") as directory:
        temporary = Path(directory)
        extracted = temporary / "thtk-extracted"
        extracted.mkdir()
        extract_result = _run(
            [
                str(thdat),
                "-gx8",
                str(archive_path),
                "-C",
                str(extracted),
                *CONTENT_GLOBS,
            ],
            require_success=True,
        )
        extracted_names = {
            path.name for path in extracted.iterdir() if path.is_file()
        }
        expected_names = {entry.name for entry in content_entries}
        if extracted_names != expected_names:
            raise ContentManifestError(
                "thdat extracted content-name set disagrees with repository "
                "selection"
            )

        assets: list[dict[str, object]] = []
        for entry in content_entries:
            wrapped = archive.extract(entry)
            decoded = decode_resource(wrapped, require_wrapper=True)
            thtk_decoded = (extracted / entry.name).read_bytes()
            assets.append(
                _asset_record(
                    entry,
                    wrapped=wrapped,
                    decoded=decoded,
                    thtk_decoded=thtk_decoded,
                    repo_root=repo_root,
                )
            )

        ecl_output = temporary / "thecl"
        ecl_output.mkdir()
        ecl_differentials = [
            _ecl_differential(
                extracted / entry.name,
                thecl=thecl,
                output=ecl_output / f"{entry.name}.txt",
            )
            for entry in content_entries
            if _content_category(entry.name) == "ecl"
        ]

        mandatory_std_names = sorted(
            asset["name"]
            for asset in assets
            if asset["category"] == "std"
            and asset["mandatory_scene_tags"]
        )
        std_output = temporary / "thstd"
        std_output.mkdir()
        std_probes = [
            _std_probe(
                extracted / name,
                thstd=thstd,
                output=std_output / f"{name}.txt",
            )
            for name in mandatory_std_names
        ]

    category_counts = Counter(str(asset["category"]) for asset in assets)
    tracked_wrapped_count = sum(
        asset["tracked_wrapped"] is not None for asset in assets
    )
    tracked_decoded_count = sum(
        asset["tracked_decoded"] is not None for asset in assets
    )
    mandatory_scenes: dict[str, object] = {}
    for scene, metadata in MANDATORY_SCENE_METADATA.items():
        scene_assets = [
            asset
            for asset in assets
            if scene in asset["mandatory_scene_tags"]
        ]
        names = sorted(str(asset["name"]) for asset in scene_assets)
        if not names:
            raise ContentManifestError(
                f"mandatory scene {scene} has no scoped assets"
            )
        mandatory_scenes[scene] = {
            **metadata,
            "selection_authority": "filename_scoped_not_runtime_load_proof",
            "asset_count": len(names),
            "content_set_sha256": _content_set_sha256(scene_assets),
            "assets": names,
        }

    failed_std = [probe["name"] for probe in std_probes if not probe["success"]]
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "taskbook_card": TASKBOOK_CARD,
        "shipped_identity": {
            "archive_label": "th08.dat",
            "archive_size": archive_path.stat().st_size,
            "archive_sha256": archive_sha256,
            "executable_label": "th08.exe",
            "executable_size": executable_path.stat().st_size,
            "executable_sha256": executable_sha256,
        },
        "external_oracle": external,
        "archive_directory_differential": {
            "entry_count": len(archive.entries),
            "directory_offset": archive.directory_offset,
            "directory_size": archive.directory_size,
            "directory_padding_size": archive.directory_padding_size,
            "thdat_repository_name_size_stored_exact_match": True,
            "thdat_list_stdout_sha256": _sha256_bytes(list_result.stdout),
            "thdat_list_stderr_sha256": _sha256_bytes(list_result.stderr),
        },
        "content_scope": {
            "globs": list(CONTENT_GLOBS),
            "asset_count": len(assets),
            "category_counts": {
                key: category_counts[key] for key in sorted(category_counts)
            },
            "content_set_sha256": _content_set_sha256(assets),
            "all_thtk_repository_decoded_payloads_exact": True,
            "tracked_wrapped_exact_count": tracked_wrapped_count,
            "tracked_decoded_exact_count": tracked_decoded_count,
            "thdat_extract_stdout_sha256": _sha256_bytes(
                extract_result.stdout
            ),
            "thdat_extract_stderr_sha256": _sha256_bytes(
                extract_result.stderr
            ),
        },
        "assets": assets,
        "mandatory_scenes": mandatory_scenes,
        "ecl_structural_differential": {
            "file_count": len(ecl_differentials),
            "all_exact": True,
            "files": ecl_differentials,
        },
        "mandatory_std_external_parser_probe": {
            "file_count": len(std_probes),
            "success_count": len(std_probes) - len(failed_std),
            "failure_count": len(failed_std),
            "all_succeeded": not failed_std,
            "failed_files": failed_std,
            "authority": (
                "diagnostic_external_tool_compatibility_only; archive "
                "extraction/decode parity remains independently exact"
            ),
            "files": std_probes,
        },
        "classification": {
            "content_identity_gate_passed": True,
            "mandatory_stage_versions_pinned": True,
            "archive_format_boundary_exact": True,
            "resource_decode_boundary_exact": True,
            "ecl_structural_boundary_exact": True,
            "external_std_parser_complete": not failed_std,
            "std_failure_blocks_content_identity": False,
        },
        "authority": {
            "kind": "offline_shipped_content_identity",
            "runtime_load_or_order_authority": False,
            "opcode_or_side_effect_authority": False,
            "event_reachability_authority": False,
            "planner_or_action_authority": False,
            "physical_trial_run": False,
        },
        "next_gate": {
            "taskbook_card": "CONTENT-02",
            "goal": (
                "build a symbolic mandatory-stage event atlas using only "
                "independently parsed ECL records, then join observed native "
                "events to exact content version and instruction offset"
            ),
            "thstd_failures_must_not_be_treated_as_missing_shipped_content": True,
        },
    }
    digest_payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_digest"] = _sha256_bytes(digest_payload)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--thtk-source", type=Path, required=True)
    parser.add_argument("--thdat", type=Path, required=True)
    parser.add_argument("--thecl", type=Path, required=True)
    parser.add_argument("--thstd", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    report = build_content_manifest(
        archive_path=args.archive,
        executable_path=args.executable,
        thtk_source=args.thtk_source,
        thdat=args.thdat,
        thecl=args.thecl,
        thstd=args.thstd,
        repo_root=repo_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
