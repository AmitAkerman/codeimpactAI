from .db import supabase


def insert_assignment(teacher_id: str, title: str, class_name: str, criteria: list[dict]):
    # Matches 'assignments' table structure
    new_assignment = {
        "teacher_id": teacher_id,
        "title": title,
        "class_name": class_name,
        "rubric": criteria  # Stored in 'rubric' jsonb column
    }
    response = supabase.table("assignments").insert(new_assignment).execute()

    # Return mapped data
    data = response.data[0]
    return {
        "id": data["id"],
        "teacher_id": data["teacher_id"],
        "title": data["title"],
        "class_name": data["class_name"],
        "criteria": data["rubric"]
    }


def list_assignments_by_class(class_name: str):
    # Fetch assignments for a specific class
    response = supabase.table("assignments").select("*").eq("class_name", class_name).execute()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "criteria": r["rubric"]
        }
        for r in response.data
    ]


def list_all_assignments():
    response = supabase.table("assignments").select("*").execute()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "class_name": r["class_name"],
            "criteria": r["rubric"]
        }
        for r in response.data
    ]


def get_assignment(assignment_id: str):
    response = supabase.table("assignments").select("*").eq("id", assignment_id).execute()
    if not response.data:
        return None
    data = response.data[0]
    return {
        "id": data["id"],
        "title": data["title"],
        "criteria": data["rubric"]
    }

def update_assignment(assignment_id: str, title: str, class_name: str, criteria: list[dict]):
    update_data = {
        "title": title,
        "class_name": class_name,
        "rubric": criteria
    }
    response = supabase.table("assignments").update(update_data).eq("id", assignment_id).execute()
    return response.data[0] if response.data else None
