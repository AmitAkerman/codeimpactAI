import random

from fastapi import HTTPException

from server.app.repositories.projects_repo import list_submissions_by_student, update_submission_grade
from server.app.repositories.rubrics_repo import insert_assignment, list_all_assignments, get_assignment
from server.app.repositories.users_repo import list_students


def get_students():
    students = list_students()
    # Add project count for UI
    for s in students:
        subs = list_submissions_by_student(s["id"])
        s["project_count"] = len(subs)
    return students


def create_rubric(teacher_id: str, title: str, class_name: str, criteria: list[dict]):
    return insert_assignment(teacher_id, title, class_name, criteria)


def get_rubrics():
    # Returns all assignments (used as rubrics)
    return list_all_assignments()


def get_student_projects(student_id: str):
    # Fetch submissions
    submissions = list_submissions_by_student(student_id)

    # We need to manually fetch titles for these submissions because 'submissions' table has no title
    # In a real app, you'd do a JOIN in the repo. Here we loop (n+1) or fetch all.
    # Optimization: Fetch all assignments once and map.
    all_assigns = {a["id"]: a["title"] for a in list_all_assignments()}

    for sub in submissions:
        aid = sub.get("assignment_id")
        sub["title"] = all_assigns.get(aid, "Unknown Assignment")

    return submissions


def analyze_ai(project_url: str, rubric_id: str):
    rubric = get_assignment(rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    ai_results = {}
    total_score = 0
    feedback_lines = []

    for crit in rubric["criteria"]:
        score = random.randint(70, 100)
        weighted_score = score * (crit["weight"] / 100)
        ai_results[crit["name"]] = score
        total_score += weighted_score
        feedback_lines.append(f"- **{crit['name']}**: Good implementation, but check edge cases.")

    final_feedback = "### AI Assessment:\n" + "\n".join(feedback_lines)

    return {
        "suggested_score": int(total_score),
        "suggested_feedback": final_feedback,
        "details": ai_results,
    }


def submit_grade(data: dict):
    # Use update_submission_grade from repo
    update_submission_grade(data["project_id"], data["total_score"], data["feedback"])
    return {"message": "Grade Saved"}
