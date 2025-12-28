from pydantic import BaseModel
from typing import Any

class RubricCreate(BaseModel):
    teacher_id: int
    title: str
    criteria: list[dict]

class AIAnalysisRequest(BaseModel):
    project_url: str
    rubric_id: str

class GradeSubmit(BaseModel):
    project_id: str
    rubric_id: str
    total_score: int
    feedback: str
    details: dict[str, Any]
