"""Strict auxiliary-ECL pointer density and churn analysis."""

from .report import (
    AuxiliaryPointerReportError,
    build_auxiliary_pointer_report,
    canonical_report_bytes,
)

__all__ = [
    "AuxiliaryPointerReportError",
    "build_auxiliary_pointer_report",
    "canonical_report_bytes",
]
