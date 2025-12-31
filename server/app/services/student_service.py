from server.app.repositories.projects_repo import list_submissions_by_student, insert_submission
from server.app.repositories.rubrics_repo import list_assignments_by_class


def get_student_dashboard(student_id: str, class_name: str):
    # 1. Get all assignments for this class (Source of Truth for titles)
    assignments = list_assignments_by_class(class_name)

    # 2. Get all submissions by this student
    submissions = list_submissions_by_student(student_id)

    # 3. Create a map for quick lookup: assignment_id -> submission
    sub_map = {s["assignment_id"]: s for s in submissions if s.get("assignment_id")}

    dashboard_items = []

    # 4. Merge
    for assign in assignments:
        aid = assign["id"]
        if aid in sub_map:
            # Student has submitted this assignment
            sub = sub_map[aid]
            dashboard_items.append({
                "assignment_id": aid,
                "title": assign["title"],  # Title comes from Assignment table
                "status": sub["status"],
                "link": sub["link"],
                "score": sub.get("score"),
                "feedback": sub.get("feedback"),
                "is_submitted": True
            })
        else:
            # Student has NOT submitted yet
            dashboard_items.append({
                "assignment_id": aid,
                "title": assign["title"],
                "status": "To Do",
                "link": "",
                "is_submitted": False
            })

    return dashboard_items


def submit_project(student_id: str, assignment_id: str, link: str):
    # Title is not passed here because it lives in the Assignment table
    return insert_submission(student_id, assignment_id, link)
