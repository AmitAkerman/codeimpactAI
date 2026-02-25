import os

try:
    # Gemini SDK
    from google import genai
except Exception:
    genai = None


def _get_client():
    """
    יוצר Client רק אם יש גם SDK וגם GEMINI_API_KEY.
    אם חסר משהו — מחזיר None ולא מפיל את השרת.
    """
    if genai is None:
        return None

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    return genai.Client(api_key=api_key)


def generate_text(prompt: str) -> str:
    client = _get_client()
    if client is None:
        # fallback כדי שהמערכת תמשיך לעבוד (הגשה/טבלאות וכו')
        # ואת ה-AI פשוט "תכבי" עד שיש מפתח.
        return "Gemini לא מוגדר (אין GEMINI_API_KEY או שה-SDK לא מותקן)."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text or ""