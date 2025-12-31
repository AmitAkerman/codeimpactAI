from .db import supabase, now_str

def list_submissions_by_student(student_id: str):
    # Selects from 'submissions' table
    response = supabase.table("submissions").select("*").eq("student_id", student_id).execute()

    projects = []
    for row in response.data:
        projects.append({
            "id": row["id"],
            "student_id": row["student_id"],
            "assignment_id": row["assignment_id"],
            "link": row["link"],
            "status": row["status"] or "Pending",
            "submitted_at": row["submitted_at"],
            "score": row.get("final_score"),
            "feedback": row.get("feedback")
        })
    return projects

def list_all_submissions():
    """Fetches all submissions for admin stats."""
    response = supabase.table("submissions").select("*").execute()
    return response.data if response.data else []

def insert_submission(student_id: str, assignment_id: str, link: str):
    new_sub = {
        "student_id": student_id,
        "assignment_id": assignment_id,
        "link": link,
        "status": "Pending",
        "submitted_at": now_str()
    }
    response = supabase.table("submissions").insert(new_sub).execute()
    row = response.data[0]

    return {
        "id": row["id"],
        "student_id": row["student_id"],
        "assignment_id": row["assignment_id"],
        "link": row["link"],
        "status": row["status"],
        "submitted_at": row["submitted_at"]
    }

def update_submission_grade(submission_id: str, score: int, feedback: str):
    update_data = {
        "final_score": score,
        "feedback": feedback,
        "status": "Graded"
    }
    response = supabase.table("submissions").update(update_data).eq("id", submission_id).execute()
    return response.data[0] if response.data else None