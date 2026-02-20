from typing import List, Any

from . import client
from .client import get, post

def list_students():
    return get("/teacher/students")

def list_rubrics():
    return get("/teacher/rubrics")

def create_rubric(teacher_id: int, title: str, criteria: list[dict]):
    return post("/teacher/rubrics", {"teacher_id": teacher_id, "title": title, "criteria": criteria})

def list_student_projects(student_id: int):
    return get(f"/teacher/student/{student_id}/projects")

def analyze_ai(project_url: str, rubrics: List[Any]):
    return post("/teacher/analyze_ai", {"project_url": project_url, "rubrics": rubrics})

def submit_grade(project_id: str, rubric_id: str, total_score: int, feedback: str, details: dict):
    return post("/teacher/grade", {
        "project_id": project_id,
        "rubric_id": rubric_id,
        "total_score": total_score,
        "feedback": feedback,
        "details": details
    })


def update_rubric(assignment_id: str, teacher_id: str, title: str, class_name: str, criteria: list[dict]):
    return client.put(f"/teacher/rubrics/{assignment_id}", {
        "teacher_id": teacher_id,
        "title": title,
        "class_name": class_name,
        "criteria": criteria
    })
