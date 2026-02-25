from fastapi import APIRouter
from ..models.teacher_model import RubricCreate, AIAnalysisRequest, GradeSubmit
from ..services.teacher_service import (
    get_students, get_student_projects, create_rubric,
    get_rubrics, analyze_ai, submit_grade, edit_rubric
)

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

@router.post("/analyze_ai")
def teacher_ai(req: AIAnalysisRequest):
    return analyze_ai(req.project_url, req.rubrics)

@router.post("/grade")
def teacher_grade(g: GradeSubmit):
    return submit_grade(g.model_dump())

@router.put("/rubrics/{rubric_id}")
def teacher_update_rubric(rubric_id: str, r: RubricCreate):
    return edit_rubric(rubric_id, r.title, r.class_name, r.criteria)