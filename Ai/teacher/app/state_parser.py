"""
Pure state parser: no DB imports. Returns list[ProposedTransition].
"""
import re
from typing import Any, List

from state_schema import ProposedTransition


def parse_state_updates(response: str, current_state: dict[str, Any]) -> List[ProposedTransition]:
    """
    Parse assistant response for method locks and stage transitions.
    Returns proposals only; no DB or state mutation.
    """
    proposals: List[ProposedTransition] = []

    # Method lock: "Method N — name locked" or "Method N - df.shape locked"
    match = re.search(
        r"Method\s+(\d+)\s*[—–-]\s*[`]?(\S+?)[`]?\s+locked",
        response,
        re.IGNORECASE,
    )
    if match:
        num = int(match.group(1))
        name = match.group(2).strip("`").strip()
        proposals.append(
            ProposedTransition(
                action="method_lock",
                method_number=num,
                method_name=name,
                parser_mode="regex",
            )
        )
    else:
        # "Method N locked" — find name from earlier in response
        match2 = re.search(r"Method\s+(\d+)\s+locked", response, re.IGNORECASE)
        if match2:
            num = int(match2.group(1))
            name_match = re.search(
                rf"Method\s+{num}\s*[—–\-:]\s*[`]?([^\s`\n]+)",
                response,
                re.IGNORECASE,
            )
            if name_match:
                name = name_match.group(1).strip("`").strip()
                proposals.append(
                    ProposedTransition(
                        action="method_lock",
                        method_number=num,
                        method_name=name,
                        parser_mode="regex",
                    )
                )

    # Stage transition: "Entering Stage S1" / "Proceeding to Stage S7A"
    stage_match = re.search(
        r"(?:Entering|Proceeding to)\s+Stage\s+(S?\d+[AB]?)\b",
        response,
        re.IGNORECASE,
    )
    if stage_match:
        raw = stage_match.group(1).upper()
        new_stage = raw if raw.startswith("S") else f"S{raw}"
        if new_stage != current_state.get("stage"):
            proposals.append(
                ProposedTransition(
                    action="stage_transition",
                    stage=new_stage,
                    parser_mode="regex",
                )
            )

    return proposals
