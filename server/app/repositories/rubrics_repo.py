import uuid
from .db_mock import RUBRICS

def insert_rubric(teacher_id: int, title: str, criteria: list[dict]):
    new_r = {"id": str(uuid.uuid4())[:8], "teacher_id": teacher_id, "title": title, "criteria": criteria}
    RUBRICS.append(new_r)
    return new_r

def list_rubrics():
    return RUBRICS

def get_rubric(rubric_id: str):
    return next((r for r in RUBRICS if r["id"] == rubric_id), None)
