"""
Teacher proposal type for state transitions. No DB imports.
"""
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class ProposedTransition:
    """A single proposed state change from the parser."""
    action: Literal["none", "method_lock", "stage_transition"]
    parser_mode: Literal["json", "regex"] = "regex"
    # method_lock
    method_number: Optional[int] = None
    method_name: Optional[str] = None
    # stage_transition
    stage: Optional[str] = None
    # Set by engine on rejection
    rejection_reason: Optional[str] = None
