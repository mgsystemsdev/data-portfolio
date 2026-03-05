"""
Strict JSON schema validation for STATE_UPDATE blocks.
Rejects unknown fields, invalid enum values, and wrong types.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

ACTION_ENUM = frozenset({"none", "lock", "announce", "decompose", "topic_change"})
CONCEPT_NAME_MAX_LEN = 80
DECOMPOSITION_MAX_ITEMS = 20


@dataclass
class ProposedTransition:
    """A single proposed state transition from the parser. Engine validates and applies."""
    action: str  # none | lock | announce | decompose | topic_change
    parser_mode: str  # "json" | "regex"
    # Payload (action-dependent). None when action is "none".
    concept_number: Optional[int] = None
    concept_name: Optional[str] = None
    decomposition: Optional[list[str]] = None
    topic: Optional[str] = None
    raw_json: Optional[str] = None
    rejection_reason: Optional[str] = None

    def to_dict(self) -> dict:
        """For logging and state_events.proposed_state."""
        d: dict = {"action": self.action, "parser_mode": self.parser_mode}
        if self.concept_number is not None:
            d["concept_number"] = self.concept_number
        if self.concept_name is not None:
            d["concept_name"] = self.concept_name
        if self.decomposition is not None:
            d["decomposition"] = self.decomposition
        if self.topic is not None:
            d["topic"] = self.topic
        if self.rejection_reason is not None:
            d["rejection_reason"] = self.rejection_reason
        return d


def _is_str_list(lst: Any) -> bool:
    if not isinstance(lst, list):
        return False
    return all(isinstance(x, str) for x in lst)


def validate_state_update(data: dict) -> tuple[Optional[ProposedTransition], Optional[str]]:
    """
    Validate STATE_UPDATE JSON. Returns (ProposedTransition, None) if valid,
    or (None, error_message) / (ProposedTransition with rejection_reason, None) if invalid.
    Rejects unknown top-level keys and invalid enums/types.
    """
    if not isinstance(data, dict):
        return None, "root must be a JSON object"

    allowed_keys = {"action", "concept_number", "concept_name", "decomposition", "topic"}
    extra = set(data.keys()) - allowed_keys
    if extra:
        return None, f"unknown fields: {sorted(extra)}"

    action = data.get("action")
    if action is None:
        return None, "missing required field: action"
    if not isinstance(action, str):
        return None, "action must be a string"
    if action not in ACTION_ENUM:
        return None, f"invalid action: {action!r} (allowed: {sorted(ACTION_ENUM)})"

    if action == "none":
        return ProposedTransition(action="none", parser_mode="json"), None

    if action == "lock":
        cn = data.get("concept_number")
        name = data.get("concept_name")
        if cn is None:
            return None, "lock requires concept_number"
        if not isinstance(cn, int):
            return None, "concept_number must be an integer"
        if name is None:
            return None, "lock requires concept_name"
        if not isinstance(name, str):
            return None, "concept_name must be a string"
        if len(name) > CONCEPT_NAME_MAX_LEN:
            return None, f"concept_name must be at most {CONCEPT_NAME_MAX_LEN} characters"
        return ProposedTransition(
            action="lock",
            parser_mode="json",
            concept_number=cn,
            concept_name=name,
        ), None

    if action == "announce":
        name = data.get("concept_name")
        if name is None:
            return None, "announce requires concept_name"
        if not isinstance(name, str):
            return None, "concept_name must be a string"
        if len(name) > CONCEPT_NAME_MAX_LEN:
            return None, f"concept_name must be at most {CONCEPT_NAME_MAX_LEN} characters"
        return ProposedTransition(
            action="announce",
            parser_mode="json",
            concept_name=name,
        ), None

    if action == "decompose":
        decomp = data.get("decomposition")
        if decomp is None:
            return None, "decompose requires decomposition"
        if not _is_str_list(decomp):
            return None, "decomposition must be an array of strings"
        if len(decomp) > DECOMPOSITION_MAX_ITEMS:
            decomp = decomp[:DECOMPOSITION_MAX_ITEMS]
        return ProposedTransition(
            action="decompose",
            parser_mode="json",
            decomposition=decomp,
        ), None

    if action == "topic_change":
        topic = data.get("topic")
        if topic is None:
            return None, "topic_change requires topic"
        if not isinstance(topic, str):
            return None, "topic must be a string"
        return ProposedTransition(
            action="topic_change",
            parser_mode="json",
            topic=topic,
        ), None

    return None, f"unhandled action: {action}"
