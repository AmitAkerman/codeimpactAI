from .db import supabase


def insert_grade(grade_data: dict):
    # The app passes: project_id, total_score, feedback, details
    # We update the 'submissions' table directly.

    update_data = {
        "final_score": grade_data["total_score"],
        "feedback": grade_data["feedback"],
        "status": "Graded"
    }

    response = supabase.table("submissions") \
        .update(update_data) \
        .eq("id", grade_data["project_id"]) \
        .execute()

    return response.data[0] if response.data else None


def list_grades():
    # Return all submissions that are graded
    response = supabase.table("submissions").select("*").eq("status", "Graded").execute()
    return response.data