import json
from db import (
    get_learner_profile,
    update_learner_profile,
    get_events,
    log_event,
    get_current_run,
    get_all_runs,
    get_fragile_concepts,
    get_mastery_summary,
    get_struggle_patterns,
    upsert_struggle,
    record_mastery,
    update_run,
    save_learner_identity,
    get_learner_identity,
)

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
    "syntax": ["how do i write", "what's the syntax", "how is it written", "format"],
    "commands": ["what commands", "which methods", "what operations", "all the ways", "what can i do with"],
    "output": ["what does it return", "return type", "gives back", "output type", "what comes back"],
    "failure": ["what breaks", "error", "what if it fails", "wrong type", "exception", "edge case"],
    "composition": ["combine with", "pair with", "chain", "after this", "together with"],
    "placement": ["where does this go", "which file", "where in code", "when do i use this"],
    "tradeoff": ["why this instead", "alternative", "why not use", "better way", "performance"],
}

QUESTION_SOPHISTICATION = {
    "basic": ["what is", "what does", "how do i", "show me", "what's this"],
    "intermediate": ["what's the difference", "when would i", "why does it", "how does it work"],
    "advanced": ["why this instead of", "trade-off", "at scale", "performance", "edge case", "what if 10x", "interview"],
}

CONCEPT_CATEGORIES = {
    "string_ops": ["str", "string", "strip", "lower", "upper", "split", "join", "replace", "format"],
    "datetime": ["date", "time", "datetime", "timestamp", "timedelta"],
    "data_structures": ["list", "dict", "set", "tuple", "array"],
    "functions": ["def", "function", "lambda", "return", "parameter", "argument"],
    "loops": ["for", "while", "loop", "iterate", "comprehension"],
    "conditionals": ["if", "else", "elif", "conditional", "boolean", "comparison"],
    "classes": ["class", "object", "method", "attribute", "inheritance", "instance"],
    "sql": ["select", "where", "join", "group by", "aggregate", "window", "cte"],
    "pandas": ["dataframe", "series", "groupby", "merge", "loc", "iloc", "apply"],
    "async": ["async", "await", "promise", "callback", "concurrent"],
    "errors": ["try", "except", "raise", "exception", "error handling"],
}


def _categorize_concept(concept_name):
    if not concept_name:
        return "general"
    lower = concept_name.lower()
    for cat, keywords in CONCEPT_CATEGORIES.items():
        for kw in keywords:
            if kw in lower:
                return cat
    return "general"


def detect_errors_in_message(content):
    found = []
    for keyword, error_type in ERROR_KEYWORDS.items():
        if keyword in content:
            found.append(error_type)
    return found


def detect_sentiment(content):
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
    lower = content.lower()
    for pref, signals in PREFERENCE_SIGNALS.items():
        for s in signals:
            if s in lower:
                return pref
    return None


def detect_self_correction(content):
    lower = content.lower()
    for signal in SELF_CORRECTION_SIGNALS:
        if signal in lower:
            return signal
    return None


def detect_anchor_engagement(content):
    lower = content.lower()
    for anchor, keywords in ANCHOR_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return anchor
    return None


def detect_question_level(content):
    lower = content.lower()
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


def analyze_user_message(session_id, content, topic, concept=None):
    """Full analysis of a user message — errors, sentiment, struggles, preferences."""
    run = get_current_run()
    run_number = run["run_number"] if run else 1

    # 1. Error detection
    errors = detect_errors_in_message(content)
    if errors:
        log_event(session_id, "error", topic, concept, {"errors": errors}, sentiment="negative")
        for err in errors:
            upsert_struggle(
                "recurring_error", err,
                f"{err} encountered during {concept or 'unknown'} in {topic}",
                topic=topic, concept=concept,
                adaptation_rule=f"Pre-teach {err} failure mode before similar concepts"
            )
        if concept:
            record_mastery(run_number, topic, concept, attempts=1, errors=len(errors))

    # 2. Sentiment detection
    sentiment = detect_sentiment(content)
    if sentiment == "frustrated":
        log_event(session_id, "frustration", topic, concept,
                  {"content_snippet": content[:100]}, sentiment="frustrated")
        upsert_struggle(
            "frustration", topic,
            f"User expressed frustration at {topic}" + (f" on {concept}" if concept else ""),
            topic=topic, concept=concept,
            adaptation_rule=f"Slow down at {topic}. Simplify. Give motivation."
        )
    elif sentiment == "confused":
        log_event(session_id, "confusion", topic, concept,
                  {"content_snippet": content[:100]}, sentiment="confused")
        category = _categorize_concept(concept)
        if category != "general":
            upsert_struggle(
                "category_weakness", category,
                f"Confusion with {category} concepts",
                topic=topic, concept=concept,
                adaptation_rule=f"Give extra Commands anchor depth on {category} concepts"
            )
    elif sentiment == "breakthrough":
        log_event(session_id, "breakthrough", topic, concept, {}, sentiment="positive")
    elif sentiment == "positive":
        log_event(session_id, "comprehension", topic, concept, {}, sentiment="positive")

    # 3. Preference detection
    pref = detect_preferences(content)
    if pref:
        log_event(session_id, "preference", topic, concept, {"preference": pref}, sentiment="neutral")
        if pref == "less_detail":
            upsert_struggle("preference", "depth", "User prefers concise explanations",
                            adaptation_rule="Keep explanations tight. Fewer examples unless asked.")
        elif pref == "more_detail":
            upsert_struggle("preference", "depth", "User wants deeper explanations",
                            adaptation_rule="Go deeper on anchors. More examples. More edge cases.")
        elif pref == "more_examples":
            upsert_struggle("preference", "examples", "User wants more code examples",
                            adaptation_rule="Add extra code variations in Commands anchor.")

    # 4. Self-correction detection
    self_fix = detect_self_correction(content)
    if self_fix:
        log_event(session_id, "self_correction", topic, concept, {"signal": self_fix}, sentiment="positive")

    # 5. Anchor engagement
    anchor = detect_anchor_engagement(content)
    if anchor:
        log_event(session_id, "anchor_engagement", topic, concept, {"anchor": anchor}, sentiment="neutral")
        upsert_struggle(
            "anchor_focus", anchor,
            f"User frequently engages with {anchor} anchor",
            topic=topic, concept=concept,
            adaptation_rule=f"Give extra depth on the {anchor} anchor — user needs it."
        )

    # 6. Question sophistication
    q_level = detect_question_level(content)
    if q_level:
        log_event(session_id, "question_level", topic, concept, {"level": q_level}, sentiment="neutral")

    # 7. Motivation detection
    lower = content.lower()
    for signal in MOTIVATION_SIGNALS:
        if signal in lower:
            log_event(session_id, "motivation", topic, concept,
                      {"signal": signal, "snippet": content[:150]}, sentiment="positive")
            upsert_struggle(
                "motivation", "career_goal",
                f"Student expressed career motivation: '{signal}'",
                adaptation_rule="Connect current concept to career goal. Be a mentor."
            )
            break

    # 8. Identity detection
    for category, signals in IDENTITY_PATTERNS.items():
        for signal in signals:
            if signal in lower:
                save_learner_identity(
                    category=category,
                    content=signal,
                    source_snippet=content[:200],
                    session_id=session_id,
                )
                log_event(session_id, "identity_share", topic, concept,
                         {"category": category, "signal": signal, "snippet": content[:150]},
                         sentiment="positive")
                break


def refresh_learner_profile():
    """Recompute full learner profile from all accumulated data."""
    error_events = get_events(event_type="error", limit=1000)
    confusion_events = get_events(event_type="confusion", limit=1000)
    frustration_events = get_events(event_type="frustration", limit=1000)
    breakthrough_events = get_events(event_type="breakthrough", limit=1000)

    error_counts = {}
    for e in error_events:
        details = json.loads(e["details"])
        for err in details.get("errors", []):
            error_counts[err] = error_counts.get(err, 0) + 1

    topic_difficulty = {}
    for e in confusion_events + frustration_events:
        t = e.get("topic") or "unknown"
        topic_difficulty[t] = topic_difficulty.get(t, 0) + 1
    slow_topics = sorted(topic_difficulty, key=topic_difficulty.get, reverse=True)[:3]

    topic_positives = {}
    for e in breakthrough_events:
        t = e.get("topic") or "unknown"
        topic_positives[t] = topic_positives.get(t, 0) + 1
    fast_topics = sorted(topic_positives, key=topic_positives.get, reverse=True)[:3]

    from db import get_conn
    conn = get_conn()
    rows = conn.execute("SELECT locked, attempts FROM concept_progress").fetchall()
    conn.close()

    total_locked = sum(1 for r in rows if r["locked"])
    total_attempts = sum(r["attempts"] for r in rows if r["locked"])
    avg_attempts = total_attempts / total_locked if total_locked else 0

    prefs = get_struggle_patterns(min_frequency=1)
    depth = "standard"
    for p in prefs:
        if p["pattern_type"] == "preference" and p["category"] == "depth":
            if "concise" in p["adaptation_rule"].lower():
                depth = "concise"
            elif "deeper" in p["adaptation_rule"].lower():
                depth = "deep"

    if avg_attempts > 3:
        depth = "deep"
    elif avg_attempts < 1.5 and total_locked > 10 and depth == "standard":
        depth = "concise"

    update_learner_profile(
        total_concepts_locked=total_locked,
        total_errors=len(error_events),
        avg_attempts_to_lock=round(avg_attempts, 2),
        common_error_types=json.dumps(error_counts),
        slow_topics=json.dumps(slow_topics),
        fast_topics=json.dumps(fast_topics),
        preferred_depth=depth,
    )


