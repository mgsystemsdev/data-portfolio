"""
Orchestration: single entry point for handling user messages. Saves messages,
streams API response, then runs parser + transition engine only when assistant
message is complete.
"""
import hashlib
import json
import time

from config import OPENAI_MODEL
from db import (
    save_message,
    get_conversation_history,
    get_system_state,
    set_message_status,
    set_message_content,
    update_system_state,
    get_last_locked_stage,
)
from prompts import build_system_prompt
from learner_analytics import analyze_user_message, refresh_learner_profile
from state_parser import parse_state_updates
from transition_engine import apply_transitions


def _prompt_hash(system_prompt: str, messages: list) -> str:
    return hashlib.sha256((system_prompt + json.dumps(messages)).encode()).hexdigest()[:16]


def handle_user_message(session_id: int, user_message: str, client, model=None, on_chunk=None):
    """
    Save user message, run analytics, build prompt, save assistant row as pending,
    stream API response, on completion mark complete and run parser + transition engine.
    Returns full assistant response text.
    """
    state = get_system_state()
    save_message(session_id, "user", user_message, stage=state.get("stage"))
    analyze_user_message(session_id, user_message, state.get("stage", "S0"))

    # Safety guard: handoff_mode requires at least one locked stage (not S0)
    if state.get("handoff_mode") == 1:
        last_locked = get_last_locked_stage()
        if last_locked is None or last_locked == "S0":
            safety_content = (
                "Stage must be completed before generating a handout.\n\n"
                "<<<STATE_UPDATE_START>>>\n"
                '{"action":"none"}\n'
                "<<<STATE_UPDATE_END>>>"
            )
            save_message(
                session_id,
                "assistant",
                safety_content,
                stage=state.get("stage"),
                status="complete",
            )
            update_system_state(handoff_mode=0)
            return safety_content

    try:
        system_prompt = build_system_prompt(state=state)
    except Exception:
        system_prompt = "You are the Data Analytics Apprenticeship. Teach one concept at a time. Current stage: " + (state.get("stage") or "S0")
    history = get_conversation_history(session_id)
    api_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in history
    ]
    prompt_hash = _prompt_hash(system_prompt, api_messages)

    assistant_message_id = save_message(
        session_id,
        "assistant",
        "",
        stage=state.get("stage"),
        status="pending",
        prompt_hash=prompt_hash,
    )

    full_response = ""
    _last_ui_update = 0.0
    try:
        stream = client.chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=api_messages,
            stream=True,
            temperature=0.3,
            max_tokens=4096,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_response += delta.content
                if on_chunk:
                    now = time.monotonic()
                    if now - _last_ui_update >= 0.08:
                        on_chunk(full_response)
                        _last_ui_update = now
        if on_chunk:
            on_chunk(full_response)
        set_message_status(assistant_message_id, "complete")
        set_message_content(assistant_message_id, full_response)
    except Exception:
        set_message_status(assistant_message_id, "failed")
        raise

    # Handout mode: skip parse/apply, reset and return
    if state.get("handoff_mode") == 1:
        update_system_state(handoff_mode=0)
        return full_response

    # Parse and apply transitions when complete
    proposals = parse_state_updates(full_response, state)
    apply_transitions(assistant_message_id, proposals, state, prompt_version=prompt_hash)

    # Refresh learner profile after transitions so it's ready for the next message
    refresh_learner_profile()

    return full_response
