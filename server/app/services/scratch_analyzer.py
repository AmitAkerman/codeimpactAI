from .teacher_service import get_rubrics
from ..services.gemini_client import generate_text


class ScratchGradingService:
    def get_dynamic_rubric_text(self):
        """מושך את הרובריקות העדכניות והופך אותן לטקסט עבור הפרומפט"""
        rubrics = get_rubrics()
        rubric_description = "מחוון הערכה רשמי (Rubrics):\n"

        for category in rubrics:
            name = category.get("name")
            weight = category.get("weight")
            rubric_description += f"- {name} (משקל: {weight}%)\n"
            for sub in category.get("sub_criteria", []):
                rubric_description += f"  * {sub.get('name')} (משקל פנימי: {sub.get('weight')}%)\n"

        return rubric_description

    def analyze_project(self, project_json_summary, dr_scratch_data):
        # משיכת הרובריקות העדכניות מה-DB/Logic
        dynamic_rubrics = self.get_dynamic_rubric_text()

        system_prompt = f"""
        עליך לשמש כמעריך פרוייקטים פדגוגי מומחה ל-Scratch. 
        תפקידך לנתח את הפרויקט ולתת ציונים מדויקים על פי המחוון הבא בלבד:

        {dynamic_rubrics}

        הנחיות לביצוע: עבור כל סעיף במחוון, קבע רמה (נמוך/בינוני/גבוה), תן ניקוד מספרי, ונמק.
        """

        # בניית גוף הפרומפט עם נתוני הפרויקט
        user_content = f"""
        נתוני קוד הפרויקט: {project_json_summary}
        נתוני Dr. Scratch: {dr_scratch_data}
        """

        return generate_text(f"{system_prompt}\n{user_content}")