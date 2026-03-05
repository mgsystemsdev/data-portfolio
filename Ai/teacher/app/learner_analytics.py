import json
from db import (
    get_learner_profile,
    update_learner_profile,
    get_events,
    get_stage_methods,
    log_event,
    get_current_run,
    get_all_runs,
    get_fragile_methods,
    get_mastery_summary,
    get_struggle_patterns,
    upsert_struggle,
    record_mastery,
    update_run,
    save_learner_identity,
    get_learner_identity,
)

STAGES = [
    "S0", "S1", "S2", "S3", "S4", "S5", "S6",
    "S7A", "S7B", "S8", "S9", "S10", "S11", "S12",
]

ERROR_KEYWORDS = {
    "KeyError": "KeyError",
    "TypeError": "TypeError",
    "ValueError": "ValueError",
    "IndexError": "IndexError",
    "AttributeError": "AttributeError",
    "NameError": "NameError",
    "SyntaxError": "SyntaxError",
    "AssertionError": "AssertionError",
    "FileNotFoundError": "FileNotFoundError",
    "ModuleNotFoundError": "ModuleNotFoundError",
    "Traceback": "Traceback",
}

FRUSTRATION_SIGNALS = [
    "i don't get it", "this is confusing", "i hate", "this is stupid",
    "i'm stuck", "this makes no sense", "why do i need", "i keep getting",
    "again?", "still broken", "nothing works", "i give up", "too much",
    "overwhelming", "lost", "i'm lost", "frustrated",
]

CONFUSION_SIGNALS = [
    "i don't understand", "confused", "what does that mean",
    "can you explain", "why did", "wait", "huh", "what happened",
    "what's the difference", "when would i use", "i thought",
]

BREAKTHROUGH_SIGNALS = [
    "oh!", "aha", "now i get it", "that makes sense", "i see the pattern",
    "clicked", "that's why", "so that's how", "oh i see", "now it's clear",
]

COMPREHENSION_SIGNALS = [
    "got it", "makes sense", "understood", "i see", "ok next",
    "done", "ran it", "cool", "perfect", "yep", "yes",
]

PREFERENCE_SIGNALS = {
    "more_examples": ["show me more", "another example", "more examples", "can you show"],
    "less_detail": ["too much detail", "just show me", "skip to", "shorter", "get to the point"],
    "more_detail": ["explain more", "go deeper", "why does", "tell me more", "elaborate"],
}

MOTIVATION_SIGNALS = [
    "get hired", "job", "interview", "career", "portfolio", "resume",
    "goal", "dream", "want to be", "my plan", "salary", "promotion",
    "freelance", "switch careers", "data analyst", "data engineer",
    "impress", "stand out", "competitive", "fast as possible", "quickly",
]

SELF_CORRECTION_SIGNALS = [
    "wait, i see", "nvm", "never mind", "i found it", "i see the problem",
    "oh wait", "actually", "my bad", "i fixed it", "figured it out",
    "i see what i did", "that was my mistake", "let me fix",
]

IDENTITY_PATTERNS = {
    "career_goal": [
        "i want to be", "i want to become", "my goal is", "i'm trying to get",
        "i want to get hired", "dream job", "i want a job", "i'm aiming for",
        "i want to work at", "i want to work as", "career goal",
    ],
    "motivation": [
        "the reason i", "i'm doing this because", "what drives me",
        "i need to", "i have to", "my family", "prove", "for my kids",
        "for myself", "tired of", "sick of", "i deserve",
    ],
    "fear": [
        "i'm afraid", "i'm scared", "what if i fail", "not good enough",
        "imposter", "too old", "too late", "behind", "everyone else",
        "i don't know if i can", "what if i'm not",
    ],
    "timeline": [
        "by next month", "in 3 months", "by end of year", "as fast as possible",
        "quickly", "how long", "how many runs", "before summer",
        "i need this job by", "deadline",
    ],
    "background": [
        "i used to", "my background", "i come from", "i've been working",
        "i studied", "my degree", "self-taught", "bootcamp", "no experience",
        "career change", "switching from",
    ],
    "opinion_asked": [
        "what do you think", "your opinion", "what would you do",
        "do you think i can", "am i on track", "honest opinion",
        "what's the fastest", "best path", "your advice",
    ],
    "personal_share": [
        "i just got laid off", "i quit my job", "i'm unemployed",
        "my boss", "my coworkers", "i hate my job", "burned out",
        "i love this", "this is fun", "this clicked",
    ],
}

