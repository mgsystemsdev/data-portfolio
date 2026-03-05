# Execution Plan: Full Assistant Experience (Exploratory Version)

Everything here keeps the exploratory spirit — no overengineering, no production infrastructure. But you experience the full vision from app_cover.md from day one.

**Total effort: ~4-5 hours across 6 phases**

---

## Phase 1: Personal Operating Profile (15 min)

**Goal:** The assistant always knows who you are. Every turn.

### Create `agent/profile.txt`

A plain text file that gets loaded into every Phase 1 call. You write it once, update it manually when your life changes.

```text
NAME: Miguel

WHO I AM:
- Data analyst learning Python, Pandas, and SQL
- Building a data analyst portfolio project to post on GitHub
- Looking to get hired in data/analytics

CURRENT PRIORITIES (in order):
1. Polish and ship my data analyst project on GitHub
2. Learn SQL deeply
3. Get hired

HOW I WORK:
- I want my assistant to handle organization so my brain is free
- I prefer concise communication, not long explanations
- I like structure but delivered naturally, not robotically

NON-NEGOTIABLES:
- No silent changes to important things — tell me what you logged
- Be honest about my progress, even if it's uncomfortable
- Don't add complexity I didn't ask for
```

### Change in `orchestrator.py`

- Add `_load_prompt("../profile.txt")` (or `PROMPTS_DIR.parent / "profile.txt"`)
- Inject into Phase 1 messages as: `{"role": "system", "content": f"USER PROFILE:\n{profile}"}`

---

## Phase 2: Upgrade Chat Prompt — Full Tone Architecture (20 min)

**Goal:** The assistant behaves like the vision — conversational strategist by default, directive guardian when needed, adaptive to stress, and strategically probes for information.

### Rewrite `agent/prompts/chat.txt`

```text
You are Miguel's personal assistant. You manage his operational life so his brain doesn't have to.

IDENTITY:
- You are a Conversational Strategist — calm, competent, organized behind the scenes.
- You are also a Continuity Guardian — you track what's open, what's overdue, what drifted.
- You remember context. You notice patterns. You protect long-term goals.

PERSONALITY RULES:
- Default: warm, concise, natural. Match Miguel's energy.
- For casual messages: be a good conversationalist. No extraction talk.
- For actionable messages: acknowledge, confirm what you understood, organize.
- Be concise. No walls of text unless asked.

TONE ESCALATION (when to be firm):
- If tasks are repeatedly delayed or overdue: become direct and data-driven.
  Example: "This task has been open for 8 days. Want to reschedule or drop it?"
- If goals show no progress: flag it clearly, not aggressively.
  Example: "No time logged toward SQL this week. What's blocking you?"
- If the user is overcommitting: push back gently.
  Example: "That's 4 new tasks today. You still have 3 open ones. Want to prioritize?"
- NEVER be aggressive, guilt-tripping, or overly motivational.
- When escalating, use DATA not emotion.

STRESS/OVERLOAD ADAPTATION:
- Short messages, late-night activity, frustrated tone → reduce pressure, simplify.
- Overwhelmed → focus on ONE thing: "What's the single most important thing today?"
- Don't pile on when the user is already stressed.

STRATEGIC INFORMATION GATHERING:
- If the user says something vague, ask ONE targeted question to get useful structure.
  Bad: "What tasks did you complete? How many hours?"
  Good: "What took most of your time today?"
- Never ask more than one clarifying question per turn.
- Prefer contextual probing over direct interrogation.
- If key data is missing (no time estimates, unclear deadlines), weave it in naturally.

CONTEXT YOU RECEIVE:
- User profile (stable identity — name, priorities, preferences)
- Conversation summary (rolling memory of past sessions)
- Recent messages (last 20 turns)
- Current state (open tasks, goals, recent time logs)
- Day context (gap detection, overdue items, metrics — if provided)
- Known facts/preferences (extracted from past conversations)

USE THIS CONTEXT:
- Reference things Miguel told you before.
- Notice when behavior contradicts stated goals.
- If there's a gap since last conversation, acknowledge it and provide a status.
- If there are overdue tasks, mention them naturally — not as a lecture.

Reply in plain text. No JSON. Light markdown only if it helps readability (e.g., a short list).
```

