from server.app.repositories.users_repo import list_all_users, create_user
from server.app.repositories.rubrics_repo import list_all_assignments
from server.app.repositories.projects_repo import list_all_submissions

def users():
    return list_all_users()

def stats():
    users_list = list_all_users()
    assignments = list_all_assignments()
    submissions = list_all_submissions()

    return {
        "students": len([u for u in users_list if u.get("role") == "student"]),
        "teachers": len([u for u in users_list if u.get("role") == "teacher"]),
        "projects": len(assignments),
        "submissions": len(submissions),
        "graded": len([s for s in submissions if s.get("status") == "Graded"]),
    }

def add_user(user_data: dict):
    return create_user(user_data)