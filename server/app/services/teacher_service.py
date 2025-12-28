import random
from fastapi import HTTPException

from server.app.repositories.users_repo import list_students
from server.app.repositories.projects_repo import list_projects_by_student, join_projects_with_grades, set_project_graded
from server.app.repositories.rubrics_repo import insert_rubric, list_rubrics, get_rubric
from server.app.repositories.grades_repo import insert_grade

def get_students():
    students = list_students()
    # add project_count
    from server.app.repositories.projects_repo import list_projects_by_student
    for s in students:
        s["project_count"] = len(list_projects_by_student(s["id"]))
    return students

def get_student_projects(student_id: int):
    projs = list_projects_by_student(student_id)
    return join_projects_with_grades(projs)

def create_rubric(teacher_id: int, title: str, criteria: list[dict]):
    return insert_rubric(teacher_id, title, criteria)

def get_rubrics():
    return list_rubrics()

def analyze_ai(project_url: str, rubric_id: str):
    rubric = get_rubric(rubric_id)
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
    insert_grade(data)
    set_project_graded(data["project_id"])
    return {"message": "Grade Saved"}
