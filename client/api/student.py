from .client import get, post

def list_projects(student_id: int):
    return get(f"/student/{student_id}/projects")

def submit_project(student_id: int, title: str, link: str):
    return post("/student/submit", {"student_id": student_id, "title": title, "link": link})
