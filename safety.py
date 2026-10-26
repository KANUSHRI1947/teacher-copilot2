"""Safety layer for Teacher Copilot.

Student records contain free text (teacher notes, contact notes, comments
copied in from parent portals or substitutes). Any of that text could contain
instructions aimed at the AI ("ignore your rules", "email every family...").
This module scans every free-text field BEFORE the record reaches an agent,
replaces suspicious text with a visible placeholder, and logs a flag the
teacher can see in the app.

No AI is used here: plain pattern matching, so it is fast, free, and testable.
"""

from __future__ import annotations

import re

# Phrases that read like instructions to an AI rather than facts about a student.
INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier|your) (instructions|rules|directions)",
    r"disregard (all |any |the )?(previous|prior|above|your) (instructions|rules)",
    r"forget (all |your )?(previous |prior )?(instructions|rules)",
    r"\b(system|developer) (prompt|message|override)\b",
    r"^\s*(system|assistant)\s*:",
    r"\byou are now\b",
    r"\bnew instructions?\s*:",
    r"(reveal|print|list|share|include|send) (all|every|the full|everyone'?s) (student|students|student's|grades|records|data)",
    r"\b(mark|label|flag|classify) (this student|him|her|them) as\b",
    r"do not (tell|inform|alert) the teacher",
    r"\bjailbreak\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_PATTERNS]

REDACTED = (
    "[REDACTED BY TEACHER COPILOT: this note contained text that looked like "
    "instructions to the AI. It was hidden from the AI and flagged for teacher review.]"
)


def looks_like_injection(text) -> str | None:
    """Return the matched phrase if text looks like a prompt injection, else None."""
    if not isinstance(text, str):
        return None
    for pattern in _COMPILED:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def sanitize_student(student: dict, flags: list) -> dict:
    """Return a copy of one student record with suspicious free text redacted.

    Every redaction is appended to ``flags`` so the app can show it.
    """
    clean = dict(student)
    sid = student.get("student_id", "?")
    name = student.get("name", "?")

    def check(text, field):
        hit = looks_like_injection(text)
        if hit:
            flags.append(
                {
                    "student_id": sid,
                    "name": name,
                    "field": field,
                    "matched": hit,
                    "original_text": text,
                }
            )
            return REDACTED
        return text

    # teacher_notes can be plain strings or {"text": ..., "evidence_type": ...}
    notes = []
    for note in student.get("teacher_notes", []) or []:
        if isinstance(note, dict):
            note = dict(note)
            note["text"] = check(note.get("text", ""), "teacher_notes")
        else:
            note = check(note, "teacher_notes")
        notes.append(note)
    clean["teacher_notes"] = notes

    if "strengths" in student:
        clean["strengths"] = [check(s, "strengths") for s in student.get("strengths") or []]

    history = []
    for contact in student.get("family_contact_history", []) or []:
        contact = dict(contact)
        if "note" in contact:
            contact["note"] = check(contact["note"], "family_contact_history")
        history.append(contact)
    clean["family_contact_history"] = history

    return clean


def dedupe_flags(flags: list) -> list:
    """Tools reload records many times per run; keep one flag per unique note."""
    seen, unique = set(), []
    for f in flags:
        key = (f["student_id"], f["field"], f["original_text"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique
