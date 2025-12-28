import uuid
from .db_mock import PROJECTS, GRADES, now_str

def list_projects_by_student(student_id: int):
    return [p for p in PROJECTS if p["student_id"] == student_id]

def insert_project(student_id: int, title: str, link: str):
    new_p = {
        "id": str(uuid.uuid4())[:8],
        "student_id": student_id,
        "title": title,
        "link": link,
        "status": "Pending",
        "submitted_at": now_str(),
    }
    PROJECTS.append(new_p)
    return new_p

def set_project_graded(project_id: str):
    for p in PROJECTS:
        if p["id"] == project_id:
            p["status"] = "Graded"
            return True
    return False

def get_project(project_id: str):
    return next((p for p in PROJECTS if p["id"] == project_id), None)

def join_projects_with_grades(projects: list[dict]):
    results = []
    for p in projects:
        grade = next((g for g in GRADES if g["project_id"] == p["id"]), None)
        p_data = p.copy()
        if grade:
            p_data["status"] = "Graded"
            p_data["score"] = grade["total_score"]
            p_data["feedback"] = grade["feedback"]
        else:
            p_data["status"] = "Pending"
        results.append(p_data)
    return results
