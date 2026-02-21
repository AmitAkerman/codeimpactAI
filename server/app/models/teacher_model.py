


from typing import Any, List

from pydantic import BaseModel


class RubricCreate(BaseModel):
    teacher_id: str
    title: str
    class_name: str
    criteria: list[dict]


class AIAnalysisRequest(BaseModel):
    project_url: str
    rubrics: List[Any]

class GradeSubmit(BaseModel):
    project_id: str
    rubric_id: str
    total_score: int
    feedback: str
    details: dict[str, Any]


