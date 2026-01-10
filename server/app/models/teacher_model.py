


from typing import Any

from pydantic import BaseModel


class RubricCreate(BaseModel):
    teacher_id: str
    title: str
    class_name: str
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


