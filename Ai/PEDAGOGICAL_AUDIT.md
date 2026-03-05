# Deep Architectural + Pedagogical Audit

**Codebases:** Teacher (Structured Data Analytics), Teacher Practice (Free Topic Teaching), Metacode (Forced Practice)  
**Format:** One question at a time, concrete answers from the actual code and prompts.  
**Verdict:** If the answer is "no" or "only in prompt, not enforced," that is stated explicitly.

---

# 🔵 CODEBASE 1 — Teacher (Structured Data Analytics Mode)

*Pandas + SQL focus. Stages S0–S12, methods per stage.*

---

## Pedagogical Depth

### 1. How do you prevent me from seeing the correct solution before I attempt it?

**No.** There is no code that hides the solution or gates it behind an attempt. The prompt (e.g. `prompt_v6.md`, `layer4_complete_v2.md`) describes pedagogy (e.g. "Confirm their answer, correct if needed, then proceed to LOCK"; "User answers BEFORE running it"). Whether the model withholds the solution is prompt-dependent only. The UI does not separate "attempt" from "solution" or enforce order.

**Risk: Medium.** Behavior is model-dependent; a user can ask for the answer immediately.

---

### 2. Do you enforce a minimum struggle period?

**No.** There is no timer, minimum-attempt count, or "struggle period" in code. Progression is "user does something → model responds → parser may emit lock." The user can type "next" / "done" / "skip" and the Teacher prompt explicitly says to accept and proceed to LOCK. So there is no enforced minimum struggle.

**Risk: High.** Users can progress without sustained effort.

---

### 3. Do you track how long I spend before asking for help?

**Partially.** `compute_avg_response_time(session_id)` exists in `teacher/app/db.py`: it measures the average time between an *assistant* message and the *next user* message (engagement latency). It is not "time before first help request" or "time on task before asking for a hint." So you track *response cadence*, not *time before asking for help*.

**Risk: Medium.** Useful for session analytics but not for the intended pedagogical metric.

---

### 4. Do you detect repeated mistake patterns?

**Yes.** Implemented in code:

- `learner_analytics.py`: `detect_errors_in_message()` (ERROR_KEYWORDS), `upsert_struggle()` for recurring errors, frustration, confusion, category weakness.
- `db.py`: `struggle_patterns` table (pattern_type, category, frequency, adaptation_rule); `method_progress.errors_hit` (JSON list per method).
- Adaptation rules: `get_struggle_patterns(min_frequency=2)` and fragile methods are injected into the prompt so the model can adapt.

**Concrete:** Repeated mistakes are logged and surface in the prompt as teaching adaptations.

---

### 5. Do you adapt future problems based on past errors?

**Yes.** Same pipeline as above: struggle patterns and fragile methods are passed into `build_learner_context()` → `_build_adaptation_rules()` and injected into the system prompt. The model is instructed to pre-teach failure modes, give extra depth on fragile methods, and double down on weak areas. Adaptation is prompt-driven from stored data, not separate "problem selection" logic.

**Concrete:** Yes; adaptation is data-driven and injected into the prompt.

---

## Technical Rigor

### 6. Do you test real-world messy data?

**Not in code.** The stage method map and docs mention real-world concerns (e.g. `df.isna()`, nulls, cleaning). Whether the *model* gives messy data or the user works on messy data is not enforced or tested by the app. No automated data-quality or "messy dataset" checks.

**Risk: High.** If the model only uses clean examples, training is shallow.

---

### 7. Do you test NULL handling edge cases?

**Not in code.** NULLs appear in the curriculum (e.g. in `prompts.py` STAGE_METHOD_MAP: "WHERE col IS NULL", "SELECT COUNT(*) - COUNT(col) AS nulls"). There is no automated test or assertion that the user has demonstrated NULL handling. Coverage is curricular only.

**Risk: Medium.** NULL handling is taught but not verified by the system.

---

### 8. Do you force JOIN complexity beyond basic examples?

**Not in code.** JOINs (including LEFT JOIN, CTE, subqueries) are in the stage method map and knowledge. Progression is by method lock (regex/parser), not by "JOIN difficulty level." The model can keep giving basic JOINs; there is no code that forces harder JOINs before lock.

