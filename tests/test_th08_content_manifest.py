#!/usr/bin/env python3
"""Tests for the immutable TH08 content-manifest helpers."""

from __future__ import annotations

import unittest

from analysis.th08_content_manifest import (
    ContentManifestError,
    _content_set_sha256,
    _content_category,
    _parse_thdat_list,
    _parse_thecl_opcodes,
    _parse_thecl_structure,
    _scene_tags,
    _termination,
)


class ContentManifestTests(unittest.TestCase):
    def test_thdat_list_parser_preserves_order_and_sizes(self) -> None:
        rows = _parse_thdat_list(
            b"Name Size Stored\n"
            b"ecldata3.ecl 50244 15451\n"
            b"stage3.std 2832 1582\n"
        )
        self.assertEqual(
            [(row.name, row.uncompressed_size, row.compressed_size) for row in rows],
            [
                ("ecldata3.ecl", 50244, 15451),
                ("stage3.std", 2832, 1582),
            ],
        )
        with self.assertRaises(ContentManifestError):
            _parse_thdat_list(b"unexpected\n")

    def test_content_categories_and_mandatory_scene_tags_are_explicit(self) -> None:
        self.assertEqual(_content_category("ecldata7.ecl"), "ecl")
        self.assertEqual(_content_category("stage4a_s.std"), "std")
        self.assertEqual(_content_category("stg5bg.anm"), "anm")
        self.assertEqual(_content_category("msg3c.dat"), "msg")
        self.assertIsNone(_content_category("th08_01.mid"))
        self.assertEqual(_scene_tags("face_st05msp.anm"), ("stage5",))
        self.assertEqual(_scene_tags("msg4ac.dat"), ("stage4a",))
        self.assertEqual(_scene_tags("ecldata7sp.ecl"), ("final_b",))
        self.assertEqual(_scene_tags("etama.anm"), ())

    def test_thecl_structure_counts_raw_instruction_lines(self) -> None:
        counts = _parse_thecl_structure(
            b"sub Sub0()\n{\n"
            b"    ins_1();\n"
            b"!ENHL57    ins_97(1);\n"
            b"}\n"
            b"timeline Timeline0()\n{\n"
            b"    ins_2(\"Sub0\");\n"
            b"-1:\n"
            b"    ins_7();\n"
            b"}\n"
        )
        self.assertEqual(
            counts,
            {
                "subroutine_count": 1,
                "timeline_count": 1,
                "instruction_line_count": 4,
            },
        )
        self.assertEqual(_parse_thecl_opcodes(
            b"sub Sub0()\n{\n"
            b"    ins_1();\n"
            b"!ENHL57    ins_97(1);\n"
            b"}\n"
            b"timeline Timeline0()\n{\n"
            b"    ins_2(\"Sub0\");\n"
            b"-1:\n"
            b"    ins_7();\n"
            b"}\n"
        ), (1, 97, 2, 7))

    def test_external_tool_termination_keeps_signal_distinct_from_exit(self) -> None:
        self.assertEqual(
            _termination(-11),
            {"kind": "signal", "number": 11, "name": "SIGSEGV"},
        )
        self.assertEqual(_termination(0), {"kind": "exit", "code": 0})

    def test_content_set_digest_is_order_independent(self) -> None:
        first = [
            {"name": "b.std", "decoded_sha256": "22"},
            {"name": "a.ecl", "decoded_sha256": "11"},
        ]
        second = list(reversed(first))
        self.assertEqual(
            _content_set_sha256(first),
            _content_set_sha256(second),
        )


if __name__ == "__main__":
    unittest.main()
