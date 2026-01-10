from .client import get, post

def list_dashboard(student_id: str, class_name: str):
    # This fetches the assignments for the student dashboard
    return get(f"/student/dashboard/{student_id}?class_name={class_name}")

def submit_project(student_id: str, assignment_id: str, link: str):
    # This sends the project submission to the server
    return post("/student/submit", {
        "student_id": student_id,
        "assignment_id": assignment_id,
        "link": link
    })