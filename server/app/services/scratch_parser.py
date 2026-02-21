import requests
import re
import json


def download_and_parse_scratch(url: str):
    """
    מורידה את קובץ ה-project.json של פרויקט Scratch ומחזירה סיכום של המבנה והבלוקים.
    """
    # 1. חילוץ ה-Project ID מה-URL
    project_id_match = re.search(r'projects/(\d+)', url)
    if not project_id_match:
        return "Error: Invalid Scratch URL"

    project_id = project_id_match.group(1)

    # 2. הכתובת להורדת ה-JSON של הבלוקים (Assets API)
    # שימי לב: זו כתובת שונה מה-API של המטא-דאטה
    assets_url = f"https://projects.scratch.mit.edu/{project_id}"

    try:
        response = requests.get(assets_url, timeout=10)
        if response.status_code != 200:
            return f"Error: Could not retrieve project JSON (Status: {response.status_code})"

        project_data = response.json()

        # 3. ניתוח וסיכום הנתונים עבור ה-AI
        summary = {
            "total_sprites": len(project_data.get('targets', [])),
            "sprites_details": []
        }

        for target in project_data.get('targets', []):
            blocks = target.get('blocks', {})
            # ספירת סוגי בלוקים מעניינים (לולאות, משתנים, מסרים)
            opcodes = [b.get('opcode') for b in blocks.values() if isinstance(b, dict)]

            sprite_info = {
                "name": target.get('name'),
                "block_count": len(blocks),
                "unique_logic": list(set(opcodes))[:15],  # לוקחים רק דוגמה מהלוגיקה
                "variables": list(target.get('variables', {}).keys()),
                "broadcast_messages": list(target.get('broadcasts', {}).values()) if 'broadcasts' in target else []
            }
            summary["sprites_details"].append(sprite_info)

        return json.dumps(summary, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Error during parsing: {str(e)}"