ANCHOR_KEYWORDS = {
    "intent": ["what does it do", "what problem", "why do we need", "what is this for", "purpose"],
    "return": ["what does it return", "return type", "gives back", "output type"],
    "parameter_control": ["parameters", "how do i target", "which argument", "default value", "what if i pass"],
    "shape": ["row count", "column count", "how many rows", "shape change", "index reset"],
    "failure": ["what breaks", "error", "what if it fails", "wrong type", "exception"],
    "composition": ["combine with", "pair with", "chain", "after this", "together with"],
    "placement": ["which module", "where does this go", "which file", "load.py", "clean.py"],
    "tradeoff": ["why this instead", "alternative", "why not use", "better way", "performance"],
}

QUESTION_SOPHISTICATION = {
    "basic": ["what is", "what does", "how do i", "show me", "what's this"],
    "intermediate": ["what's the difference", "when would i", "why does it", "how does it work"],
    "advanced": ["why this instead of", "trade-off", "at scale", "performance", "edge case", "what if 10x", "interview"],
}

# Method categories for pattern detection
METHOD_CATEGORIES = {
    "string_ops": ["str.strip", "str.lower", "str.upper", "str.title", "str.contains", "str.replace"],
    "datetime": ["dt.year", "dt.month", "dt.day", "dt.days", "to_datetime", "Timestamp"],
    "selection": ["df.loc", "df.iloc", "df[", "isin", "condition"],
    "aggregation": ["groupby", "agg", "size()", "count()", "sum()", "mean()", "min()", "max()"],
    "numpy": ["np.where", "np.busday_count"],
    "sql_basic": ["SELECT", "WHERE", "GROUP BY", "COUNT", "ORDER BY"],
    "sql_advanced": ["JOIN", "CASE WHEN", "ROW_NUMBER", "CTE", "RANK", "LAG", "LEAD", "Subquery"],
    "validation": ["assert", "duplicated", "isna", "isnull", "equals"],
    "io": ["read_excel", "to_csv", "to_excel", "to_sql"],
}


def _categorize_method(method_name):
    """Determine which category a method belongs to."""
    if not method_name:
        return "general"
    for cat, keywords in METHOD_CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in method_name.lower():
                return cat
    return "general"


def detect_errors_in_message(content):
    """Scan user message for Python/SQL error patterns."""
    found = []
    for keyword, error_type in ERROR_KEYWORDS.items():
        if keyword in content:
            found.append(error_type)
    return found


def detect_sentiment(content):
    """Classify the emotional tone of a user message."""
    lower = content.lower()
    for signal in FRUSTRATION_SIGNALS:
        if signal in lower:
            return "frustrated"
    for signal in BREAKTHROUGH_SIGNALS:
        if signal in lower:
            return "breakthrough"
    for signal in CONFUSION_SIGNALS:
        if signal in lower:
            return "confused"
    for signal in COMPREHENSION_SIGNALS:
        if signal in lower:
            return "positive"
    return "neutral"


def detect_preferences(content):
    """Detect teaching preference signals."""
    lower = content.lower()
    for pref, signals in PREFERENCE_SIGNALS.items():
        for s in signals:
            if s in lower:
                return pref
    return None


def detect_self_correction(content):
    """Detect when user catches their own error — sign of growing independence."""
    lower = content.lower()
    for signal in SELF_CORRECTION_SIGNALS:
        if signal in lower:
            return signal
    return None


def detect_anchor_engagement(content):
    """Detect which anchor the user is asking about."""
    lower = content.lower()
    for anchor, keywords in ANCHOR_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return anchor
    return None


def detect_question_level(content):
    """Classify question sophistication: basic → intermediate → advanced."""
    lower = content.lower()
    # Check advanced first (most specific)
    for kw in QUESTION_SOPHISTICATION["advanced"]:
        if kw in lower:
            return "advanced"
    for kw in QUESTION_SOPHISTICATION["intermediate"]:
        if kw in lower:
            return "intermediate"
    for kw in QUESTION_SOPHISTICATION["basic"]:
        if kw in lower:
            return "basic"
    return None