**Risk: Medium.** Complexity is prompt/curriculum-dependent, not enforced.

---

### 9. Do you require performance considerations?

**Not in code.** The prompt (e.g. layer docs) mentions "TIME COMPLEXITY ANALYSIS" and efficiency. There is no code that requires the user to discuss or demonstrate performance, or that grades answers on performance.

**Risk: Medium.** Purely prompt-level.

---

### 10. Do you sometimes require rewriting solutions in alternative forms?

**No.** There is no code that requires "now do the same in SQL" or "rewrite this with a different pattern." Teacher is linear stage/method; locking is on method completion. Pythonic vs non-Pythonic is enforced only in Teacher Practice / Metacode via `python_mastery` for certain topics, not in Teacher.

**Risk: Low for Teacher.** Single-form demonstration per method.

---

## Memory Reinforcement

### 11. Do you revisit previously failed concepts after a time delay?

**Yes, partially.** `get_methods_due_for_review(days_threshold=7)` in `teacher/app/db.py` returns methods locked 7+ days ago. This is used in `_build_adaptation_rules()` and injected into the prompt: "SPACED REPETITION: These methods are due for review" and "When you encounter these methods, briefly confirm the user still remembers them." So the *system surfaces* what is due for review; the *model* is instructed to revisit. There is no automatic "pop quiz" or forced review session in code.

**Concrete:** Revisit is prompt-driven from DB; no hard gate or mandatory review flow.

---

### 12. Do you retest without context?

**No.** There is no mode that strips context and asks "solve X from memory." Run 2+ prompt says "Recall-first mode" and "Hardened methods = 'Write it from memory'" but that is model instruction. The app does not present a context-free retest or measure it separately.

**Risk: High.** Recall is not objectively tested; retention can be overestimated.

---

### 13. Do you measure recall vs recognition?

**No.** Mastery levels (unseen, fragile, familiar, confident, hardened) are derived from *attempts* and *errors* in `record_mastery` / `promote_mastery`, not from a recall test (e.g. "reproduce without hints"). No separate recall vs recognition metric.

**Risk: High.** You track effort and errors, not true recall.

---

## Progress Measurement

### 14. What metric defines "SQL 6/10" in this system?

**There is none.** The system has: methods locked per stage, mastery_level per method, run_number, attempts, errors. There is no defined scale (e.g. "6/10") or competency score. "SQL 6/10" is not computed or displayed.

**Concrete:** No such metric exists.

---

### 15. What measurable change should occur after 9 weeks?

**Not defined.** No 9-week target or outcome metric in code or config. You could infer from methods_locked, error counts, or session summaries, but no explicit "after 9 weeks, X should improve by Y."

**Risk: Critical for outcome-based design.** Redesign needed if the goal is measurable improvement.

---

### 16. Do you track error rate reduction over time?

**Partially.** Errors are logged (learner_events, method_progress.errors_hit, struggle_patterns). There is no aggregated "error rate over time" (e.g. errors per attempt per week) or dashboard. Data exists; the metric is not computed or exposed.

**Concrete:** Raw error data yes; error-rate-over-time no.

---

### 17. Do you track time-to-solution improvement?

**Partially.** `compute_avg_response_time` tracks average time between assistant message and next user message per session. That is a proxy for engagement speed, not "time to solve problem X." There is no per-method or per-problem time-to-solution or improvement trend.

**Concrete:** Session-level response time yes; time-to-solution improvement no.

---

# 🟡 CODEBASE 2 — Teacher Practice (Free Topic Teaching Mode)

*Concept exploration. Topic/category from TOPIC_MENU; "one drill at a time"; Challenge Mode (Guided / Semi-Guided / Independent).*

---

## Depth Control

### 1. Do you prevent overconsumption of explanation without practice?

**No.** There is no code that limits explanation length, number of messages, or "read time" before practice. The concept is locked when the model emits a lock and the parser accepts it. The model can write long explanations; the user can request more explanation without ever attempting. No gate in code.

**Risk: High.** Topic mode can become explanation-heavy without practice.

---

### 2. Do you force practice after teaching?

**Only via lock.** Practice is "demonstrate / answer then lock." The transition_engine only applies a lock when the model proposes it and the parser validates. There is no code that enforces "minimum N attempts" or "you must try before solution." So practice is *the path to lock*, but not *forced* in a strict sense (user can say "skip" and the prompt may still allow lock).