def _build_run_comparison():
    runs = get_all_runs()
    if len(runs) <= 1:
        return None

    current = runs[-1]
    previous = runs[-2]

    lines = [
        f"Previous Run {previous['run_number']}:",
        f"  Topic reached: {previous['topic_reached']}",
        f"  Concepts locked: {previous['concepts_locked_total']}",
        f"  Errors: {previous['total_errors']}",
        f"  Confusions: {previous['total_confusions']}",
        f"  Breakthroughs: {previous['total_breakthroughs']}",
    ]

    prev_mastery = get_mastery_summary(previous["run_number"])
    curr_mastery = get_mastery_summary(current["run_number"])

    improved, regressed = [], []
    level_rank = {"unseen": 0, "fragile": 1, "familiar": 2, "confident": 3, "hardened": 4}

    prev_map = {(m["topic"], m["concept_name"]): m for m in prev_mastery}
    for m in curr_mastery:
        key = (m["topic"], m["concept_name"])
        if key in prev_map:
            pl = level_rank.get(prev_map[key]["mastery_level"], 0)
            cl = level_rank.get(m["mastery_level"], 0)
            if cl > pl:
                improved.append(f"{m['concept_name']} ({prev_map[key]['mastery_level']} → {m['mastery_level']})")
            elif cl < pl:
                regressed.append(f"{m['concept_name']} ({prev_map[key]['mastery_level']} → {m['mastery_level']})")

    if improved:
        lines.append(f"\n  Improved this run: {', '.join(improved[:10])}")
    if regressed:
        lines.append(f"  Regressed this run: {', '.join(regressed[:10])}")

    return "\n".join(lines)


def _build_adaptation_rules():
    from db import get_concepts_due_for_review
    patterns = get_struggle_patterns(min_frequency=2)
    fragile = get_fragile_concepts()
    run = get_current_run()
    run_number = run["run_number"] if run else 1

    rules = []

    for p in patterns:
        if p["adaptation_rule"]:
            rules.append(f"• {p['adaptation_rule']} (seen {p['frequency']}x)")

    if fragile:
        concept_list = ", ".join(f"{c['concept_name']}({c['topic']})" for c in fragile[:8])
        rules.append(f"• These concepts are still fragile — give extra depth: {concept_list}")

    due = get_concepts_due_for_review(days_threshold=7)
    if due:
        due_list = ", ".join(f"{c['concept_name']}({c['topic']}, {int(c['days_since'])}d ago)" for c in due[:6])
        rules.append(f"• SPACED REPETITION: These concepts are due for review: {due_list}")
        rules.append("• When you encounter these, briefly confirm the user still remembers them.")

    self_corrections = get_events(event_type="self_correction", limit=100)
    if len(self_corrections) >= 3:
        rules.append(f"• User has self-corrected {len(self_corrections)} times — growing independence. Acknowledge it.")

    q_events = get_events(event_type="question_level", limit=50)
    if q_events:
        levels = [json.loads(e["details"]).get("level", "basic") for e in q_events]
        recent = levels[:10]
        advanced_pct = sum(1 for l in recent if l == "advanced") / len(recent) if recent else 0
        if advanced_pct >= 0.3:
            rules.append("• User is asking advanced questions. Match that depth.")
        elif all(l == "basic" for l in recent):
            rules.append("• User is asking basic questions. Keep fundamentals front and center.")

    if run_number == 1:
        rules.append("• Run 1: Full teaching mode. All 8 anchors. Full depth on Commands anchor.")
    elif run_number == 2:
        rules.append("• Run 2: Confirm recall on hardened concepts. Double down on fragile ones.")
        rules.append("• Run 2: Pre-teach failure modes the user hit in Run 1.")
    elif run_number >= 3:
        rules.append(f"• Run {run_number}: Recall-first mode. Hardened concepts = write from memory.")
        rules.append(f"• Run {run_number}: Focus on composition and trade-offs, not basics.")

    return rules


