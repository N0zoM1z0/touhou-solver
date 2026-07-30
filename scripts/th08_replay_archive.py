"""Content-addressed retention for user-generated TH08 replay inputs."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from th08_replay import decode_replay


SCHEMA = "th08-content-addressed-replay-archive-v1"


def archive_replay(
    source: Path,
    archive_dir: Path,
    *,
    manifest: Path | None = None,
) -> dict[str, object]:
    metadata, _decoded = decode_replay(source)
    suffix = source.suffix.lower() or ".rpy"
    archived = archive_dir / (
        f"{source.stem}_{metadata.sha256}{suffix}"
    )
    archive_dir.mkdir(parents=True, exist_ok=True)
    if archived.exists():
        archived_metadata, _ = decode_replay(archived)
        if archived_metadata.sha256 != metadata.sha256:
            raise RuntimeError(
                "content-addressed replay archive path has wrong bytes"
            )
        copy_status = "already_present"
    else:
        shutil.copy2(source, archived)
        archived_metadata, _ = decode_replay(archived)
        if archived_metadata.sha256 != metadata.sha256:
            archived.unlink(missing_ok=True)
            raise RuntimeError("archived replay failed post-copy identity")
        copy_status = "copied"

    record = {
        "schema": SCHEMA,
        "archived_at": datetime.now().astimezone().isoformat(),
        "source": source.as_posix(),
        "archive": archived.as_posix(),
        "copy_status": copy_status,
        "metadata": asdict(metadata),
    }
    target_manifest = manifest or archive_dir / (
        f"{source.stem}_{metadata.sha256}_manifest.json"
    )
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    target_manifest.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**record, "manifest": target_manifest.as_posix()}


__all__ = ["SCHEMA", "archive_replay"]
