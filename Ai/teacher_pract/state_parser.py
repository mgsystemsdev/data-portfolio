"""
State parser — extracts proposed state transitions from assistant responses.
Pure: no DB access. Returns list of ProposedTransition for the transition engine.
"""

import re
import json
from typing import List

from state_schema import ProposedTransition, validate_state_update

STATE_UPDATE_START = "<<<STATE_UPDATE_START>>>"
STATE_UPDATE_END = "<<<STATE_UPDATE_END>>>"


def parse_state_updates(response: str, current_state: dict) -> List[ProposedTransition]:
    """
    Parse state changes from an assistant response.
    Returns a list of ProposedTransition (0 or 1 for strict format; possibly multiple from regex fallback).
    Parser does not touch the DB; call transition_engine.apply_transitions() with the result.
    """
    response = response.strip() if response else ""

    # 1. Strict format: exactly one block at end of message
    proposals = _parse_strict_block(response)
    if proposals is not None:
        return proposals  # list of 0 or 1 (0 if action was "none" or rejected)

    # 2. Fallback: regex (flagged as parser_mode="regex"; engine will not apply lock/promote from regex)
    return _parse_regex(response, current_state)


def _parse_strict_block(response: str) -> List[ProposedTransition] | None:
    """
    Require <<<STATE_UPDATE_START>>> ... <<<STATE_UPDATE_END>>> once at end of message.
    Returns list of proposals if block found (valid or invalid); None if no block (caller may use regex).
    """
    if STATE_UPDATE_START not in response or STATE_UPDATE_END not in response:
        return None

    # Must appear once and at end (after trailing whitespace)
    end_idx = response.rfind(STATE_UPDATE_END)
    if end_idx == -1:
        return None
    after_end = response[end_idx + len(STATE_UPDATE_END) :].strip()
    if after_end:
        return None  # block not at end

    start_idx = response.rfind(STATE_UPDATE_START)
    if start_idx == -1 or start_idx > end_idx:
        return None

    between = response[start_idx + len(STATE_UPDATE_START) : end_idx].strip()
    # Single line of JSON (no embedded newlines)
    if "\n" in between:
        return [ProposedTransition(
            action="none",
            parser_mode="json",
            raw_json=between,
            rejection_reason="STATE_UPDATE JSON must be a single line",
        )]

    try:
        data = json.loads(between)
    except json.JSONDecodeError as e:
        return [ProposedTransition(
            action="none",
            parser_mode="json",
            raw_json=between,
            rejection_reason=f"Invalid JSON: {e}",
        )]

    transition, err = validate_state_update(data)
    if err:
        return [ProposedTransition(
            action=data.get("action", "none"),
            parser_mode="json",
            raw_json=between,
            rejection_reason=err,
        )]
    if transition.action == "none":
        return []
    return [transition]


def _parse_regex(response: str, current_state: dict) -> List[ProposedTransition]:
    """Regex-based extraction. All proposals get parser_mode='regex'; engine restricts destructive actions."""
    topic = current_state.get("topic", "None")
    category = current_state.get("category", "general")
    proposals: List[ProposedTransition] = []

    # Topic transition
    topic_match = re.search(
        r"(?:Moving to|Entering)\s+topic\s+([A-Za-z0-9_\s]+?)(?:\s*$|\.|,)",
        response,
        re.IGNORECASE,
    )
    if topic_match:
        new_topic = topic_match.group(1).strip()
        if new_topic != topic:
            proposals.append(ProposedTransition(
                action="topic_change",
                parser_mode="regex",
                topic=new_topic,
            ))

    # Lock: regex may produce lock; engine will reject lock from regex (no destructive actions)
    locked_detected = False
    match = re.search(
        r"Concept\s+(\d+)\s*[—–-]\s*([^`\n]+?)\s+locked",
        response,
        re.IGNORECASE,
    )
    if not match:
        match2 = re.search(r"Concept\s+(\d+)\s+locked", response, re.IGNORECASE)
        if match2:
            num = int(match2.group(1))
            name_match = re.search(
                rf"Concept\s+{num}\s*[—–\-:]\s*[`]?([^\n`]+)",
                response,
                re.IGNORECASE,
            )
            if name_match:
                name = name_match.group(1).strip("`").strip()
                proposals.append(ProposedTransition(
                    action="lock",
                    parser_mode="regex",
                    concept_number=num,
                    concept_name=name,
                ))
                locked_detected = True
    if match:
        num = int(match.group(1))
        name = match.group(2).strip("`").strip()
        proposals.append(ProposedTransition(
            action="lock",
            parser_mode="regex",
            concept_number=num,
            concept_name=name,
        ))
        locked_detected = True

    # Announce (only if no lock from this message)
    if not locked_detected:
        concept_announce = re.search(
            r"(?:^|\n)(?:Concept\s+\d+\s*[—–-]\s*)([^\n]+)",
            response,
            re.IGNORECASE,
        )
        if concept_announce:
            announced = concept_announce.group(1).strip().rstrip(".")
            if announced and len(announced) < 80:
                proposals.append(ProposedTransition(
                    action="announce",
                    parser_mode="regex",
                    concept_name=announced,
                ))

    # Decomposition
    decomp_match = re.search(
        r"(?:decomposition|concept map)[:\s]+([^\n]+(?:\n\s*\d+\.[^\n]+)*)",
        response,
        re.IGNORECASE,
    )
    if decomp_match:
        items = re.findall(r"\d+\.\s+([^\n]+)", response)
        if items:
            proposals.append(ProposedTransition(
                action="decompose",
                parser_mode="regex",
                decomposition=[i.strip() for i in items[:20]],
            ))

    return proposals


def strip_state_block(response: str) -> str:
    """Remove STATE_UPDATE blocks from response text for display (supports both delimiter formats)."""
    if not response:
        return response
    # New format
    s = re.sub(
        re.escape(STATE_UPDATE_START) + r".*?" + re.escape(STATE_UPDATE_END),
        "",
        response,
        flags=re.DOTALL,
    )
    # Legacy format
    s = re.sub(
        r"\s*<!--STATE_UPDATE.*?STATE_UPDATE-->\s*",
        "",
        s,
        flags=re.DOTALL,
    )
    return s.rstrip()
