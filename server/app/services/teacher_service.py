import random
from fastapi import HTTPException
from server.app.repositories.projects_repo import list_submissions_by_student, update_submission_grade
from server.app.repositories.rubrics_repo import insert_assignment, list_all_assignments, get_assignment, \
    update_assignment
from server.app.repositories.users_repo import list_students


def get_students():
    students = list_students()
    for s in students:
        subs = list_submissions_by_student(s["id"])
        s["project_count"] = len(subs)
    return students


def create_rubric(teacher_id: str, title: str, class_name: str, criteria: list[dict]):
    return insert_assignment(teacher_id, title, class_name, criteria)


def get_rubrics():
    return list_all_assignments()


def get_student_projects(student_id: str):
    submissions = list_submissions_by_student(student_id)
    all_assigns = {a["id"]: a["title"] for a in list_all_assignments()}
    for sub in submissions:
        aid = sub.get("assignment_id")
        sub["title"] = all_assigns.get(aid, "Unknown Assignment")
    return submissions


def analyze_ai(project_url: str, rubric_id: str):
    rubric_data = get_assignment(rubric_id)
    if not rubric_data:
        raise HTTPException(status_code=404, detail="Rubric not found")

    rubric = rubric_data.get("criteria", [])

    # --- UPDATED LOGIC FOR HIERARCHICAL RUBRIC ---
    ai_results = {}
    total_score = 0
    feedback_lines = []

    # Check if rubric is nested (New format) or flat (Old format)
    is_nested = len(rubric) > 0 and "sub_criteria" in rubric[0]

    if is_nested:
        for cat in rubric:
            cat_name = cat["name"]
            cat_weight = cat["weight"]

            # Sub-category calculation
            cat_score_accum = 0
            sub_feedback = []

            for sub in cat["sub_criteria"]:
                # AI "grades" the sub-criteria
                raw_score = random.randint(70, 100)  # Mock AI Logic

                # Weight within the category (e.g., 50% of the category)
                sub_weight_val = sub["weight"]

                # Contribution to category score
                cat_score_accum += raw_score * (sub_weight_val / 100.0)

                ai_results[f"{cat_name} > {sub['name']}"] = raw_score
                sub_feedback.append(f"  - {sub['name']}: {raw_score}/100 (Solid implementation)")

            # Now add category score to total total
            # Category score is (cat_score_accum)
            # Contribution to Global Total is cat_score_accum * (cat_weight / 100)

            total_score += cat_score_accum * (cat_weight / 100.0)

            feedback_lines.append(f"**{cat_name}** (Calc Score: {int(cat_score_accum)})")
            feedback_lines.extend(sub_feedback)

    else:
        # FALLBACK: Old Flat Logic
        for crit in rubric:
            score = random.randint(70, 100)
            weighted_score = score * (crit["weight"] / 100)
            ai_results[crit["name"]] = score
            total_score += weighted_score
            feedback_lines.append(f"- **{crit['name']}**: Good implementation.")

    final_feedback = "### AI Assessment Report\n" + "\n".join(feedback_lines)

    return {
        "suggested_score": int(total_score),
        "suggested_feedback": final_feedback,
        "details": ai_results,
    }


def submit_grade(data: dict):
    update_submission_grade(data["project_id"], data["total_score"], data["feedback"])
    return {"message": "Grade Saved"}


def edit_rubric(assignment_id: str, title: str, class_name: str, criteria: list[dict]):
    return update_assignment(assignment_id, title, class_name, criteria)