def analyze_user_message(session_id, content, stage, method=None):
    """Full analysis of a user message — errors, sentiment, struggles, preferences."""
    run = get_current_run()
    run_number = run["run_number"] if run else 1

    # 1. Error detection
    errors = detect_errors_in_message(content)
    if errors:
        log_event(session_id, "error", stage, method, {"errors": errors}, sentiment="negative")
        for err in errors:
            category = _categorize_method(method)
            upsert_struggle(
                "recurring_error", err,
                f"{err} encountered during {method or 'unknown'} in {stage}",
                stage=stage, method=method,
                adaptation_rule=f"Pre-teach {err} failure mode before introducing similar methods"
            )
        # Update mastery for this method
        if method:
            record_mastery(run_number, stage, method, attempts=1, errors=len(errors))

    # 2. Sentiment detection
    sentiment = detect_sentiment(content)
    if sentiment == "frustrated":
        log_event(session_id, "frustration", stage, method, {"content_snippet": content[:100]}, sentiment="frustrated")
        upsert_struggle(
            "frustration", stage,
            f"User expressed frustration at {stage}" + (f" on {method}" if method else ""),
            stage=stage, method=method,
            adaptation_rule=f"Slow down at {stage}. Simplify. Give motivation."
        )
    elif sentiment == "confused":
        log_event(session_id, "confusion", stage, method, {"content_snippet": content[:100]}, sentiment="confused")
        category = _categorize_method(method)
        if category != "general":
            upsert_struggle(
                "category_weakness", category,
                f"Confusion with {category} methods",
                stage=stage, method=method,
                adaptation_rule=f"Give extra Parameter Control depth on {category} methods"
            )
    elif sentiment == "breakthrough":
        log_event(session_id, "breakthrough", stage, method, {}, sentiment="positive")
    elif sentiment == "positive":
        log_event(session_id, "comprehension", stage, method, {}, sentiment="positive")

    # 3. Preference detection
    pref = detect_preferences(content)
    if pref:
        log_event(session_id, "preference", stage, method, {"preference": pref}, sentiment="neutral")
        if pref == "less_detail":
            upsert_struggle("preference", "depth", "User prefers concise explanations",
                            adaptation_rule="Keep explanations tight. Fewer examples unless asked.")
        elif pref == "more_detail":
            upsert_struggle("preference", "depth", "User wants deeper explanations",
                            adaptation_rule="Go deeper on anchors. More examples. More edge cases.")
        elif pref == "more_examples":
            upsert_struggle("preference", "examples", "User wants more code examples",
                            adaptation_rule="Add extra code variations in Parameter Control anchor.")

    # 4. Self-correction detection (independence signal)
    self_fix = detect_self_correction(content)
    if self_fix:
        log_event(session_id, "self_correction", stage, method, {"signal": self_fix}, sentiment="positive")

    # 5. Anchor engagement — which anchors get follow-up questions
    anchor = detect_anchor_engagement(content)
    if anchor:
        log_event(session_id, "anchor_engagement", stage, method, {"anchor": anchor}, sentiment="neutral")
        upsert_struggle(
            "anchor_focus", anchor,
            f"User frequently engages with {anchor} anchor",
            stage=stage, method=method,
            adaptation_rule=f"Give extra depth on the {anchor} anchor — user needs it."
        )

    # 6. Question sophistication tracking
    q_level = detect_question_level(content)
    if q_level:
        log_event(session_id, "question_level", stage, method, {"level": q_level}, sentiment="neutral")

    # 7. Motivation detection — student shares goals/career aspirations
    lower = content.lower()
    for signal in MOTIVATION_SIGNALS:
        if signal in lower:
            log_event(session_id, "motivation", stage, method, {"signal": signal, "snippet": content[:150]}, sentiment="positive")
            upsert_struggle(
                "motivation", "career_goal",
                f"Student expressed career motivation: '{signal}'",
                adaptation_rule="Connect current method to career goal. Be a mentor. Engage with their ambition."
            )
            break

    # 8. Identity detection — learn about the user as a person
    for category, signals in IDENTITY_PATTERNS.items():
        for signal in signals:
            if signal in lower:
                save_learner_identity(
                    category=category,
                    content=signal,
                    source_snippet=content[:200],
                    session_id=session_id,
                )
                log_event(session_id, "identity_share", stage, method,
                         {"category": category, "signal": signal, "snippet": content[:150]},
                         sentiment="positive")
                break


