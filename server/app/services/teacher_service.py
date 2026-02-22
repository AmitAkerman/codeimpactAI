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
        print("\n" + "=" * 50)
        print("SCRATCH PROJECT SUMMARY LOG:")
        print(json.dumps(project_summary, ensure_ascii=False, indent=4))
        print("=" * 50 + "\n")
        # -----------------------
    except Exception as e:
        project_summary = f"Could not parse blocks. Error: {str(e)}"

    # 4. הפיכת המחוון המעובד לטקסט JSON עבור הפרומפט
    rubric_context = json.dumps(formatted_rubric_list, ensure_ascii=False, indent=2)

    # 5. בניית הפרומפט המפורט
    # הגדרת הקריטריונים החדשים בתוך ה-Rubric
    rubric_context = """
    1. יצירתיות (משקל 30%):
       - חדשנות: נמוך (1-3) רעיון בנאלי | בינוני (4-6) שיפור רעיון קיים | גבוה (7-10) רעיון מקורי וייחודי.
       - פשטות ובהירות: נמוך (1-3) מסובך/קוד לא יעיל | בינוני (4-6) ברור תוך זמן קצר | גבוה (7-10) אינטואיטיבי לחלוטין.
       - רמה פדגוגית: נמוך (1-3) ידע-הבנה | בינוני (4-6) יישום-אנליזה | גבוה (7-10) סינטזה-הערכה.

    2. שימושיות (משקל 30%):
       - חווית משתמש (UX): נמוך (1-3) רכיבי ברירת מחדל | בינוני (4-6) עריכת דמויות/רקעים | גבוה (7-10) רקעים ייחודיים ומותאמים.
       - מולטימדיה: נמוך (1-3) ללא אלמנטים | בינוני (4-6) אנימציה בלבד | גבוה (7-10) שילוב מלא של אנימציה וצלילים.

    3. קוד ואלגוריתמיקה (משקל 40%):
       - ציון Dr. Scratch: נמוך (1-7) | בינוני (7-14) | גבוה (14-21).
       - מספר אובייקטים (Sprites): נמוך (עד 3) | בינוני (עד 5) | גבוה (עד 10).
       - אמצעי קלט: נמוך (1-3) מקלדת בלבד | בינוני (4-6) מקלדת ועכבר | גבוה (7-10) שימוש במצלמה.
       - ניהול אירועים ומסרים: נמוך (1-3) שימוש ב-Wait | בינוני (4-6) 2 מסרי Broadcast | גבוה (7-10) 5 מסרים ומעלה.
       - למידה עצמאית: נמוך (1-3) אלמנט אחד חדש | בינוני (4-6) 2 אלמנטים | גבוה (7-10) 3 אלמנטים ומעלה.
    """

    prompt = f"""
    עליך לשמש כמעריך פדגוגי מומחה ל-Scratch המנתח פרויקטים לעומק.
    נתח את הפרויקט בכתובת {project_url} על סמך הקריטריונים הבאים.

    ### מחוון הערכה (Rubrics):
    {rubric_context}

    ### נתוני קוד הפרויקט (Project Summary):
    {project_summary}

    ### נתוני Dr. Scratch:
    {dr_scratch_results}

    ### הנחיות עבודה למשוב:
    1. הצלבת נתונים: השתמש ברשימת ה-`broadcast_messages` ו-`total_sprites` מתוך נתוני הקוד כדי לקבוע את הציון בקטגוריית "ניהול אירועים ומסרים" ו"מספר אובייקטים".
    2. נימוק מבוסס ראיות: עבור כל קריטריון, ציין דוגמה ספציפית (שם של דמות, הודעת Broadcast ספציפית או בלוק מיוחד) שתומכת בציון שנתת.
    3. ניתוח פדגוגי: הסבר בעברית רהוטה מדוע הפרויקט נמצא ברמת "יישום" או "סינטזה" על סמך מורכבות הבלוקים.
    4. שקלול מתמטי: בצע חישוב מדויק לפי המשקלים (יצירתיות 30%, שימושיות 30%, קוד 40%).

    ### פורמט פלט נדרש (JSON בלבד):
    {{
        "suggested_score": 85,
        "suggested_feedback": "כותרת: יצירתיות... [נימוק]. כותרת: שימושיות... [נימוק]. כותרת: קוד... [נימוק].",
        "details": {{
            "innovation": 8,
            "ux": 5,
            "dr_scratch_sync": 14,
            "messages_management": 10,
            "independent_learning": 7
        }},
        "evidence_found": ["שמות הבלוקים או המסרים שהשפיעו על הציון"]
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