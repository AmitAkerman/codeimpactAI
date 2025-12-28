from server.app.repositories.projects_repo import (
    list_projects_by_student,
    insert_project,
    join_projects_with_grades,
)

def get_student_projects(student_id: int):
    projs = list_projects_by_student(student_id)
    return join_projects_with_grades(projs)

def submit_project(student_id: int, title: str, link: str):
    return insert_project(student_id, title, link)
