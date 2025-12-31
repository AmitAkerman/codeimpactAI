from fastapi import APIRouter
from server.app.models.student_model import ProjectSubmit
from server.app.services.student_service import get_student_dashboard, submit_project

# This is the 'router' that main.py is trying to import
router = APIRouter(prefix="/student", tags=["student"])

@router.get("/dashboard/{student_id}")
def student_dashboard(student_id: str, class_name: str):
    return get_student_dashboard(student_id, class_name)

@router.post("/submit")
def student_submit(p: ProjectSubmit):
    # Pass the fields from the Pydantic model to the service
    return submit_project(p.student_id, p.assignment_id, p.link)