from server.app.repositories.users_repo import list_all_users
from server.app.repositories.db_mock import PROJECTS
from server.app.repositories.grades_repo import list_grades

def users():
    return list_all_users()

def stats():
    users_list = list_all_users()
    grades = list_grades()

    return {
        "students": len([u for u in users_list if u["role"] == "student"]),
        "teachers": len([u for u in users_list if u["role"] == "teacher"]),
        "projects": len(PROJECTS),
        "graded": len(grades),
    }
