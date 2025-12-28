from pydantic import BaseModel

class ProjectSubmit(BaseModel):
    student_id: int
    title: str
    link: str