def refresh_learner_profile():
    """Recompute full learner profile from all accumulated data."""
    error_events = get_events(event_type="error", limit=1000)
    confusion_events = get_events(event_type="confusion", limit=1000)
    frustration_events = get_events(event_type="frustration", limit=1000)
    breakthrough_events = get_events(event_type="breakthrough", limit=1000)

    # Error type counts
    error_counts = {}
    for e in error_events:
        details = json.loads(e["details"])
        for err in details.get("errors", []):
            error_counts[err] = error_counts.get(err, 0) + 1

    # Stage difficulty map
    stage_difficulty = {}
    for e in confusion_events + frustration_events:
        s = e.get("stage", "unknown")
        stage_difficulty[s] = stage_difficulty.get(s, 0) + 1

    slow_stages = sorted(stage_difficulty, key=stage_difficulty.get, reverse=True)[:3]

    # Fast stages (breakthroughs + comprehension, low errors)
    stage_positives = {}
    for e in breakthrough_events:
        s = e.get("stage", "unknown")
        stage_positives[s] = stage_positives.get(s, 0) + 1
    fast_stages = sorted(stage_positives, key=stage_positives.get, reverse=True)[:3]

    # Method lock stats — single query instead of per-stage loop
    from db import get_conn
    _conn = get_conn()
    _row = _conn.execute(
        "SELECT COUNT(*) as total_locked, COALESCE(SUM(attempts), 0) as total_attempts FROM method_progress WHERE locked = 1"
    ).fetchone()
    _conn.close()
    total_locked = _row["total_locked"]
    total_attempts = _row["total_attempts"]
    lock_count = total_locked

    avg_attempts = total_attempts / lock_count if lock_count else 0

    # Depth preference from struggles
    prefs = get_struggle_patterns(min_frequency=1)
    depth = "standard"
    for p in prefs:
        if p["pattern_type"] == "preference" and p["category"] == "depth":
            if "concise" in p["adaptation_rule"].lower():
                depth = "concise"
            elif "deeper" in p["adaptation_rule"].lower():
                depth = "deep"

    # Override by performance
    if avg_attempts > 3:
        depth = "deep"
    elif avg_attempts < 1.5 and total_locked > 10 and depth == "standard":
        depth = "concise"

    update_learner_profile(
        total_methods_locked=total_locked,
        total_errors=len(error_events),
        avg_attempts_to_lock=round(avg_attempts, 2),
        common_error_types=json.dumps(error_counts),
        slow_stages=json.dumps(slow_stages),
        fast_stages=json.dumps(fast_stages),
        preferred_depth=depth,
    )


def _build_run_comparison():
    """Compare current run to previous runs."""
    runs = get_all_runs()
    if len(runs) <= 1:
        return None

    current = runs[-1]
    previous = runs[-2]

    lines = []
    lines.append(f"Previous Run {previous['run_number']}:")
    lines.append(f"  Reached: {previous['stage_reached']}")
    lines.append(f"  Methods locked: {previous['methods_locked_total']}")
    lines.append(f"  First-try locks: {previous['methods_first_try']}")
    lines.append(f"  Errors: {previous['total_errors']}")
    lines.append(f"  Confusions: {previous['total_confusions']}")
    lines.append(f"  Breakthroughs: {previous['total_breakthroughs']}")

    # Compare mastery across runs
    prev_mastery = get_mastery_summary(previous["run_number"])
    curr_mastery = get_mastery_summary(current["run_number"])

    improved = []
    regressed = []
    level_rank = {"unseen": 0, "fragile": 1, "familiar": 2, "confident": 3, "hardened": 4}

    prev_map = {(m["stage"], m["method_name"]): m for m in prev_mastery}
    for m in curr_mastery:
        key = (m["stage"], m["method_name"])
        if key in prev_map:
            prev_level = level_rank.get(prev_map[key]["mastery_level"], 0)
            curr_level = level_rank.get(m["mastery_level"], 0)
            if curr_level > prev_level:
                improved.append(f"{m['method_name']} ({prev_map[key]['mastery_level']} → {m['mastery_level']})")
            elif curr_level < prev_level:
                regressed.append(f"{m['method_name']} ({prev_map[key]['mastery_level']} → {m['mastery_level']})")

    if improved:
        lines.append(f"\n  Improved this run: {', '.join(improved[:10])}")
    if regressed:
        lines.append(f"  Regressed this run: {', '.join(regressed[:10])}")

    return "\n".join(lines)