**Concrete:** Practice is the intended path to lock; not strictly enforced in code.

---

### 3. Do you restrict topic jumping?

**No.** The user can select any topic and category from the sidebar at any time (`TOPIC_MENU`, "Practice This Topic"). `transition_engine` allows `topic_change` to any topic in `TOPIC_MENU`. There is no prerequisite check or "complete X before Y."

**Risk: High.** Unlimited topic hopping is allowed; discipline is not enforced.

---

### 4. Do you detect when I'm avoiding hard topics?

**No.** Confusion/frustration per topic are logged (`learner_events`, `topic_difficulty` → `slow_topics` in learner_profile). That data could be used to infer "hard" topics, but there is no code that detects "user only picks easy topics" or nudges/blocks to balance difficulty. No avoidance detection.

**Concrete:** No.

---

## Concept Retention

### 5. Do you test what I "learned" 24–72 hours later?

**Not on a 24–72h schedule.** `get_concepts_due_for_review(days_threshold=7)` exists; concepts locked 7+ days ago are surfaced for review in the prompt. There is no 24–72 hour specific test or forced quiz. So delayed review is at 7 days, and again prompt-driven, not a mandatory test.

**Concrete:** 7-day review is surfaced; no 24–72h test.

---

### 6. Do you require active recall?

**Only in prompt.** Run 2+ instructions say "Confirm recall on hardened concepts" and "Recall-first mode." The app does not require the user to type an answer from memory or pass a recall check before progressing. So no code-enforced active recall.

**Risk: High.** Illusion of knowledge if the model keeps re-explaining.

---

### 7. Do you mix old topics with new ones?

**Not enforced.** Adaptation rules can mention fragile concepts and "due for review"; the model is instructed to mix. There is no code that schedules or enforces "today 2 old, 1 new" or similar. Mixing is prompt-only.

**Concrete:** No.

---

## Structural Safety

### 8. Can I skip foundational topics?

**Yes.** Any topic in `TOPIC_MENU` can be selected. There is no prerequisite graph or "foundations first" gate. User can start with "System Design" and never do "Python" or "SQL."

**Risk: High.** Becomes comfort mode if users avoid foundations.

---

### 9. Do you enforce prerequisites?

**No.** No prerequisite relation in code or data. `transition_engine._guard_topic_change` only checks `proposal.topic in TOPIC_MENU`. No "topic B requires topic A" logic.

**Concrete:** No.

---

### 10. Is progression gated?

**Only within a topic.** Within one topic, concepts have an order (`concept_number`); "next concept" is the first unlocked. But the user can at any time switch topic (sidebar). So progression is linear within a topic but not gated across topics.

**Concrete:** Gated only within current topic; not across the curriculum.

---

# 🔴 CODEBASE 3 — Metacode (Forced Practice Mode)

*Same structure as Teacher Practice (topics, concepts, lock). "One concept at a time. Any topic. Full depth." No Challenge Mode in UI (unlike Teacher Practice).*

---

## Friction Enforcement

### 1. Can I skip a problem?

**Yes.** There is no code that blocks "next" or "skip." The Teacher prompt (shared pedagogical culture) says: "When the user says 'next', 'done', 'skip' during or after Practice (Anchor 8), accept immediately. No friction. Proceed to LOCK." So the system is explicitly designed to allow skip and still progress.

**Risk: Critical for "forced" practice.** Friction is low; skip is allowed.

---

### 2. Can I request the solution immediately?

**Nothing prevents it.** The user can ask "give me the answer." Whether the model refuses is prompt-dependent. There is no code that blocks the message or forces "attempt first."

**Concrete:** No enforcement; request-solution is possible.

---

### 3. Is there a timed component?

**No.** No timer in the codebase. No time limit per concept or per session. No "solve in under N minutes" or interview-style timer.

**Risk: High.** No time pressure; cannot simulate interview conditions.

---

### 4. Are hints restricted?

**No.** No hint counter, hint budget, or "max hints per problem." The user can ask for hints repeatedly; the model can give as much as it wants.

**Concrete:** No.

---

### 5. Do you require manual rewrite after correction?

