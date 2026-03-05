# Documentation Standards

Guidelines for maintaining a clean, organized `docs/` directory and project root.

---

## File placement rules

| Type | Location | Examples |
|------|----------|---------|
| Project entry (how to run, file tree) | Root `README.md` | Quick start, architecture overview |
| Design docs, plans, specs | `docs/` | Vision, execution plans, architecture |
| Prompts and AI config | `agent/prompts/` | chat.txt, extract.txt |
| Code documentation | Inline docstrings | orchestrator.py, event_store.py |

**Never** put planning or documentation .md files in the project root (except `README.md`). All docs go in `docs/`.

---

## Document lifecycle

### 1. Active
The document describes current work or next steps. Listed in `docs/README.md` as "Active."

### 2. Reference
The document is accurate and useful but not being actively worked from. Describes vision, specs, or completed designs.

### 3. Archive
The document is historical. It may be outdated but is kept for context. Clearly marked as "Archive" in the index. **Never modify archive documents.**

### 4. Delete
The document is a completed task artifact, a superseded plan, or contains only outdated information that duplicates other docs. Remove it. Don't keep dead files.

---

## When to delete a document

Delete if ANY of these are true:
- It was a task/plan file and the work is **fully completed**
- It was an alignment/comparison doc and the code it compared against **no longer exists**
- Its content has been **fully absorbed** into another active document
- It has a generated hash-style filename (e.g., `split_app_cover_5c47e8ec.plan.md`) — these are task artifacts, not documentation

---

## Naming conventions

- Use `UPPER_SNAKE_CASE.md` for docs: `EXECUTION_PLAN.md`, `ARCHITECTURE_AND_PRODUCTION.md`
- Use `lower_snake_case` for code files: `event_store.py`, `schema.sql`
- Use descriptive names. Not `plan.md` or `notes.md`. Say what the plan is for.
- No hash suffixes or generated IDs in filenames

---

## Content standards

### Every document must have:
1. A clear `# Title` on line 1
2. A one-line description of its purpose within the first 5 lines
3. Its status (Active / Reference / Archive) — either in the doc itself or in `docs/README.md`

### Keep documents focused:
- One document = one purpose
- Don't mix "what we built" with "what we should build next"
- Don't duplicate content across docs. Cross-reference instead.

### When the codebase changes:
- Update `README.md` (root) if the file tree or architecture changed
- Update `docs/README.md` if docs were added/removed/moved
- Mark reference docs as outdated if the code diverged significantly (add a note at the top, don't rewrite the doc)

---

## `__pycache__/` and generated files

- Never commit `__pycache__/` directories
- Never commit `assistant.db` (it's user data)
- Never commit `.env` (it contains secrets)
- Add these to `.gitignore`

---

## Review checklist (run periodically)

- [ ] Are there any .md files in the project root besides `README.md`? → Move to `docs/` or delete
- [ ] Are there any docs in `docs/` not listed in `docs/README.md`? → Add to index or delete
- [ ] Are there any docs referencing code/tables/files that no longer exist? → Update or delete
- [ ] Are there any task artifact files with hash IDs in their names? → Delete if completed
- [ ] Are there `__pycache__/` directories? → Delete
- [ ] Is root `README.md` file tree accurate? → Update if needed
