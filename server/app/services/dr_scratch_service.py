import requests
import re


def analyze_with_dr_scratch(url: str):
    # 1. חילוץ ה-Project ID מה-URL
    project_id_match = re.search(r'projects/(\d+)', url)
    if not project_id_match:
        return {"error": "Invalid Scratch URL"}

    project_id = project_id_match.group(1)

    # 2. בניית הכתובת ל-API של Dr. Scratch
    api_url = f"https://www.drscratch.org/api/analyze/{project_id}"

    try:
        # 3. ביצוע הקריאה
        # response = requests.get(api_url, timeout=10)  # הוספת timeout למניעת תקיעה
        response = requests.post("https://www.drscratch.org/api/analyze/", json={"project_id": project_id})
        if response.status_code == 200:
            return response.json()
        return {"error": f"Dr. Scratch returned error {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}