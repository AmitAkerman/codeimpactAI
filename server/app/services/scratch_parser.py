import requests
import re
import json

import requests
import re
import json

def get_project_token(project_id):
    """Fetches the project token required to download assets."""
    api_url = f"https://api.scratch.mit.edu/projects/{project_id}"
    res = requests.get(api_url)
    if res.status_code == 200:
        return res.json().get('project_token')
    return None
def download_and_parse_scratch(url: str, token: str = None):
    """
    1. מחלצת Project ID.
    2. משיגה Project Token (אם חסר).
    3. מורידה את ה-JSON משרתי ה-Assets.
    4. מנתחת ומחזירה סיכום מובנה.
    """
    # 1. חילוץ ה-Project ID מה-URL
    project_id_match = re.search(r'projects/(\d+)', url)
    if not project_id_match:
        # במקרה שהמשתמש שלח רק את ה-ID כמחרוזת
        project_id = url if url.isdigit() else None
        if not project_id:
            return {"error": "Invalid Scratch URL or ID"}
    else:
        project_id = project_id_match.group(1)

    # 2. השגת Token אוטומטית מ-api.scratch.mit.edu
    if not token:
        try:
            meta_url = f"https://api.scratch.mit.edu/projects/{project_id}"
            meta_res = requests.get(meta_url, timeout=5)
            if meta_res.status_code == 200:
                token = meta_res.json().get('project_token')
                print(f"DEBUG: Successfully fetched token: {token[:10]}...")
        except Exception as e:
            print(f"DEBUG: Token fetch failed: {e}")

    # 3. פנייה ל-Assets API (projects.scratch.mit.edu)
    assets_url = f"https://projects.scratch.mit.edu/{project_id}"
    params = {"token": token} if token else {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://scratch.mit.edu/"
    }

    try:
        response = requests.get(assets_url, headers=headers, params=params, timeout=10)

        if response.status_code == 403:
            return {"error": "Error 403: Forbidden. Project might be unshared or token invalid."}
        if response.status_code != 200:
            return {"error": f"Failed to download project. Status: {response.status_code}"}

        project_data = response.json()

        # 4. ניתוח הנתונים (Parsing) לפי המבנה ששלחת
        summary = {
            "project_id": project_id,
            "total_sprites": len(project_data.get('targets', [])),
            "sprites_details": []
        }

        for target in project_data.get('targets', []):
            blocks = target.get('blocks', {})

            # חילוץ ה-Opcodes מתוך אובייקט הבלוקים
            # אנחנו בודקים ש-b הוא dict כי לפעמים יש שם רשימות (shadow blocks)
            opcodes = [b.get('opcode') for b in blocks.values() if isinstance(b, dict)]

            sprite_info = {
                "name": target.get('name'),
                "role": "Stage" if target.get('isStage') else "Sprite",
                "block_count": len([b for b in blocks.values() if isinstance(b, dict)]),
                "logic_summary": list(set(opcodes))[:15],  # 15 דוגמאות ללוגיקה ייחודית
                "variables": list(target.get('variables', {}).keys()),
                "broadcast_messages": list(target.get('broadcasts', {}).values())
            }
            summary["sprites_details"].append(sprite_info)

        return summary

    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}
