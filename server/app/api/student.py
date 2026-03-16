from fastapi import APIRouter, HTTPException
from server.app.models.student_model import ProjectSubmit, ProjectUpdate
from server.app.services.student_service import get_student_dashboard, submit_project
from server.app.repositories.db import supabase

# This is the 'router' that main.py is trying to import
router = APIRouter(prefix="/student", tags=["student"])
@router.get("/dashboard/{student_id}")
def student_dashboard(student_id: str, class_name: str):
    return get_student_dashboard(student_id, class_name)

@router.post("/submit")
def student_submit(p: ProjectSubmit):
    return submit_project(p.student_id, p.assignment_id, p.link)

@router.put("/projects/{project_id}")
def update_project(project_id: str, p: ProjectUpdate):
    # This was migrated from the old main.py
    response = supabase.table("submissions").update({"link": p.link}).eq("id", project_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project updated successfully"}