**No.** No code that requires "now write it again in your own words" or "retype the solution" after a correction. Lock can happen after model correction without a second attempt from the user.

**Concrete:** No.

---

## Adaptive Difficulty

### 6. How do you increase difficulty?

**Only via prompt.** Run 2+ and adaptation rules say "Challenge the user," "Push for speed and accuracy," "Recall-first mode." Fragile concepts get "give extra depth." There is no code that increases problem difficulty (e.g. harder variants, more constraints). Difficulty is model interpretation.

**Concrete:** No programmed difficulty scaling.

---

### 7. What triggers harder problems?

**Nothing in code.** No trigger such as "after 3 correct in a row, switch to hard." Harder problems are not generated or selected by the app; the model may choose to give harder tasks based on prompt instructions.

**Concrete:** No.

---

### 8. Do you mix problem types?

**Not in code.** Concepts are in a linear order per topic. No logic that mixes "drill type A" with "drill type B" or cycles through categories. Mixing would be model-driven.

**Concrete:** No.

---

### 9. Do you simulate interview-style pressure?

**No.** No timer, no peer comparison, no "interview mode" flag. Pressure would be only from prompt tone.

**Concrete:** No.

---

## Error Heatmap

### 10. Do you log my most common mistakes?

**Yes.** Same as Teacher / Teacher Practice: `learner_events` (event_type e.g. error, confusion), `concept_progress.errors_hit`, `struggle_patterns` with frequency. Common mistakes are logged and aggregated in learner_profile (e.g. common_error_types).

**Concrete:** Yes.

---

### 11. Do you generate targeted drills based on weakness?

**Partially.** Weakness (fragile concepts, struggle patterns) is injected into the prompt via `build_learner_context()` and `_build_adaptation_rules()`. The model is instructed to "give extra depth" and "double down on fragile ones." There is no separate "drill generator" that produces targeted exercises from the error heatmap. So targeting is prompt-driven, not generated drills.

**Concrete:** Targeting via prompt; no automated drill generation.

---

### 12. Do you escalate repetition on weak areas?

**Partially.** Spaced repetition surfaces "concepts due for review" (7+ days); adaptation says "double down on fragile ones." There is no numeric escalation (e.g. "3x more problems on weak areas" or "repeat until 2 correct in a row"). Repetition is model-guided, not escalated by code.

**Concrete:** Prompt-level emphasis; no escalation logic.

---

## Adversarial Questions

### 13. How could a user game this system and still "appear" to progress?

**Concrete ways:**

- Say "next" / "done" / "skip" and receive lock (prompt tells model to accept).
- Ask "give me the answer" or paste a solution from elsewhere; model may confirm and lock.
- Stick to easy topics and never pick hard ones (no prerequisite or balance check).
- Request hints until the model effectively gives the solution, then confirm.
- In Teacher: jump to a stage via "Practice This Stage" and rely on model to be lenient.

Progress is "concepts/methods locked"; locking depends on model output and parser. If the model is permissive, the user can progress without real struggle.

---

### 14. If I tried to avoid discomfort, how would I do it?

- Choose only easy or familiar topics (Teacher Practice / Metacode).
- Use "next" / "skip" to avoid doing the exercise (all codebases where that prompt exists).
- Ask for the solution or full code and paste it (no attempt-first gate).
- Switch topic as soon as something gets hard (no lock on topic completion).
- Avoid Challenge Mode in Teacher Practice, or pick "Guided" only (if that tier is easier).

No code prevents these; only prompt design can discourage them.

---

# 🧠 SYSTEM-WIDE QUESTIONS

*(Apply across Teacher, Teacher Practice, Metacode.)*

---

### 1. Is learning state versioned?

**Yes.** `system_state` has a `version` column. Updates go through `update_system_state_with_version(conn, expected_version, **kwargs)` in the transition engine; concurrent updates can be rejected (version mismatch). So state transitions are versioned and guarded.

**Concrete:** Yes.

---

### 2. Are transitions guarded?

**Yes.** Transition engine validates every proposal (e.g. lock, decompose, topic_change): guards check topic in TOPIC_MENU, concept in decomposition or list, not already locked, decomposition not overwritten, etc. Rejected transitions are recorded in `state_events` with `rejection_reason`. Idempotency by `assistant_message_id` is enforced.

