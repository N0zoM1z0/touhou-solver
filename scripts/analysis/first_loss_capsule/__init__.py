"""First-loss exact-root selection and restricted witness audit."""

from .report import audit
from .selection import select_first_loss_bracket
from .types import FirstLossBracket, FirstLossSelection

__all__ = [
    "FirstLossBracket",
    "FirstLossSelection",
    "audit",
    "select_first_loss_bracket",
]