def _build_adaptation_rules():
    """Generate specific teaching instructions from accumulated patterns."""
    from db import get_methods_due_for_review, get_recent_summaries, compute_avg_response_time, get_events

    patterns = get_struggle_patterns(min_frequency=2)
    fragile = get_fragile_methods()
    run = get_current_run()
    run_number = run["run_number"] if run else 1

    rules = []

    # From struggle patterns
    for p in patterns:
        if p["adaptation_rule"]:
            rules.append(f"• {p['adaptation_rule']} (seen {p['frequency']}x)")

    # From fragile methods
    if fragile:
        method_list = ", ".join(f"{m['method_name']}({m['stage']})" for m in fragile[:8])
        rules.append(f"• These methods are still fragile — give extra depth: {method_list}")

    # Spaced repetition — methods due for review
    due = get_methods_due_for_review(days_threshold=7)
    if due:
        due_list = ", ".join(f"{m['method_name']}({m['stage']}, {int(m['days_since'])}d ago)" for m in due[:6])
        rules.append(f"• SPACED REPETITION: These methods are due for review: {due_list}")
        rules.append("• When you encounter these methods, briefly confirm the user still remembers them.")

    # Self-correction growth (independence)
    self_corrections = get_events(event_type="self_correction", limit=100)
    if len(self_corrections) >= 3:
        rules.append(f"• User has self-corrected {len(self_corrections)} times — growing independence. Acknowledge it.")

    # Question sophistication trend
    q_events = get_events(event_type="question_level", limit=50)
    if q_events:
        levels = [json.loads(e["details"]).get("level", "basic") for e in q_events]
        recent = levels[:10]
        advanced_pct = sum(1 for l in recent if l == "advanced") / len(recent) if recent else 0
        if advanced_pct >= 0.3:
            rules.append("• User is asking advanced questions (trade-offs, scale, alternatives). Match that depth.")
        elif all(l == "basic" for l in recent):
            rules.append("• User is still asking basic questions. Keep fundamentals front and center.")

    # Run-based rules
    if run_number == 1:
        rules.append("• Run 1: Full teaching mode. All 8 anchors. Full depth on Parameter Control.")
    elif run_number == 2:
        rules.append("• Run 2: Confirm recall on hardened methods (brief). Double down on fragile ones.")
        rules.append("• Run 2: Pre-teach failure modes the user hit in Run 1.")
    elif run_number >= 3:
        rules.append(f"• Run {run_number}: Recall-first mode. Hardened methods = 'Write it from memory.'")
        rules.append(f"• Run {run_number}: Focus on composition and trade-offs, not basics.")
        rules.append(f"• Run {run_number}: Challenge the user. Push for speed and accuracy.")

    return rules


def build_learner_context():
    """Build the full adaptive intelligence section for prompt injection.
    Uses the learner profile as-is (refreshed after the previous message).
    """
    p = get_learner_profile()
    run = get_current_run()
    run_number = run["run_number"] if run else 1

    if p["total_methods_locked"] == 0 and run_number == 1:
        return "This is a new learner on Run 1. No history yet. Discover their pace."

    error_types = json.loads(p["common_error_types"])
    slow_stages = json.loads(p["slow_stages"])
    fast_stages = json.loads(p["fast_stages"])

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🧠 ADAPTIVE INTELLIGENCE — RUN {run_number}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"Pipeline run: {run_number}",
        f"Methods locked total: {p['total_methods_locked']}",
        f"Average attempts to lock: {p['avg_attempts_to_lock']}",
        f"Total errors across all runs: {p['total_errors']}",
        f"Explanation depth: {p['preferred_depth']}",
    ]

    if error_types:
        top = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append(f"Top error types: {', '.join(f'{e}({c})' for e, c in top)}")

    if slow_stages:
        lines.append(f"Difficult stages: {', '.join(slow_stages)}")
    if fast_stages:
        lines.append(f"Strong stages: {', '.join(fast_stages)}")

    # Mastery breakdown
    mastery = get_mastery_summary(run_number)
    if mastery:
        counts = {"hardened": 0, "confident": 0, "familiar": 0, "fragile": 0, "unseen": 0}
        for m in mastery:
            counts[m["mastery_level"]] = counts.get(m["mastery_level"], 0) + 1
        lines.append("")
        lines.append("Mastery breakdown this run:")
        for level in ["hardened", "confident", "familiar", "fragile"]:
            if counts[level]:
                lines.append(f"  {level}: {counts[level]} methods")

    # Run comparison
    comparison = _build_run_comparison()
    if comparison:
        lines.append("")
        lines.append(comparison)

    # Adaptation rules
    rules = _build_adaptation_rules()
    if rules:
        lines.append("")
        lines.append("TEACHING ADAPTATIONS (follow these):")
        lines.extend(rules)

    # Session history
    from db import get_recent_summaries
    summaries = get_recent_summaries(limit=3)
    if summaries:
        lines.append("")
        lines.append("RECENT SESSION HISTORY:")
        for s in summaries:
            lines.append(f"  {s['summary_text']}")

    # Depth instructions
    lines.append("")
    if p["preferred_depth"] == "deep":
        lines.append("DEPTH: This learner needs extra examples, slower pacing, and pre-taught failure modes.")
    elif p["preferred_depth"] == "concise":
        lines.append("DEPTH: This learner is quick. Keep explanations tight. Move faster through confident methods.")
    else:
        lines.append("DEPTH: Standard pacing. Full anchors. Adjust if signals change.")

    return "\n".join(lines)