**Concrete:** Yes.

---

### 3. Can malformed output corrupt state?

**No.** Parser validates or rejects (e.g. STATE_UPDATE JSON); invalid proposals get `rejection_reason` and are not applied. Transition engine applies only validated updates with version check. So malformed model output does not corrupt state; it may result in no state change or a recorded failure.

**Concrete:** State is not corrupted by malformed output.

---

### 4. Is there logging for attempts and failure reasons?

**Yes.** `learner_events` (event_type, details, sentiment), `state_events` (rejection_reason, parser_mode), `concept_progress` / `method_progress` (attempts, errors_hit). Attempts and failure reasons are logged.

**Concrete:** Yes.

---

### 5. Can I export performance metrics?

**No.** No API or UI to export progress, metrics, or reports. Session summaries and events are stored in SQLite but there is no export to CSV/JSON or dashboard for the learner. So the system does not expose exportable performance metrics to the user.

**Concrete:** No.

---

### 6. Is there a measurable "competency threshold"?

**No.** No defined threshold such as "SQL 6/10" or "concepts locked ≥ N across topics." Mastery levels (unseen → hardened) are internal. There is no single "competent" or "ready" threshold in code or config.

**Concrete:** No.

---

### 7. Can the system objectively say: "You are SQL interview ready"?

**No.** It can report methods/concepts locked, mastery levels, and errors. It does not compute or declare "interview ready" or any equivalent. That would require a defined threshold and possibly a dedicated assessment; neither exists.

**Concrete:** No.

---

# 🔥 Most Important Final Question

**"If I train 30 hours per week for 9 weeks using these engines, what specific, measurable transformation will occur?"**

**Answer from the codebase:** The system does **not** define a 9-week or 30h/week outcome. It does **not** specify:

- "Average time to solve medium JOIN problems will drop from 25 minutes to under 10 minutes with <10% logical errors"
- "You will lock N methods per week"
- "Error rate will decrease by X%"

What *is* measurable in data but not defined as a *target*:

- Methods/concepts locked, run number, mastery levels, attempts, errors, session count, average response time between messages.

So the honest answer is: **no specific, measurable transformation is defined.** You could infer "you’ll have more methods locked and possibly lower error rate if you engage seriously," but that is vague. To be real, the system would need explicit outcome metrics and targets (e.g. time-to-solution, error rate, competency score) and optionally export/reporting.

**Verdict:** Today the answer is closer to "you’ll improve confidence" (vague) than to a concrete metric. Redesign is needed for outcome-driven claims.

---

# Step Back: What Enforces vs What Slows

| Enforced in code / data | Emphasized (prompt / design) |
|-------------------------|------------------------------|
| Struggle patterns and error logging | Struggle (but skip/next accepted) |
| Spaced repetition *surfaced* (7d due) | Recall (Run 2+ instructions) |
| Adaptation rules from data | Repetition on weak areas (prompt) |
| Versioned, guarded state | — |
| **Not present:** minimum struggle, timer, hint limits, prerequisite gates, topic balance, export, competency threshold | Explanation, guidance, topic freedom, comfort |

So: **explanation, guidance, comfort, and topic exploration are supported;** **struggle, recall, repetition, time pressure, and measurable progress are only partly enforced (or only in prompt).** That will slow outcome-oriented progress unless you add code-level enforcement and metrics.

---

# Calibration: Which Codebase Builds Muscle Without Explanation?

**Teacher (Codebase 1)** is the one that would still be most effective if all explanation capability were removed.

- Progression is **fixed** (stages S0–S12, methods per stage). The user must *do* something (run code, paste output, or confirm) for the parser to emit a lock. The curriculum is in the stage method map; the "teacher" could be reduced to "validate output and lock" and the pipeline would still advance.
- Teacher Practice and Metacode depend more on the model to *teach* then lock; without explanation, they become "try something → get lock or not." That can still build muscle if the model only locks on correct demonstration, but the design is more explanation-centric. Teacher’s structure (fixed sequence, method-level gates) makes it the one that most clearly builds muscle by structure alone.

**Concrete answer:** Teacher (Structured Data Analytics Mode) is the one that would still be effective if explanation were removed, because progression is gated by method completion and output, not by consuming explanations.
