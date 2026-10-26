import json
from pathlib import Path

from safety import sanitize_student, dedupe_flags

# Folder is "Data" (capital D). Linux/graders' machines are case-sensitive.
DATA_PATH = Path(__file__).resolve().parent / "Data" / "students.json"

# Every prompt-injection hit found while tools read records during a run.
SAFETY_FLAGS = []


def reset_safety_flags():
    SAFETY_FLAGS.clear()


def get_safety_flags():
    return dedupe_flags(SAFETY_FLAGS)


def load_students():
    """Load all student records, with suspicious free text redacted (see safety.py)."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [sanitize_student(s, SAFETY_FLAGS) for s in raw]


def search_students(query: str):
    """Search students by name, student ID, or course."""
    students = load_students()
    q = query.lower().strip()

    matches = []

    for student in students:
        if (
            q in student["name"].lower()
            or q in student["student_id"].lower()
            or q in student["course"].lower()
        ):
            matches.append(student)

    return matches


def get_student_profile(student_id: str):
    """Return the full record for one student."""
    students = load_students()

    for student in students:
        if student["student_id"].lower() == student_id.lower():
            return student

    return {"error": f"No student found with ID {student_id}"}


def get_class_summary(course: str):
    """Return student records for a specific course."""
    students = load_students()

    class_students = [
        student
        for student in students
        if student["course"].lower() == course.lower()
    ]

    return {
        "course": course,
        "student_count": len(class_students),
        "students": class_students,
    }


def get_family_contact_history(student_id: str):
    """Return family contact history for one student."""
    student = get_student_profile(student_id)

    if "error" in student:
        return student

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "family_contact_history": student["family_contact_history"],
    }



def get_positive_outreach_opportunities(course: str):
    """Find students who may be due for positive family outreach."""
    students = get_class_summary(course)["students"]
    opportunities = []

    for student in students:
        history = student.get("family_contact_history", [])

        positive_count = sum(
            1 for contact in history
            if contact.get("type") == "positive"
        )

        concern_count = sum(
            1 for contact in history
            if contact.get("type") in ["concern", "corrective", "negative"]
        )

        target_positive_count = concern_count * 5
        positives_needed = max(0, target_positive_count - positive_count)

        if not history:
            status = "No documented family contact. Consider positive outreach."
        elif positives_needed > 0:
            status = f"Below 5:1 positive-to-concern goal. {positives_needed} more positive contact(s) needed."
        else:
            status = "Currently meets the 5:1 positive-to-concern goal."

        opportunities.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "positive_contacts": positive_count,
            "concern_contacts": concern_count,
            "positives_needed_for_5_to_1": positives_needed,
            "status": status,
            "documented_strengths": student.get("teacher_notes", []),
        })

    return {
        "course": course,
        "goal": "Aim for about 5 positive or affirming family communications for every 1 concern-focused communication.",
        "students": opportunities,
    }


def get_family_message_context(student_id: str):
    """Gather documented information for a teacher-reviewed family message."""
    student = get_student_profile(student_id)

    if "error" in student:
        return student

    return {
        "student_id": student["student_id"],
        "name": student["name"],

        "family_preferred_language": student.get("family_preferred_language", "Not documented"),
        "primary_adult_supporter": student.get("primary_adult_supporter", "Not documented"),
        "strengths": student.get("strengths", []),
        "course": student["course"],
        "current_grade": student["current_grade"],
        "recent_assessment_scores": student["recent_assessment_scores"],
        "missing_assignments": student["missing_assignments"],
        "absences": student["absences"],
        "tardies": student["tardies"],
        "teacher_notes": student.get("teacher_notes", []),
        "family_contact_history": student.get("family_contact_history", []),
        "instruction": (
            "Use only documented information when drafting. "
            "Do not invent praise, concerns, or family circumstances. "
            "The message is a draft for teacher review and must never be sent automatically."
        ),
    }


def get_graduation_support_context(student_id: str):
    """Gather documented information for human-reviewed graduation planning."""
    student = get_student_profile(student_id)

    if "error" in student:
        return student

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "graduation_status": student.get("graduation_status", "Not documented"),
        "graduation_requirements": student.get("graduation_requirements", {}),
        "course": student["course"],
        "current_grade": student["current_grade"],
        "recent_assessment_scores": student["recent_assessment_scores"],
        "missing_assignments": student["missing_assignments"],
        "absences": student["absences"],
        "tardies": student["tardies"],
        "support_status": student.get("support_status", "Not documented"),
        "accommodations": student.get("accommodations", []),
        "strengths": student.get("strengths", []),
        "teacher_notes": student.get("teacher_notes", []),
        "family_contact_history": student.get("family_contact_history", []),
        "instruction": (
            "Use only documented information when discussing graduation planning. "
            "Do not declare the student eligible or ineligible for a waiver, appeal, "
            "alternative pathway, or other graduation option. "
            "If the record suggests that an additional pathway may be worth reviewing, "
            "recommend human verification with the appropriate school staff. "
            "Do not invent missing graduation requirements, policies, deadlines, or eligibility rules."
        ),
    }
def get_daily_triage(course: str):
    """Identify documented student priorities for teacher review."""
    students = get_class_summary(course)["students"]
    triage_results = []

    for student in students:
        reasons = []
        priority_points = 0

        grade = student.get("current_grade")
        scores = student.get("recent_assessment_scores", [])
        missing = student.get("missing_assignments", 0)
        absences = student.get("absences", 0)
        tardies = student.get("tardies", 0)
        graduation_status = student.get("graduation_status", "")

        if grade is not None and grade < 65:
            reasons.append(f"Current grade is {grade}.")
            priority_points += 2

        if len(scores) >= 3 and scores[-1] < scores[-2] < scores[-3]:
            reasons.append(
                f"Recent assessment scores declined: "
                f"{scores[-3]} -> {scores[-2]} -> {scores[-1]}."
            )
            priority_points += 2

        if missing >= 5:
            reasons.append(f"{missing} missing assignments.")
            priority_points += 2
        elif missing >= 2:
            reasons.append(f"{missing} missing assignments.")
            priority_points += 1

        if absences >= 5:
            reasons.append(f"{absences} documented absences.")
            priority_points += 2
        elif absences >= 3:
            reasons.append(f"{absences} documented absences.")
            priority_points += 1

        if tardies >= 5:
            reasons.append(f"{tardies} documented tardies.")
            priority_points += 1

        if "outstanding" in graduation_status.lower():
            reasons.append(
                f"Graduation status: {graduation_status}."
            )
            priority_points += 3

        if priority_points >= 5:
            priority = "HIGH"
        elif priority_points >= 2:
            priority = "MEDIUM"
        else:
            priority = "ROUTINE"

        triage_results.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "priority": priority,
            "priority_points": priority_points,
            "documented_reasons": reasons,
            "strengths": student.get("strengths", []),
            "family_contact_history": student.get(
                "family_contact_history", []
            ),
        })

    triage_results.sort(
        key=lambda student: student["priority_points"],
        reverse=True,
    )

    return {
        "course": course,
        "instruction": (
            "Use this triage only as a teacher decision-support tool. "
            "Priority levels are based only on the documented indicators "
            "listed here and are not diagnoses or disciplinary judgments. "
            "Explain why a student was prioritized and include documented "
            "strengths when available. The teacher makes all final decisions."
        ),
        "students": triage_results,
    }