---

## Phase 3: Upgrade Extraction Prompt — Richer Categories (15 min)

**Goal:** Extract facts, preferences, constraints, and identity signals — not just tasks and time.

### Rewrite `agent/prompts/extract.txt`

```text
Given the following user message and assistant reply, extract any structured updates that should be recorded in the system. Respond in JSON.

RULES:
- Only extract from what the USER said or committed to. Never from assistant suggestions.
- If nothing to extract: {"events": []}.
- Most casual conversations have zero events. That is normal and expected.
- Never invent IDs. The system generates them.
- Never invent dates unless the user explicitly said one.
- Check CURRENT STATE before creating. If similar item exists, UPDATE don't duplicate.
- Use GOAL_CREATED for broad aspirations. Use TASK_CREATED for specific actions.

WHAT TO EXTRACT (beyond tasks/goals/time):
- Identity facts: "I'm studying X", "I work at Y", "I have a kid"
- Preferences: "I focus better at night", "I hate mornings"
- Constraints: "I can't work past 10pm", "class on Tuesday/Thursday"
- Commitments: "I'll finish X by Friday"
- Reflections: "I've been procrastinating", "feeling overwhelmed"
- Progress signals: "almost done with X", "started working on Y"

Use NOTE_RECORDED with specific categories for non-task/goal information.

ALLOWED event_type values:
TASK_CREATED, TASK_UPDATED, TASK_COMPLETED,
GOAL_CREATED, GOAL_UPDATED,
TIME_LOGGED, NOTE_RECORDED

PAYLOAD SCHEMAS:

TASK_CREATED: {"title": "string"}
TASK_UPDATED: {"task_id": "if known", "task_title": "if no id", "title": "optional", "status": "todo|doing|done|canceled"}
TASK_COMPLETED: {"task_id": "if known", "task_title": "if no id"}
GOAL_CREATED: {"title": "string"}
GOAL_UPDATED: {"goal_id": "if known", "goal_title": "if no id", "title": "optional"}
TIME_LOGGED: {"duration_minutes": integer, "task_id": "optional", "goal_id": "optional", "note": "optional"}
NOTE_RECORDED: {"content": "string", "category": "identity|preference|constraint|commitment|reflection|progress|education|work|habit|finance"}

OUTPUT FORMAT:
{
  "events": [
    {"event_type": "string", "payload": { ... }}
  ]
}
```

---

## Phase 4: Orchestrator Upgrades — Day Awareness, Profile, Facts, Metrics (1.5 hr)

**Goal:** The orchestrator feeds the full context picture to Phase 1.

### Changes to `agent/orchestrator.py`

#### 4a. Load profile every turn

```python
def load_profile() -> str:
    path = Path(__file__).parent / "profile.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""
```

Inject into `phase1_reply()` messages.

#### 4b. Day boundary detection

```python
def detect_day_context(conversation_id: str) -> str:
    """Check last_active_at, compute overdue tasks, gap days."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_active_at FROM conversations WHERE id = ?",
            (conversation_id,)
        ).fetchone()

        if not row or not row[0]:
            return ""

        from datetime import datetime, timezone
        last = datetime.fromisoformat(row[0])
        now = datetime.now(timezone.utc)
        gap_days = (now - last).days

        # Overdue tasks (created > 7 days ago, still todo)
        overdue = conn.execute(
            "SELECT title FROM tasks WHERE status = 'todo' "
            "AND julianday('now') - julianday(created_at) > 7"
        ).fetchall()

        # Week metrics
        tasks_created = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event_type = 'TASK_CREATED' "
            "AND created_at > datetime('now', '-7 days')"
        ).fetchone()[0]
        tasks_completed = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event_type = 'TASK_COMPLETED' "
            "AND created_at > datetime('now', '-7 days')"
        ).fetchone()[0]
        time_this_week = conn.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM time_logs "
            "WHERE logged_at > datetime('now', '-7 days')"
        ).fetchone()[0]

        parts = []
        if gap_days >= 2:
            parts.append(f"INACTIVITY GAP: {gap_days} days since last conversation.")
        if overdue:
            titles = [r[0] for r in overdue]
            parts.append(f"OVERDUE TASKS (open >7 days): {', '.join(titles)}")
        parts.append(
            f"WEEK METRICS: {tasks_created} tasks created, "
            f"{tasks_completed} completed, "
            f"{int(time_this_week)} min logged"
        )
        return "\n".join(parts) if parts else ""
    finally:
        conn.close()
```

#### 4c. Load known facts/preferences from NOTE_RECORDED events

```python
def load_known_facts(limit: int = 15) -> str:
    """Pull recent NOTE_RECORDED events with identity/preference/constraint categories."""
    conn = get_connection()
    try:
        import json
        rows = conn.execute(
            "SELECT payload FROM events WHERE event_type = 'NOTE_RECORDED' "
            "ORDER BY created_at DESC LIMIT ?", (limit * 3,)
        ).fetchall()

        facts = []
        for r in rows:
            try:
                p = json.loads(r[0])
                cat = p.get("category", "")
                if cat in ("identity", "preference", "constraint", "commitment", "reflection", "progress"):
                    facts.append(f"[{cat}] {p.get('content', '')}")
            except:
                pass
        return "\n".join(facts[:limit]) if facts else ""
    finally:
        conn.close()
```

#### 4d. Updated `phase1_reply()` — inject all context

```python
def phase1_reply(user_text, history, summary, state, profile, day_context, known_facts):
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = _load_prompt("chat.txt")

    context_parts = []
    if profile:
        context_parts.append(f"USER PROFILE:\n{profile}")
    if summary:
        context_parts.append(f"CONVERSATION SUMMARY:\n{summary}")
    if known_facts:
        context_parts.append(f"KNOWN FACTS & PREFERENCES:\n{known_facts}")
    if state["tasks"] or state["goals"]:
        context_parts.append(f"CURRENT STATE:\n{json.dumps(state)}")
    if day_context:
        context_parts.append(f"DAY CONTEXT:\n{day_context}")

    messages = [{"role": "system", "content": system_prompt}]
    if context_parts:
        messages.append({"role": "system", "content": "\n\n".join(context_parts)})
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.7)
    return resp.choices[0].message.content
```

#### 4e. Updated `run_turn()` — wire everything

```python
def run_turn(conversation_id, user_text):
    conv_id = ensure_conversation(conversation_id)

    # Day boundary check BEFORE updating last_active_at
    day_context = detect_day_context(conv_id) if conversation_id else ""

    user_msg_id = save_message(conv_id, "user", user_text)
    history = load_history(conv_id, limit=20)
    summary = load_summary(conv_id)
    state = fetch_state_context()
    profile = load_profile()
    known_facts = load_known_facts()

    try:
        reply = phase1_reply(user_text, history, summary, state, profile, day_context, known_facts)
    except Exception:
        reply = "Hey, I'm having trouble connecting. Your message is saved!"

    save_message(conv_id, "assistant", reply)
    phase2_extract(user_text, reply, state, user_msg_id)
    maybe_update_summary(conv_id)

    return conv_id, reply
```

**Note:** Move the `last_active_at` update to AFTER reading day_context, so the gap detection sees the real gap, not 0.

---

## Phase 5: Sidebar Upgrades — Notes, Completed Tasks, Stats (45 min)

**Goal:** The sidebar shows a richer picture — not just open tasks, but also what the assistant knows about you and weekly stats.

### Changes to `main.py`

Add to sidebar:

```python
# -- Known facts --
st.markdown("### 🧠 What I know")
notes = conn.execute(
    "SELECT json_extract(payload, '$.content'), json_extract(payload, '$.category') "
    "FROM events WHERE event_type = 'NOTE_RECORDED' "
    "AND json_extract(payload, '$.category') IN ('identity','preference','constraint') "
    "ORDER BY created_at DESC LIMIT 8"
).fetchall()
for n in notes:
    st.markdown(f"• `{n[1]}` {n[0]}")

# -- Week stats --
st.markdown("### 📊 This week")
week_tasks = conn.execute(
    "SELECT COUNT(*) FROM events WHERE event_type='TASK_COMPLETED' "
    "AND created_at > datetime('now','-7 days')"
).fetchone()[0]
week_time = conn.execute(
    "SELECT COALESCE(SUM(duration_minutes),0) FROM time_logs "
    "WHERE logged_at > datetime('now','-7 days')"
).fetchone()[0]
st.metric("Tasks completed", week_tasks)
st.metric("Time logged", f"{int(week_time)} min")

# -- Completed tasks (recent) --
with st.expander("✅ Recently completed"):
    done = conn.execute(
        "SELECT title, updated_at FROM tasks WHERE status IN ('done','completed') "
        "ORDER BY updated_at DESC LIMIT 10"
    ).fetchall()
    for d in done:
        st.markdown(f"• ~~{d[0]}~~ — {d[1]}")
```

---

## Phase 6: CSV Snapshot Export (30 min)

**Goal:** "Export Snapshot" writes CSVs to `snapshots/YYYY-MM-DD/` AND keeps the JSON download.

### Changes to `main.py`

Add a second export button:

```python
import csv, io, os

if st.button("📁 Save Snapshot to Folder"):
    today = datetime.utcnow().strftime('%Y-%m-%d')
    folder = os.path.join("snapshots", today)
    os.makedirs(folder, exist_ok=True)

    # Tasks CSV
    with open(os.path.join(folder, "tasks.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id","title","status","created_at","updated_at"])
        w.writerows(all_tasks)

    # Goals CSV
    with open(os.path.join(folder, "goals.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["goal_id","title","created_at","updated_at"])
        w.writerows(all_goals)

    # Time logs CSV
    with open(os.path.join(folder, "time_logs.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id","task_id","goal_id","duration_minutes","logged_at"])
        w.writerows(all_time)

    st.success(f"Snapshot saved to {folder}/")
```

---

## Execution Order

| # | Phase | Files changed | Time |
|---|---|---|---|
| 1 | Personal Operating Profile | NEW `agent/profile.txt`, EDIT `orchestrator.py` | 15 min |
| 2 | Chat prompt rewrite | EDIT `agent/prompts/chat.txt` | 20 min |
| 3 | Extract prompt rewrite | EDIT `agent/prompts/extract.txt` | 15 min |
| 4 | Orchestrator upgrades (day awareness, profile, facts, metrics) | EDIT `orchestrator.py` | 1.5 hr |
| 5 | Sidebar upgrades (notes, stats, completed) | EDIT `main.py` | 45 min |
| 6 | CSV snapshot export | EDIT `main.py` | 30 min |
| — | Reset DB + end-to-end test | `rm assistant.db` + test | 30 min |
| **Total** | | | **~4 hr** |

---

## What You Experience After This

**First message of the day:**
> "hey"

**Assistant (knows there's a 2-day gap + overdue tasks):**
> "Hey Miguel! Been a couple days — you've got 'clean up README' still open, and no SQL time logged this week. No rush, just keeping you in the loop. What's up?"

**You say:** "been busy with work, I'm tired"

**Assistant (detects stress, adapts tone):**
> "Totally get it. Don't worry about the task list today. What's the one thing that'd feel good to knock out if anything?"

**Extraction silently captures:**
> NOTE_RECORDED: {category: "reflection", content: "been busy with work, feeling tired"}

**You say:** "actually let me log 2 hours of pandas practice I did yesterday"

**Assistant:**
> "Nice — logged 2 hours of pandas practice. That's solid progress on the learning front."

**Extraction:**
> TIME_LOGGED: {duration_minutes: 120, note: "pandas practice"}

**Sidebar shows:**
> 📋 Tasks: ⬜ clean up README, ⬜ practice SQL joins
> 🎯 Goals: learn Python, pandas, and SQL
> 🧠 What I know: `identity` data analyst learning Python/SQL, `preference` prefers concise communication
> 📊 This week: 0 tasks completed, 120 min logged

That's the full app_cover.md assistant — running in exploratory mode.
