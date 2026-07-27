"""Compatibility facade for replayable TH08 semantic cases."""

from th08_semantics import (
    DIFFICULTIES,
    FAMILIES,
    SCHEMA,
    SemanticCase,
    generate_case,
    generate_cases,
    shrink_case,
)

__all__ = [
    "DIFFICULTIES",
    "FAMILIES",
    "SCHEMA",
    "SemanticCase",
    "generate_case",
    "generate_cases",
    "shrink_case",
]
