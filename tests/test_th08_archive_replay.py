from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from th08_replay import ReplayMetadata
from th08_replay_archive import archive_replay


class ReplayArchiveTests(unittest.TestCase):
    def test_archive_is_content_addressed_and_idempotent(self) -> None:
        metadata = ReplayMetadata(
            name="th8_15.rpy",
            sha256="12" * 32,
            file_size=6,
            encoded_main_size=6,
            compressed_size=0,
            uncompressed_size=0,
            trailing_size=0,
            checksum=0,
            rolling_key=0,
            route_id=2,
            difficulty_index=3,
            extended_input_records=False,
            stages=(),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "th8_15.rpy"
            source.write_bytes(b"replay")
            archive_dir = root / "archive"
            manifest = root / "manifest.json"

            def decode(path: Path) -> tuple[ReplayMetadata, bytes]:
                self.assertEqual(path.read_bytes(), b"replay")
                return metadata, b"decoded"

            with patch(
                "th08_replay_archive.decode_replay",
                side_effect=decode,
            ):
                first = archive_replay(
                    source,
                    archive_dir,
                    manifest=manifest,
                )
                second = archive_replay(
                    source,
                    archive_dir,
                    manifest=manifest,
                )
            self.assertEqual(first["copy_status"], "copied")
            self.assertEqual(second["copy_status"], "already_present")
            self.assertEqual(len(tuple(archive_dir.iterdir())), 1)
            self.assertEqual(
                json.loads(manifest.read_text(encoding="utf-8"))[
                    "metadata"
                ]["sha256"],
                metadata.sha256,
            )


if __name__ == "__main__":
    unittest.main()
