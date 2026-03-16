from pydantic import BaseModel

class ProjectSubmit(BaseModel):
    student_id: str
    assignment_id: str
    link: str

class ProjectUpdate(BaseModel):
    link: str