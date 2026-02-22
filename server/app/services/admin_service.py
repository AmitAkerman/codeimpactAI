import csv
import io

from server.app.repositories.projects_repo import list_all_submissions
from server.app.repositories.rubrics_repo import list_all_assignments
from server.app.repositories.users_repo import list_all_users, create_user


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

def bulk_add_teachers_from_csv(csv_content: str):
    f = io.StringIO(csv_content)
    reader = csv.DictReader(f)
    reader.fieldnames = [name.strip() for name in reader.fieldnames]

    success_count = 0
    errors = []

    for row in reader:
        try:
            user_data = {
                "username": row["username"].strip(),
                "password": row["password"].strip(),
                "role": "teacher", # Force the role to teacher
                "full_name": row.get("full_name", "").strip(),
                "class_name": None
            }
            create_user(user_data)
            success_count += 1
        except Exception as e:
            errors.append(f"Error creating {row.get('username')}: {str(e)}")

    return {"message": f"Successfully created {success_count} teachers.", "errors": errors}