def build_learner_context():
    """Build the full adaptive intelligence section for prompt injection.
    Uses the learner profile as-is (refreshed after the previous message).
    """
    p = get_learner_profile()
    run = get_current_run()
    run_number = run["run_number"] if run else 1

    if p["total_concepts_locked"] == 0 and run_number == 1:
        return "This is a new learner on Run 1. No history yet. Discover their pace."

    error_types = json.loads(p["common_error_types"])
    slow_topics = json.loads(p["slow_topics"])
    fast_topics = json.loads(p["fast_topics"])

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🧠 ADAPTIVE INTELLIGENCE — RUN {run_number}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"Learning run: {run_number}",
        f"Concepts locked total: {p['total_concepts_locked']}",
        f"Average attempts to lock: {p['avg_attempts_to_lock']}",
        f"Total errors across all runs: {p['total_errors']}",
        f"Explanation depth: {p['preferred_depth']}",
    ]

    if error_types:
        top = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append(f"Top error types: {', '.join(f'{e}({c})' for e, c in top)}")
    if slow_topics:
        lines.append(f"Difficult topics: {', '.join(slow_topics)}")
    if fast_topics:
        lines.append(f"Strong topics: {', '.join(fast_topics)}")

    mastery = get_mastery_summary(run_number)
    if mastery:
        counts = {"hardened": 0, "confident": 0, "familiar": 0, "fragile": 0}
        for m in mastery:
            lv = m["mastery_level"]
            if lv in counts:
                counts[lv] += 1
        lines.append("")
        lines.append("Mastery breakdown this run:")
        for level in ["hardened", "confident", "familiar", "fragile"]:
            if counts[level]:
                lines.append(f"  {level}: {counts[level]} concepts")

    comparison = _build_run_comparison()
    if comparison:
        lines.append("")
        lines.append(comparison)

    rules = _build_adaptation_rules()
    if rules:
        lines.append("")
        lines.append("TEACHING ADAPTATIONS (follow these):")
        lines.extend(rules)

    from db import get_recent_summaries
    summaries = get_recent_summaries(limit=3)
    if summaries:
        lines.append("")
        lines.append("RECENT SESSION HISTORY:")
        for s in summaries:
            lines.append(f"  {s['summary_text']}")

    lines.append("")
    if p["preferred_depth"] == "deep":
        lines.append("DEPTH: This learner needs extra examples, slower pacing, and pre-taught failure modes.")
    elif p["preferred_depth"] == "concise":
        lines.append("DEPTH: This learner is quick. Keep it tight. Move faster through confident concepts.")
    else:
        lines.append("DEPTH: Standard pacing. Full anchors. Adjust if signals change.")

    return "\n".join(lines)


def _confidence_decay(confidence, last_updated, half_life_days=30):
    """Decay confidence over time. Never treat as binary truth."""
    if confidence is None or confidence <= 0:
        return 0.0
    try:
        from datetime import datetime, timezone
        if last_updated:
            if hasattr(last_updated, "split"):
                t = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            else:
                t = last_updated
            now = datetime.now(timezone.utc) if t.tzinfo else datetime.now()
            if hasattr(t, "tzinfo") and t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            days = (now - t).total_seconds() / 86400
        else:
            days = 0
    except Exception:
        days = 0
    import math
    decayed = confidence * (0.5 ** (days / half_life_days))
    return max(0.0, min(1.0, decayed))


def _build_learner_identity_context():
    identity = get_learner_identity()
    if not identity:
        return ""

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🧑 WHO THIS PERSON IS — WHAT YOU'VE LEARNED ABOUT THEM",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    CONFIDENCE_THRESHOLD = 0.3  # Never treat as binary; use threshold

    grouped = {}
    for item in identity:
        conf = item.get("confidence", 0.8)
        updated = item.get("last_updated")
        decayed = _confidence_decay(conf, updated)
        if decayed < CONFIDENCE_THRESHOLD:
            continue
        cat = item["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(item["source_snippet"] if item["source_snippet"] else item["content"])

    labels = {
        "career_goal": "🎯 Career Goals",
        "motivation": "🔥 What Drives Them",
        "fear": "😰 Fears & Doubts",
        "timeline": "⏰ Timeline Pressure",
        "background": "📚 Background",
        "opinion_asked": "🤔 They Asked Your Opinion On",
        "personal_share": "💬 Personal Things They Shared",
    }

    for cat, items in grouped.items():
        label = labels.get(cat, cat.replace("_", " ").title())
        lines.append(f"\n{label}:")
        for item in items:
            lines.append(f'  • "{item}"')

    return "\n".join(lines)
