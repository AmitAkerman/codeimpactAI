import json
import random
from typing import List, Any

from fastapi import HTTPException
from ..repositories.projects_repo import list_submissions_by_student, update_submission_grade
from ..repositories.rubrics_repo import insert_assignment, list_all_assignments, get_assignment, \
    update_assignment
from ..repositories.users_repo import list_students
from ..services.gemini_client import generate_text
from ..services.scratch_parser import download_and_parse_scratch


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


def analyze_ai(project_url: str, rubrics: List[Any]):
    """
    מנתחת פרויקט סקראץ' בעזרת AI על בסיס רשימת רובריקות שנשלחה מהקליאנט.
    """
    # 1. עיבוד רשימת הרובריקות שהתקבלה מהבקשה
    # אנחנו רצים על הרשימה כדי לוודא שכל המידע (שם, משקל ותתי-קריטריונים) עובר
    formatted_rubric_list = []
    for category in rubrics:
        category_info = {
            "category_name": category.get("name"),
            "category_weight": category.get("weight"),
            "sub_criteria": category.get("sub_criteria", []),
            "description": category.get("description", "")
        }
        formatted_rubric_list.append(category_info)

    # 2. נתוני Dr. Scratch - Mock לבדיקות
    dr_scratch_results = {"score": 14, "mastery": "Medium"}

    # 3. ניתוח קוד ה-Scratch (הורדת ה-JSON)
    try:
        project_summary = download_and_parse_scratch(project_url)
    except Exception as e:
        project_summary = f"Could not parse blocks. Error: {str(e)}"

    # 4. הפיכת המחוון המעובד לטקסט JSON עבור הפרומפט
    rubric_context = json.dumps(formatted_rubric_list, ensure_ascii=False, indent=2)

    # 5. בניית הפרומפט המפורט
    prompt = f"""
    עליך לשמש כמעריך פדגוגי מומחה ל-Scratch. 
    נתח את הפרויקט בכתובת {project_url} על סמך המחוון ההיררכי הבא:

    ### מחוון הערכה (Rubrics):
    {rubric_context}

    ### נתוני קוד הפרויקט:
    {project_summary}

    ### נתוני Dr. Scratch:
    {dr_scratch_results}

    ### הנחיות מחמירות למשוב:
    1. עבור כל קטגוריה ברשימה, עליך לנתח כל תת-קריטריון בנפרד.
    2. לכל קטגוריה, כתוב כותרת ברורה ב-Markdown ולאחריה 2-3 משפטים של נימוק פדגוגי בעברית.
    3. בנימוק, ציין שמות של דמויות, משתנים או בלוקים ספציפיים שמצאת בקוד.
    4. בצע שקלול מתמטי מדויק: (ציון תת-קריטריון * משקל פנימי) -> ציון קטגוריה. סכום ציוני הקטגוריות * משקלן -> ציון סופי.

    ### פורמט פלט נדרש (JSON בלבד):
    {{
        "suggested_score": 85,
        "suggested_feedback": "כאן יופיע הדו"ח המלא והמפורט בעברית עם כותרות לכל קטגוריה",
        "details": {{ "שם תת-הקריטריון": 85 }}
    }}
    """

    # 6. שליחה ל-AI
    try:
        ai_response_raw = generate_text(prompt)
        clean_json = ai_response_raw.replace("```json", "").replace("```", "").strip()
        ai_response = json.loads(clean_json)
    except Exception as e:
        return {
            "suggested_score": 0,
            "suggested_feedback": f"שגיאה בעיבוד ה-AI: {str(e)}",
            "details": {},
            "raw_dr_scratch": dr_scratch_results
        }

    return {
        "suggested_score": ai_response.get("suggested_score", 0),
        "suggested_feedback": ai_response.get("suggested_feedback", "לא ניתן לייצר משוב"),
        "details": ai_response.get("details", {}),
        "raw_dr_scratch": dr_scratch_results
    }


def submit_grade(data: dict):
    update_submission_grade(data["project_id"], data["total_score"], data["feedback"])
    return {"message": "Grade Saved"}


def edit_rubric(assignment_id: str, title: str, class_name: str, criteria: list[dict]):
    return update_assignment(assignment_id, title, class_name, criteria)