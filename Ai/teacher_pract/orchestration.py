"""
Single entry for processing user messages: build prompt, call API, save messages, parse and apply transitions.
UI must only call handle_user_message(); it must not build prompts, call API directly, parse state, or mutate DB.
"""

import hashlib
import json
import time
from typing import Callable, Optional

from config import OPENAI_MODEL
from db import (
    get_system_state,
    save_message,
    set_message_status,
    get_conversation_history,
    log_parser_metric,
    update_system_state,
    all_handout_concepts_locked,
)
from prompts import build_system_prompt
from learner_analytics import analyze_user_message, refresh_learner_profile
from state_parser import parse_state_updates, strip_state_block
from transition_engine import apply_transitions


def _compute_prompt_hash(system_prompt: str, api_messages: list) -> str:
    """Deterministic hash for reproducibility and state_events."""
    payload = system_prompt + "\n" + json.dumps(api_messages, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def handle_user_message(
    session_id: int,
    user_message: str,
    *,
    client,
    max_context_messages: int = 30,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Single entry: load state, build prompt, call API, save user + assistant messages,
    run parser and transition engine. Returns full raw assistant response.
    On stream error, marks assistant message as 'failed' and re-raises.
    """
    state = get_system_state()

    # Save user message first so history includes it for prompt build
    save_message(
        session_id,
        "user",
        user_message,
        topic=state.get("topic"),
        concept=state.get("current_concept"),
    )

    analyze_user_message(
        session_id,
        user_message,
        state.get("topic", "None"),
        state.get("current_concept"),
    )

    # Handout mode safety: if active but no handout content, abort
    if state.get("handout_mode") == 1 and not state.get("active_handout"):
        no_handout_msg = "No active handout found.\n\n<<<STATE_UPDATE_START>>>\n{\"action\":\"none\"}\n<<<STATE_UPDATE_END>>>"
        save_message(
            session_id,
            "assistant",
            no_handout_msg,
            topic=state.get("topic"),
            concept=state.get("current_concept"),
            status="complete",
        )
        update_system_state(handout_mode=0)
        return no_handout_msg

    system_prompt = build_system_prompt(state=state)
    api_messages = [{"role": "system", "content": system_prompt}]
    history = get_conversation_history(session_id, limit=max_context_messages)
    api_messages.extend([{"role": m["role"], "content": m["content"]} for m in history])

    prompt_hash = _compute_prompt_hash(system_prompt, api_messages)

    # Save assistant message as pending (we'll get id and update to complete after stream)
    assistant_msg_id = save_message(
        session_id,
        "assistant",
        "",  # placeholder; we'll update content after stream
        topic=state.get("topic"),
        concept=state.get("current_concept"),
        status="pending",
        prompt_hash=prompt_hash,
    )

    full_response = ""
    _last_ui_update = 0.0
    try:
        # Handout drills are shorter; reduce max_tokens for faster responses
        response_limit = 2048 if state.get("handout_mode") == 1 else 4096
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=api_messages,
            stream=True,
            temperature=0.3,
            max_tokens=response_limit,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_response += delta.content
                if on_chunk:
                    now = time.monotonic()
                    if now - _last_ui_update >= 0.08:
                        on_chunk(strip_state_block(full_response) + "▌")
                        _last_ui_update = now
        if on_chunk:
            on_chunk(strip_state_block(full_response))
    except Exception:
        set_message_status(assistant_msg_id, "failed")
        raise

    # Update assistant row with full content and set status complete (required before parse/apply)
    from db import get_conn
    conn = get_conn()
    conn.execute(
        "UPDATE conversations SET content = ?, status = ? WHERE id = ?",
        (full_response, "complete", assistant_msg_id),
    )
    conn.commit()
    conn.close()

    # Parse and apply transitions (only when status = complete)
    proposals = parse_state_updates(full_response, state)
    # Handout mode: filter out decompose/topic_change to enforce isolation
    if state.get("handout_mode") == 1:
        proposals = [p for p in proposals if p.action not in ("decompose", "topic_change")]
    # Parser mode metrics for observability
    if any(getattr(p, "rejection_reason", None) for p in proposals):
        log_parser_metric("failed")
    elif any(p.parser_mode == "json" for p in proposals):
        log_parser_metric("json_success")
    elif any(p.parser_mode == "regex" for p in proposals):
        log_parser_metric("regex_fallback")
    else:
        log_parser_metric("json_success" if not proposals else "failed")
    apply_transitions(
        assistant_msg_id,
        proposals,
        state,
        prompt_version=prompt_hash,
    )

    # Handout mode: check if all handout concepts are now locked
    if state.get("handout_mode") == 1 and all_handout_concepts_locked(state):
        phase = state.get("handout_phase", "drill")
        if phase == "drill":
            # Drills complete → enter challenge phase (🔴 INDEPENDENT)
            update_system_state(handout_phase="challenge", handout_challenges_done=0)
        elif phase == "challenge":
            # Increment challenge counter when evaluation is detected (❌ ✅ 🚀 pattern)
            if "❌" in full_response and "✅" in full_response and "🚀" in full_response:
                done = state.get("handout_challenges_done", 0) + 1
                update_system_state(handout_challenges_done=done)
                # Only allow exit after minimum 2 challenges
                if done >= 2 and "stage complete" in full_response.lower():
                    update_system_state(handout_mode=0, active_handout=None, handout_phase="drill", handout_challenges_done=0)

    # Refresh learner profile after transitions so it's ready for the next message
    refresh_learner_profile()

    return full_response
