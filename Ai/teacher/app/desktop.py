"""
Data Analytics Apprenticeship — Flet Desktop App
Run:  python3 app/desktop.py
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from db import (
    init_db,
    create_session,
    save_message,
    get_conversation_history,
    get_system_state,
    get_stage_methods,
    update_system_state,
    build_resume_block,
    reset_for_new_run,
    close_session,
    generate_session_summary,
)
from orchestration import handle_user_message


def main(page: ft.Page):
    page.title = "Data Analytics Apprenticeship"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 900
    page.window.min_height = 600

    init_db()
    session_id = create_session()
    messages = []
    is_streaming = False

    # ── Chat bubble ───────────────────────────────────

    def make_bubble(role, text):
        is_user = role == "user"
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "You" if is_user else "Engine",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_200 if is_user else ft.Colors.ORANGE_300,
                    ),
                    ft.Markdown(
                        text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                        code_theme=ft.MarkdownCodeTheme.MONOKAI,
                        on_tap_link=lambda e: page.launch_url(e.data),
                        code_style_sheet=ft.MarkdownStyleSheet(
                            code_text_style=ft.TextStyle(size=12, font_family="Courier"),
                        ),
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.BLUE) if is_user else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            border_radius=12,
            padding=ft.Padding(left=16, right=16, top=12, bottom=12),
            margin=ft.Margin(
                left=60 if is_user else 0,
                right=0 if is_user else 60,
                top=0,
                bottom=8,
            ),
            alignment=ft.Alignment(1, 0) if is_user else ft.Alignment(-1, 0),
        )

    # ── Chat list ─────────────────────────────────────

    chat_list = ft.ListView(
        expand=True,
        spacing=0,
        auto_scroll=True,
        padding=ft.Padding(left=20, right=20, top=16, bottom=16),
    )

    # ── Streaming bubble ref ──────────────────────────

    streaming_md = ft.Markdown(
        "",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        code_theme=ft.MarkdownCodeTheme.MONOKAI,
        code_style_sheet=ft.MarkdownStyleSheet(
            code_text_style=ft.TextStyle(size=12, font_family="Courier"),
        ),
    )

    streaming_bubble = ft.Container(
        content=ft.Column(
            [
                ft.Text("Engine", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_300),
                streaming_md,
            ],
            spacing=4,
            tight=True,
        ),
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        border_radius=12,
        padding=ft.Padding(left=16, right=16, top=12, bottom=12),
        margin=ft.Margin(left=0, right=60, top=0, bottom=8),
        visible=False,
    )

    # ── State panel ───────────────────────────────────

    state_labels = {}
    fields = [
        ("stage", "🧭 Stage"),
        ("stack", "🛠 Stack"),
        ("shape", "📊 Shape"),
        ("scope", "🎯 Scope"),
        ("artifacts", "📂 Artifacts"),
        ("last_hardened", "🔒 Hardened"),
        ("kpis", "📈 KPIs"),
        ("nb_done", "🔬 NB Done"),
        ("next_action", "➡️ Next"),
    ]

    state_column = ft.Column(spacing=2, tight=True)
    for key, label in fields:
        t = ft.Text(f"{label}: —", size=11, color=ft.Colors.WHITE70)
        state_labels[key] = t
        state_column.controls.append(t)

    methods_column = ft.Column(spacing=2, tight=True)

    def refresh_state():
        state = get_system_state()
        for key, t in state_labels.items():
            val = state.get(key, "—")
            label = fields[[f[0] for f in fields].index(key)][1]
            t.value = f"{label}: {val}"

        methods_column.controls.clear()
        meths = get_stage_methods(state["stage"])
        if meths:
            for m in meths:
                icon = "✅" if m["locked"] else "⬜"
                methods_column.controls.append(
                    ft.Text(f"{icon} {m['method_name']}", size=11, color=ft.Colors.WHITE70)
                )
        else:
            methods_column.controls.append(
                ft.Text("No methods tracked", size=11, color=ft.Colors.WHITE38)
            )
    

    def new_session(e):
        nonlocal session_id, messages
        close_session(session_id)
        generate_session_summary(session_id)
        session_id = create_session()
        messages.clear()
        chat_list.controls.clear()
        resume = build_resume_block()
        chat_list.controls.append(make_bubble("assistant", resume))
        save_message(session_id, "assistant", resume, status="complete")
        refresh_state()
        page.update()

    def new_run(e):
        nonlocal session_id, messages
        close_session(session_id)
        generate_session_summary(session_id)
        reset_for_new_run()
        session_id = create_session()
        messages.clear()
        chat_list.controls.clear()
        resume = build_resume_block()
        chat_list.controls.append(make_bubble("assistant", resume))
        save_message(session_id, "assistant", resume, status="complete")
        refresh_state()
        page.update()

    def resume_session(e):
        messages.clear()
        chat_list.controls.clear()
        resume = build_resume_block()
        chat_list.controls.append(make_bubble("assistant", resume))
        save_message(session_id, "assistant", resume, status="complete")
        page.update()

    STAGE_NAMES = {
        "S0": "SETUP", "S1": "LOAD", "S2": "INSPECT", "S3": "CLEAN",
        "S4": "SELECT", "S5": "TRANSFORM", "S6": "TRANSFORM",
        "S7A": "AGGREGATE (Pandas)", "S7B": "AGGREGATE (SQL)",
        "S8": "SLA ENGINE", "S9": "INTELLIGENCE ENGINE",
        "S10": "VALIDATE", "S11": "PRESENT", "S12": "AUTOMATE",
    }

    stage_practice_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(key=s, text=f"{s} — {n}") for s, n in STAGE_NAMES.items()],
        value=get_system_state()["stage"],
        width=200,
        text_size=12,
    )

    def practice_stage(e):
        nonlocal session_id, messages
        target = stage_practice_dropdown.value
        name = STAGE_NAMES.get(target, target)
        update_system_state(stage=target, stage_name=name)
        close_session(session_id)
        generate_session_summary(session_id)
        session_id = create_session()
        messages.clear()
        chat_list.controls.clear()
        resume = build_resume_block(stage=target)
        chat_list.controls.append(make_bubble("assistant", resume))
        save_message(session_id, "assistant", resume, status="complete")
        refresh_state()
        page.update()

    state_panel = ft.Container(
        content=ft.Column(
            [
                ft.Text("📌 System State", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                ft.Divider(height=1, color=ft.Colors.WHITE12),
                state_column,
                ft.Container(height=12),
                ft.Text("📋 Methods", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                methods_column,
                ft.Container(height=12),
                ft.Text("🎯 Stage Practice", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                stage_practice_dropdown,
                ft.Button("Practice This Stage", on_click=practice_stage, width=200),
                ft.Container(expand=True),
                ft.Button("▶️ Resume", on_click=resume_session, width=200),
                ft.Container(height=4),
                ft.Button("New Session", icon=ft.Icons.REFRESH, on_click=new_session, width=200),
                ft.Container(height=4),
                ft.Button("New Run", icon=ft.Icons.REPLAY, on_click=new_run, width=200),
            ],
            spacing=6,
            expand=True,
        ),
        width=250,
        bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
        border=ft.Border(left=ft.BorderSide(1, ft.Colors.WHITE12), top=None, right=None, bottom=None),
        padding=16,
    )

    # ── Input bar ─────────────────────────────────────

    input_field = ft.TextField(
        hint_text="Paste output, ask a question, or say 'begin'...",
        border_radius=8,
        filled=True,
        expand=True,
        text_size=14,
        content_padding=ft.Padding(left=16, right=16, top=12, bottom=12),
        on_submit=lambda e: send_message(e),
    )

    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.BLUE_200,
        icon_size=24,
        on_click=lambda e: send_message(e),
    )

    # ── Send logic ────────────────────────────────────

    def send_message(e):
        nonlocal is_streaming
        text = input_field.value.strip()
        if not text or is_streaming:
            return

        is_streaming = True
        input_field.value = ""
        input_field.disabled = True
        send_btn.disabled = True
        page.update()

        # User bubble
        chat_list.controls.append(make_bubble("user", text))
        messages.append({"role": "user", "content": text})

        # Show streaming bubble
        streaming_md.value = "⏳"
        streaming_bubble.visible = True
        chat_list.controls.append(streaming_bubble)
        page.update()

        # Stream in background thread via orchestration
        client = OpenAI(api_key=OPENAI_API_KEY)

        def stream():
            nonlocal is_streaming
            try:
                def on_chunk(text):
                    streaming_md.value = text
                    page.update()

                full = handle_user_message(
                    session_id,
                    text,
                    client,
                    model=OPENAI_MODEL,
                    on_chunk=on_chunk,
                )

                # Done streaming — replace with final bubble
                chat_list.controls.remove(streaming_bubble)
                streaming_bubble.visible = False
                chat_list.controls.append(make_bubble("assistant", full))
                messages.append({"role": "assistant", "content": full})
                refresh_state()

            except Exception as ex:
                streaming_md.value = f"⚠️ Error: {ex}"

            finally:
                is_streaming = False
                input_field.disabled = False
                send_btn.disabled = False
                page.update()

        threading.Thread(target=stream, daemon=True).start()

    # ── Layout ────────────────────────────────────────

    # Auto-resume block on startup
    resume = build_resume_block()
    chat_list.controls.append(make_bubble("assistant", resume))

    # Load existing history
    history = get_conversation_history(session_id)
    if history:
        chat_list.controls.clear()
        for msg in history:
            chat_list.controls.append(make_bubble(msg["role"], msg["content"]))
        messages.extend(history)

    refresh_state()

    input_bar = ft.Container(
        content=ft.Row([input_field, send_btn], spacing=8),
        padding=ft.Padding(left=20, right=20, top=12, bottom=12),
        border=ft.Border(top=ft.BorderSide(1, ft.Colors.WHITE12), left=None, right=None, bottom=None),
    )

    title_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("🔧 Data Analytics Apprenticeship", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("One method at a time.", size=12, color=ft.Colors.WHITE38, italic=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=20, right=20, top=12, bottom=12),
        border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.WHITE12), left=None, right=None, top=None),
    )

    chat_area = ft.Column(
        [title_bar, chat_list, streaming_bubble, input_bar],
        expand=True,
        spacing=0,
    )

    page.add(
        ft.Row(
            [
                ft.Container(content=chat_area, expand=True),
                state_panel,
            ],
            expand=True,
            spacing=0,
        )
    )


ft.app(target=main)
