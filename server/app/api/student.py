from fastapi import APIRouter
from server.app.models.student_model import ProjectSubmit
from server.app.services.student_service import get_student_projects, submit_project

router = APIRouter(prefix="/student", tags=["student"])

@router.get("/{student_id}/projects")
def student_projects(student_id: int):
    return get_student_projects(student_id)

@router.post("/submit")
def student_submit(proj: ProjectSubmit):
    submit_project(proj.student_id, proj.title, proj.link)
    return {"message": "Submitted"}
