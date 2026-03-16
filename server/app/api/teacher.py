from fastapi import APIRouter, HTTPException
from ..models.teacher_model import RubricCreate, AIAnalysisRequest, GradeSubmit
from ..services.teacher_service import (
    get_students, get_student_projects, create_rubric,
    get_rubrics, analyze_ai, submit_grade, edit_rubric
)
from ..services.scratch_parser import download_and_parse_scratch, get_project_token
from ..repositories.db import supabase

router = APIRouter(prefix="/teacher", tags=["teacher"])

@router.get("/students")
def teacher_students():
    return get_students()

@router.get("/student/{student_id}/projects")
def teacher_student_projects(student_id: int):
    return get_student_projects(student_id)

@router.post("/rubrics")
def teacher_create_rubric(r: RubricCreate):
    create_rubric(teacher_id=r.teacher_id, title=r.title, criteria=r.criteria, class_name=r.class_name)
    return {"message": "Rubric Created"}

@router.get("/rubrics")
def teacher_list_rubrics():
    return get_rubrics()

@router.put("/rubrics/{rubric_id}")
def teacher_update_rubric(rubric_id: str, r: RubricCreate):
    return edit_rubric(rubric_id, r.title, r.class_name, r.criteria)

@router.delete("/rubrics/{rubric_id}")
def delete_rubric(rubric_id: str):
    # Migrated from old main.py
    response = supabase.table("assignments").delete().eq("id", rubric_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Rubric not found or already deleted")
    return {"message": "Rubric Deleted"}

@router.post("/analyze_ai")
def teacher_ai(req: AIAnalysisRequest):
    return analyze_ai(req.project_url, req.rubrics)

@router.post("/grade")
def teacher_grade(g: GradeSubmit):
    return submit_grade(g.model_dump())

@router.get("/test_dr_scratch/{project_id}")
def test_dr_scratch(project_id: str, token: str = None):
    if not token:
        token = get_project_token(project_id)
        print(f"DEBUG: Automatically fetched token: {token}")

    result = download_and_parse_scratch(project_id, token)

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result